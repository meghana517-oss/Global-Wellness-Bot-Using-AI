from fastapi import FastAPI, Depends, HTTPException, status, Header, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from difflib import get_close_matches, SequenceMatcher
import random
import re 
import os

# -----------------------
# SQLAlchemy setup
# -----------------------

DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'wellness.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -----------------------
# Database Models
# -----------------------
class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    language = Column(String, default="English")
    hashed_password = Column(String, nullable=False)

class Dialogue(Base):
    __tablename__ = "dialogues"
    intent = Column(String, primary_key=True)
    response = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)

class Symptom(Base):
    __tablename__ = "symptoms"
    symptom_name = Column(String, primary_key=True)
    description = Column(String, nullable=False)

class Medication(Base):
    __tablename__ = "medications"
    condition = Column(String, primary_key=True)
    medicine_name = Column(String, nullable=False)

class FirstAid(Base):
    __tablename__ = "first_aid"
    issue = Column(String, primary_key=True)
    steps = Column(String, nullable=False)

class WellnessTip(Base):
    __tablename__ = "wellness_tips"
    id = Column(Integer, primary_key=True)
    tip_text = Column(Text, nullable=False)
    category = Column(String, nullable=False)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    user_text = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    intent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# -----------------------
# Security helpers
# -----------------------
SECRET_KEY = "replace_this_with_a_strong_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -----------------------
# FastAPI App & Middleware
# -----------------------
app = FastAPI(
    title="Wellness Hub API",
    description="Multilingual wellness assistant with secure authentication",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# -----------------------
# Pydantic Schemas
# -----------------------
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    age: int
    language: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class ProfileResponse(BaseModel):
    email: str
    full_name: str
    age: int
    language: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    language: Optional[str] = None
    password: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str
    new_password: str

class RespondRequest(BaseModel):
    text: str
    intent: Optional[List[str]] = []
    confidence_scores: Optional[Dict[str, float]] = {}
    last_tip: Optional[str] = None

class RespondResponse(BaseModel):
    response: str
    intent: List[str]
    confidence_scores: Dict[str, float]

# -----------------------
# Dependencies
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization.startswith("Bearer "):
        raise credentials_exception
    token = authorization.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# -----------------------
# Auth & Profile Routes
# -----------------------
@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if get_user(db, request.email):
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_pw = get_password_hash(request.password)
    user = User(
        email=request.email,
        full_name=request.full_name,
        age=request.age,
        language=request.language,
        hashed_password=hashed_pw,
    )
    db.add(user)
    db.commit()
    return {"msg": "Registration successful"}

@app.post("/token", response_model=TokenResponse)
def token(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile", response_model=ProfileResponse)
def read_profile(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "age": current_user.age,
        "language": current_user.language,
    }

@app.put("/profile")
def update_profile(request: UpdateProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = get_user(db, current_user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.full_name is not None:
        user.full_name = request.full_name
    if request.age is not None:
        user.age = request.age
    if request.language is not None:
        user.language = request.language
    if request.password:
        user.hashed_password = get_password_hash(request.password)

    db.commit()
    return {"msg": "Profile updated successfully"}

@app.put("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return {"msg": "Password reset successful"}

# -----------------------
# DialogueManager Integration
# -----------------------
from backend.knowledge_base import query_db, LANGUAGE_MAP
from backend.dialogue_manager import DialogueManager
dialogue_manager = DialogueManager()

respond_router = APIRouter()

@respond_router.post("/respond", response_model=RespondResponse)
def respond(request: RespondRequest, db: Session = Depends(get_db)):
    dialogue_manager = DialogueManager()
    try:
        result = dialogue_manager.generate_response(request.text)

        message = Message(
            email="anonymous",
            user_text=request.text,
            bot_response=result["response"],
            intent=result["intent"],
            timestamp=datetime.utcnow()
        )

        db.add(message)
        db.commit()

        return RespondResponse(
            response=result["response"],
            intent=[result["intent"]],
            confidence_scores={result["intent"]: 1.0}
        )

    except Exception as e:
        db.rollback()
        return RespondResponse(
            response=f"⚠️ Internal error: {str(e)}",
            intent=["error"],
            confidence_scores={"error": 0.0}
        )

    finally:
        db.close()
        dialogue_manager.close()

app.include_router(respond_router)
