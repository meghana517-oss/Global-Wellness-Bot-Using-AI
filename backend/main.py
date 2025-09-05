from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# -----------------------
# CONFIG
# -----------------------
SECRET_KEY = "replace_this_with_a_strong_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
DATABASE_URL = "sqlite:///./wellness.db"

# -----------------------
# SQLAlchemy setup
# -----------------------
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    language = Column(String, default="English")
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# -----------------------
# Security helpers
# -----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
# Pydantic Schemas
# -----------------------
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    age: int
    language: str
    password: str

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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
# -----------------------
# Dependency: DB session
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

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
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
# FastAPI App & Middleware
# -----------------------
app = FastAPI(
    title="Wellness Hub API",
    description="Multilingual wellness assistant with secure authentication",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
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
# Dev Helpers (Optional)
# -----------------------
@app.get("/debug/users", response_model=List[ProfileResponse])
def debug_users(db: Session = Depends(get_db)):
    rows = db.query(User).all()
    return [{"email": r.email, "full_name": r.full_name, "age": r.age, "language": r.language} for r in rows]

@app.get("/debug/token")
def debug_token(request: Request, token: str = Depends(oauth2_scheme)):
    return {
        "headers": dict(request.headers),
        "token": token
    }
