
from fastapi import FastAPI, Depends, HTTPException, status, Header, Request, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, func, desc, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import os, json, re, unicodedata, io, csv
from difflib import get_close_matches,SequenceMatcher
from jose import JWTError, jwt
from collections import Counter
from passlib.context import CryptContext

# --- Password hashing setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold

def deduplicate_conditions(conditions: list[str], threshold: float = 0.8) -> list[str]:
    unique = []
    for cond in conditions:
        if not any(is_similar(cond, existing, threshold) for existing in unique):
            unique.append(cond)
    return unique


# -----------------------
# Alias Map Loader
# -----------------------
def load_condition_aliases() -> dict:
    alias_path = os.path.join("data_structured", "condition_aliases.json")
    if not os.path.exists(alias_path):
        return {}
    with open(alias_path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    full_name = Column(String)
    age = Column(Integer)
    language = Column(String, default="English")
    hashed_password = Column(String)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    user_text = Column(Text)
    bot_response = Column(Text)
    intent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String, default="milestone2")  

class ConditionInfo(Base):
    __tablename__ = "conditions"
    condition_en = Column(String, primary_key=True)
    condition_hi = Column(String)
    description_en = Column(Text)
    description_hi = Column(Text)
    symptom_en = Column(Text)
    symptom_hi = Column(Text)
    first_aid_en = Column(Text)
    first_aid_hi = Column(Text)
    prevention_en = Column(Text)
    prevention_hi = Column(Text)
    disclaimer_en = Column(Text)
    disclaimer_hi = Column(Text)
    intent_category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class BackupCondition(Base):
    __tablename__ = "backup_conditions"
    condition_en = Column(String, primary_key=True)
    condition_hi = Column(String)
    description_en = Column(Text)
    description_hi = Column(Text)
    symptom_en = Column(Text)
    symptom_hi = Column(Text)
    first_aid_en = Column(Text)
    first_aid_hi = Column(Text)
    prevention_en = Column(Text)
    prevention_hi = Column(Text)
    disclaimer_en = Column(Text)
    disclaimer_hi = Column(Text)
    intent_category = Column(String)
  
class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True)
    query_text = Column(Text)
    bot_response = Column(Text)  # Added for analytics
    timestamp = Column(DateTime, default=datetime.utcnow)
    matched_condition = Column(String, nullable=True)
    intent = Column(String)
    entities = Column(Text)
    language = Column(String)
    email = Column(String, nullable=True)  

class ChatLog(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)               
    role = Column(String)                  
    message = Column(Text)                  
    response = Column(Text)                 
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query_lang = Column(String, default="English")
    response_lang = Column(String, default="English")

class FAQ(Base):
    __tablename__ = "faq"
    id = Column(Integer, primary_key=True, index=True)
    question_en = Column(Text)
    question_hi = Column(Text)
    answer_en = Column(Text)
    answer_hi = Column(Text)
    tags = Column(String)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    query_text = Column(Text)
    response_text = Column(Text)
    thumbs = Column(String)  
    comment = Column(Text)
    sentiment = Column(String)  
    timestamp = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Store hashed password

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Integer, default=0)  # 0 = unused, 1 = used

class KBEntry(Base):
    __tablename__ = "kb_entries"

    id = Column(Integer, primary_key=True, index=True)
    condition_en = Column(String, unique=True, nullable=False)
    intent_category = Column(String, nullable=False)
    description_en = Column(String, nullable=True)
    symptom_en = Column(String, nullable=True)
    first_aid_en = Column(String, nullable=True)
    prevention_en = Column(String, nullable=True)
    disclaimer_en = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)

# -----------------------
# Security helpers
# -----------------------
SECRET_KEY = os.environ.get("WELLBOT_SECRET_KEY", "replace_this_with_a_strong_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- JWT Token Verification ---
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_admin(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

# -----------------------
# FastAPI App & Middleware
# -----------------------
app = FastAPI(title="Wellness Hub API", description="Multilingual wellness assistant", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

security_scheme = HTTPBearer()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title, version=app.version,
        description=app.description, routes=app.routes
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer"}
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# -----------------------
# Shared Dependencies
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
    if not user:
        return False
    # First try normal bcrypt verification
    try:
        if verify_password(password, user.hashed_password):
            return user
    except Exception:
        # If the stored hash is malformed we will attempt legacy fallback below
        pass
    if not (isinstance(user.hashed_password, str) and user.hashed_password.startswith("$2")):
        # Treat stored value as plaintext
        if password == user.hashed_password:
            # Migrate to bcrypt
            try:
                user.hashed_password = get_password_hash(password)
                db.add(user)
                db.commit()
                db.refresh(user)
                return user
            except Exception:
                db.rollback()
                return user 
    return False

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=401, detail="Invalid credentials")
    if not authorization.startswith("Bearer "):
        raise credentials_exception
    token = authorization.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email)
    if user is None:
        raise credentials_exception
    return user

# -----------------------
# Pydantic Schemas
# -----------------------
# -----------------------
# Auth & Profile Schemas
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

class QueryRequest(BaseModel):
    text: str

class ChatLogCreate(BaseModel):
    user_id: str
    role: str  # "user" or "admin"
    message: str
    response: str
    feedback: Optional[str] = None

class ChatHistoryEntry(BaseModel):
    email: str
    query: str
    response: str
    comment: str = ""
    timestamp: Optional[str] = None
    query_lang: Optional[str] = "English"
    response_lang: Optional[str] = "English"

class FeedbackSchema(BaseModel):
    query_text: str
    response_text: str
    thumbs: str  
    comment: Optional[str] = None
    sentiment: Optional[str] = None  
    timestamp: Optional[datetime] = None

    class Config:
        orm_mode = True

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# -----------------------
# Knowledge Base Schema
# -----------------------
class ConditionInfoSchema(BaseModel):
    condition_en: str
    condition_hi: Optional[str]
    description_en: Optional[str]
    description_hi: Optional[str]
    symptom_en: Optional[str]
    symptom_hi: Optional[str]
    first_aid_en: Optional[str]
    first_aid_hi: Optional[str]
    prevention_en: Optional[str]
    prevention_hi: Optional[str]
    disclaimer_en: Optional[str]
    disclaimer_hi: Optional[str]
    intent_category: Optional[str]

    class Config:
        orm_mode = True
        
# -----------------------
# Auth & Profile Endpoints
# -----------------------

# --- Admin Debug Endpoint: List all users ---
@app.get("/admin/list-users")
def admin_list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{
        "email": u.email,
        "full_name": u.full_name,
        "age": u.age,
        "language": u.language
    } for u in users]
@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Normalize email (trim & lowercase) to avoid duplicate case variants or trailing spaces
    normalized_email = request.email.strip().lower()
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email required")
    if get_user(db, normalized_email):
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_pw = get_password_hash(request.password)
    user = User(
        email=normalized_email,
        full_name=request.full_name.strip() if request.full_name else None,
        age=request.age,
        language=request.language,
        hashed_password=hashed_pw,
    )
    db.add(user)
    db.commit()
    return {"msg": "Registration successful"}

@app.post("/token", response_model=TokenResponse)
def token(request: LoginRequest, db: Session = Depends(get_db)):
    normalized_email = request.email.strip().lower()
    user = authenticate_user(db, normalized_email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user-exists")
def user_exists(email: str, db: Session = Depends(get_db)):
    """Lightweight endpoint for frontend to differentiate 'unregistered' vs 'wrong password'."""
    normalized_email = email.strip().lower()
    return {"email": normalized_email, "exists": bool(get_user(db, normalized_email))}

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

@app.post("/auth/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Secure password change: requires current password verification."""
    user = get_user(db, current_user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password too short")
    if verify_password(payload.new_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="New password must differ from current password")
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "password_changed"}

def _generate_reset_token(length: int = 48) -> str:
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@app.post("/auth/request-password-reset")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    email_norm = payload.email.strip().lower()
    user = get_user(db, email_norm)
    if not user:
        return {"status": "ok"}
    db.query(PasswordResetToken).filter(PasswordResetToken.email == email_norm, PasswordResetToken.used == 0).delete()
    token = _generate_reset_token()
    expires = datetime.utcnow() + timedelta(minutes=30)
    pr = PasswordResetToken(email=email_norm, token=token, expires_at=expires)
    db.add(pr)
    db.commit()
    # Only return token in API response, do not send email
    return {"status": "issued", "token": token, "expires_at": expires.isoformat()}

@app.post("/auth/reset-password")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    pr = db.query(PasswordResetToken).filter(PasswordResetToken.token == payload.token).first()
    if not pr:
        raise HTTPException(status_code=400, detail="Invalid token")
    if pr.used:
        raise HTTPException(status_code=400, detail="Token already used")
    if pr.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password too short")
    user = get_user(db, pr.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(payload.new_password)
    pr.used = 1
    db.commit()
    return {"status": "password_reset"}

# -----------------------
# Pydantic Schemas
# -----------------------
class RespondRequest(BaseModel):
    text: str
    intent: Optional[List[str]] = []
    confidence_scores: Optional[Dict[str, float]] = {}

class RespondResponse(BaseModel):
    response: str
    intent: List[str]
    confidence_scores: Dict[str, float]

# -----------------------
# DialogueManager Integration
# -----------------------
from backend.dialogue_manager import DialogueManager
dialogue_manager = DialogueManager()

@app.post("/respond", response_model=RespondResponse)
def respond(request: RespondRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = dialogue_manager.generate_response(request.text)

        # Store chat history in ChatLog
        chat_entry = ChatLog(
            user_id=current_user.email,
            role="user",
            message=request.text,
            response=result["response"],
            feedback=None,
            timestamp=datetime.utcnow()
        )
        db.add(chat_entry)

        # Log query
        log = QueryLog(
            query_text=request.text,
            bot_response=result["response"],
            matched_condition=result.get("matched_condition"),
            intent=result.get("intent"),
            entities=result.get("entities", ""),
            language=result.get("language", "English"),
            email=current_user.email
        )
        db.add(log)

        # Log message
        message = Message(
            email=current_user.email,
            user_text=request.text,
            bot_response=result["response"],
            intent=result["intent"],
            timestamp=datetime.utcnow()
        )
        db.add(message)
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

@app.middleware("http")
async def jwt_middleware(request: Request, call_next):
    """Auth strategy:
    - Public: GET /kb*, /kb/search, /kb/categories, /kb/respond, /analytics/top-intents
    - Protected: any non-GET under /kb (create/update/delete), all /analytics except top-intents, all /chat
    """
    path = request.url.path
    method = request.method.upper()

    # Always public explicit endpoints
    if path in ("/kb/respond", "/kb/search", "/kb/categories", "/analytics/top-intents"):
        return await call_next(request)

    # Allow all GETs under /kb without auth
    if path.startswith("/kb") and method == "GET":
        return await call_next(request)

    # Protect mutating /kb operations & broader secure prefixes
    protected_prefixes = ["/kb", "/analytics", "/chat"]
    if any(path.startswith(p) for p in protected_prefixes):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})
        token = auth.split(" ")[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Token verification failed"})
    return await call_next(request)


# ------------------------------------------
# Fuzzy Matching and Respond Route
# -------------------------------------------
# Normalize text for fuzzy matching
def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", re.sub(r"[^\w\s\u0900-\u097F]", "", text.strip().lower()))

# Fuzzy match against condition names
_ALIAS_CACHE: dict | None = None
_KB_LIST_CACHE: list[dict] | None = None
_KB_LIST_CACHE_TS: float | None = None
_KB_CATEGORIES_CACHE: list[dict] | None = None
_KB_CATEGORIES_TS: float | None = None
_CACHE_TTL_SECONDS = 60.0

EXTRA_ALIAS_OVERRIDES: dict[str, str | None] = {
    "Persistent Headache": "Headache",
    "Child Fever": "Fever",
    "Feeling Drained": "Fatigue",
    "Overwhelmed Emotion": "Emotional Wellness",
    "Elderly Cough Care": "Cough",
    
}

def load_alias_cache():
    global _ALIAS_CACHE
    if _ALIAS_CACHE is None:
        try:
            _ALIAS_CACHE = load_condition_aliases()
        except Exception:
            _ALIAS_CACHE = {}
    return _ALIAS_CACHE

def resolve_via_alias(raw: str) -> str | None:
    aliases = load_alias_cache()
    q = normalize_text(raw)
    for pseudo, canonical in EXTRA_ALIAS_OVERRIDES.items():
        if normalize_text(pseudo) == q:
            return canonical
    for canonical, lang_map in aliases.items():
        for arr in lang_map.values():
            for term in arr:
                if normalize_text(term) == q:
                    return canonical
    return None

def fuzzy_lookup(condition: str, lang: str, db: Session) -> str:
    resolved = resolve_via_alias(condition)
    if resolved:
        return resolved
    normalized_condition = normalize_text(condition)
    all_conditions = db.query(ConditionInfo).all()
    candidates = [
        normalize_text(getattr(entry, f"condition_{lang}"))
        for entry in all_conditions
        if getattr(entry, f"condition_{lang}")
    ]
    matches = get_close_matches(normalized_condition, candidates, n=1, cutoff=0.7)
    if not matches:
        return None
    for entry in all_conditions:
        if normalize_text(getattr(entry, f"condition_{lang}")) == matches[0]:
            return entry.condition_en
    return None

# Suggest similar conditions
def get_condition_suggestions(query: str, db: Session) -> list:
    all_conditions = db.query(ConditionInfo).all()
    candidates = [entry.condition_en for entry in all_conditions if entry.condition_en]
    matches = get_close_matches(query.lower(), [c.lower() for c in candidates], n=3, cutoff=0.6)
    suggestions = [c for c in candidates if c.lower() in matches]
    return suggestions

# -------------------------------------------------------------
# Core KB processing helper (reusable by API & internal callers)
# -------------------------------------------------------------
def kb_process_query(raw_text: str, db: Session, user_email: str | None = None) -> dict:
    """Process a KB query and return structured response.

    Returns one of two shapes:
    1. Fallback:
       {"fallback": True, "message": {"en": str, "hi": str}, "suggestions": [...]} (suggestions optional)
    2. Success:
       {
         "conditions": [{"en": en, "hi": hi}],
         "description": {"en": str, "hi": str},
         "possible_symptom": {"en": str, "hi": str},
         "first_aid_tips": {"en": str, "hi": str},
         "prevention_tips": {"en": str, "hi": str},
         "disclaimer": {"en": str, "hi": str},
         "language": "en" | "hi"
       }
    """
    text = (raw_text or "").strip()
    if not text:
        return {
            "fallback": True,
            "message": {
                "en": "Please enter a wellness question or symptom.",
                "hi": "कृपया कोई स्वास्थ्य प्रश्न या लक्षण दर्ज करें।"
            }
        }
    lang = "hi" if any("\u0900" <= c <= "\u097F" for c in text) else "en"
    aliases = load_condition_aliases()
    matched_conditions: set[str] = set()
    normalized_text = normalize_text(text)

    # Basic conversational intents (quick responses)
    basic_intents = {
        "hello": {
            "en": "Hello! How can I support your wellness today?",
            "hi": "नमस्ते! मैं आपकी सेहत से जुड़ी किसी भी बात में मदद कर सकता हूँ।"
        },
        "नमस्ते": {
            "en": "Hello! How can I support your wellness today?",
            "hi": "नमस्ते! मैं आपकी सेहत से जुड़ी किसी भी बात में मदद कर सकता हूँ।"
        },
        "thanks": {
            "en": "You're welcome! Let me know if you need anything else.",
            "hi": "आपका स्वागत है! अगर कुछ और पूछना चाहें तो बताइए।"
        },
        "धन्यवाद": {
            "en": "You're welcome! Let me know if you need anything else.",
            "hi": "आपका स्वागत है! अगर कुछ और पूछना चाहें तो बताइए।"
        },
        "goodbye": {
            "en": "Take care! Wishing you wellness and peace.",
            "hi": "ख़्याल रखिए! सेहत और सुकून की शुभकामनाएँ।"
        },
        "अलविदा": {
            "en": "Take care! Wishing you wellness and peace.",
            "hi": "ख़्याल रखिए! सेहत और सुकून की शुभकामनाएँ।"
        }
    }
    if normalized_text in basic_intents:
        return {"fallback": True, "message": basic_intents[normalized_text]}

    # Token splitting for multi-topic queries (very lightweight)
    split_keywords = ["और", "या", "के लिए", "कैसे", "क्या"]
    tokens = [normalized_text]
    for keyword in split_keywords:
        tokens = [subtoken.strip() for token in tokens for subtoken in token.split(keyword)]

    for token in tokens:
        for canonical, lang_map in aliases.items():
            for alias in lang_map.get(lang, []):
                if normalize_text(alias) in token:
                    matched_conditions.add(canonical)

    # Fallback fuzzy if no alias match
    if not matched_conditions:
        fallback = fuzzy_lookup(normalized_text, lang, db)
        if fallback:
            matched_conditions.add(fallback)

    # Still no match => suggestions
    if not matched_conditions:
        suggestions = get_condition_suggestions(normalized_text, db)
        # Log unknown query
        try:
            fallback_en = "I couldn't find wellness information for that. Try asking about a symptom, condition, or first aid topic."
            fallback_hi = "मुझे उस विषय पर सेहत संबंधी जानकारी नहीं मिली। कृपया किसी लक्षण, शिकायत या प्राथमिक उपचार के बारे में पूछें।"
            qlog_unknown = QueryLog(
                query_text=text,
                bot_response=(fallback_en if lang == "en" else fallback_hi)[:500],
                matched_condition=None,
                intent="unknown",
                entities="",
                language="Hindi" if lang == "hi" else "English",
                email=user_email
            )
            db.add(qlog_unknown)
            db.commit()
        except Exception:
            db.rollback()
        return {
            "fallback": True,
            "message": {
                "en": "I couldn't find wellness information for that. Try asking about a symptom, condition, or first aid topic.",
                "hi": "मुझे उस विषय पर सेहत संबंधी जानकारी नहीं मिली। कृपया किसी लक्षण, शिकायत या प्राथमिक उपचार के बारे में पूछें।"
            },
            "suggestions": suggestions,
            "language": lang
        }

    # Aggregate response across matched conditions
    response: dict = {
        "conditions": [],
        "description": {"en": "", "hi": ""},
        "possible_symptom": {"en": "", "hi": ""},
        "first_aid_tips": {"en": "", "hi": ""},
        "prevention_tips": {"en": "", "hi": ""},
        "disclaimer": {"en": "", "hi": ""},
        "language": lang
    }
    for condition in matched_conditions:
        entry = db.query(ConditionInfo).filter(ConditionInfo.condition_en == condition).first()
        if entry:
            response["conditions"].append({"en": entry.condition_en, "hi": entry.condition_hi})
            response["description"]["en"] += (entry.description_en or "") + "\n"
            response["description"]["hi"] += (entry.description_hi or "") + "\n"
            response["possible_symptom"]["en"] += (entry.symptom_en or "") + "\n"
            response["possible_symptom"]["hi"] += (entry.symptom_hi or "") + "\n"
            response["first_aid_tips"]["en"] += (entry.first_aid_en or "") + "\n"
            response["first_aid_tips"]["hi"] += (entry.first_aid_hi or "") + "\n"
            response["prevention_tips"]["en"] += (entry.prevention_en or "") + "\n"
            response["prevention_tips"]["hi"] += (entry.prevention_hi or "") + "\n"
            response["disclaimer"]["en"] = entry.disclaimer_en or response["disclaimer"]["en"]
            response["disclaimer"]["hi"] = entry.disclaimer_hi or response["disclaimer"]["hi"]

    # Log successful lookup
    try:
        intent_category = None
        if response["conditions"]:
            first_condition = response["conditions"][0]["en"]
            entry = db.query(ConditionInfo).filter(ConditionInfo.condition_en == first_condition).first()
            if entry:
                intent_category = entry.intent_category
        entities = ", ".join([c["en"] for c in response["conditions"]]) if response["conditions"] else ""
        qlog = QueryLog(
            query_text=text,
            bot_response=(response["description"]["en"] or response["description"]["hi"]).strip()[:500],
            matched_condition=entities if entities else None,
            intent=intent_category if intent_category else "kb_lookup",
            entities=entities,
            language="Hindi" if lang == "hi" else "English",
            email=user_email
        )
        db.add(qlog)
        db.commit()
    except Exception:
        db.rollback()
    return response

# GET: Suggestions for search bar
@app.get("/kb/search")
def search_kb(q: str):
    db: Session = SessionLocal()
    suggestions = get_condition_suggestions(q, db)
    db.close()
    return {"suggestions": suggestions}

"""Knowledge Base respond endpoint (public; optional auth for email capture)."""
# POST: Respond to KB query
@app.post("/kb/respond")
def respond_kb(req: QueryRequest, authorization: str = Header(None)):
    db: Session = SessionLocal()
    user_email = None
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_email = payload.get("sub")
            except Exception as e:
                print(f"[KB_RESPOND] JWT decode failed: {e}")
    try:
        return kb_process_query(req.text, db, user_email=user_email)
    finally:
        db.close()

# GET all conditions
@app.get("/kb", response_model=List[ConditionInfoSchema])
def get_all_conditions(db: Session = Depends(get_db)):
    # Simple time-based cache (invalidated on writes not tracked here; TTL protects staleness)
    import time
    global _KB_LIST_CACHE, _KB_LIST_CACHE_TS
    now = time.time()
    if _KB_LIST_CACHE is not None and _KB_LIST_CACHE_TS and (now - _KB_LIST_CACHE_TS) < _CACHE_TTL_SECONDS:
        return _KB_LIST_CACHE
    rows = db.query(ConditionInfo).all()
    _KB_LIST_CACHE = rows
    _KB_LIST_CACHE_TS = now
    return rows

# Lightweight list of condition names (English & Hindi) for frontend fuzzy/correction
@app.get("/kb/conditions")
def get_condition_names(db: Session = Depends(get_db)):
    rows = db.query(ConditionInfo.condition_en, ConditionInfo.condition_hi).all()
    names = []
    for en, hi in rows:
        if en: names.append(en)
        if hi: names.append(hi)
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for n in names:
        if n not in seen:
            seen.add(n)
            deduped.append(n)
    return deduped

# --- Valid categories for KB classification ---
VALID_CATEGORIES = {
    "Symptoms & Diagnosis",
    "Lifestyle & Prevention",
    "First Aid & Emergency",
    "Wellness & Mental Health",
    "Diseases & Conditions",
    "Special Cases & Care",
    "Others"
}

@app.get("/kb/categories")
def get_category_distribution(db: Session = Depends(get_db)):
    import time
    global _KB_CATEGORIES_CACHE, _KB_CATEGORIES_TS
    now = time.time()
    if _KB_CATEGORIES_CACHE is not None and _KB_CATEGORIES_TS and (now - _KB_CATEGORIES_TS) < _CACHE_TTL_SECONDS:
        return _KB_CATEGORIES_CACHE
    raw = db.query(ConditionInfo.intent_category, func.count()) \
        .group_by(ConditionInfo.intent_category) \
        .all()
    result = []
    for category, count in raw:
        label = category if category in VALID_CATEGORIES else "Uncategorized"
        result.append({"category": label, "count": count})
    _KB_CATEGORIES_CACHE = result
    _KB_CATEGORIES_TS = now
    return result

@app.get("/analytics/top-intents")
def top_intents(db: Session = Depends(get_db)):
    raw = db.query(ConditionInfo.intent_category, func.count())\
        .group_by(ConditionInfo.intent_category)\
        .all()

    result = []
    for intent, count in raw:
        if intent in VALID_CATEGORIES:
            label = intent
        else:
            label = "Uncategorized"
        result.append({"intent": label, "count": count})

    return result

# GET single condition
@app.get("/kb/{condition_en}", response_model=ConditionInfoSchema)
def get_condition(condition_en: str, db: Session = Depends(get_db)):
    condition = db.query(ConditionInfo).filter(func.lower(ConditionInfo.condition_en) == condition_en.lower().strip()).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    return condition

# POST new condition
@app.post("/kb", response_model=ConditionInfoSchema)
def create_condition(condition: ConditionInfoSchema, db: Session = Depends(get_db)):
    global _KB_LIST_CACHE, _KB_LIST_CACHE_TS, _KB_CATEGORIES_CACHE, _KB_CATEGORIES_TS
    existing = db.query(ConditionInfo).filter_by(condition_en=condition.condition_en).first()
    if existing:
        raise HTTPException(status_code=400, detail="Condition already exists")
    new_entry = ConditionInfo(**condition.dict())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    # Invalidate KB caches
    _KB_LIST_CACHE = None
    _KB_LIST_CACHE_TS = None
    _KB_CATEGORIES_CACHE = None
    _KB_CATEGORIES_TS = None
    return new_entry

# PUT update condition
@app.put("/kb/{condition_en}", response_model=ConditionInfoSchema)
def update_condition(condition_en: str, update: ConditionInfoSchema, db: Session = Depends(get_db)):
    global _KB_LIST_CACHE, _KB_LIST_CACHE_TS, _KB_CATEGORIES_CACHE, _KB_CATEGORIES_TS
    condition = db.query(ConditionInfo).filter_by(condition_en=condition_en).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(condition, key, value)
    db.commit()
    db.refresh(condition)
    # Invalidate KB caches
    _KB_LIST_CACHE = None
    _KB_LIST_CACHE_TS = None
    _KB_CATEGORIES_CACHE = None
    _KB_CATEGORIES_TS = None
    return condition

# DELETE condition
@app.delete("/kb/{condition_en}")
def delete_condition(condition_en: str, db: Session = Depends(get_db)):
    global _KB_LIST_CACHE, _KB_LIST_CACHE_TS, _KB_CATEGORIES_CACHE, _KB_CATEGORIES_TS
    condition = db.query(ConditionInfo).filter_by(condition_en=condition_en).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    db.delete(condition)
    db.commit()
    # Invalidate KB caches
    _KB_LIST_CACHE = None
    _KB_LIST_CACHE_TS = None
    _KB_CATEGORIES_CACHE = None
    _KB_CATEGORIES_TS = None
    return {"message": f"Condition '{condition_en}' deleted successfully"}

@app.get("/analytics/daily")
def get_daily_query_count(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    count = db.query(QueryLog).filter(QueryLog.timestamp >= today).count()
    return {"count": count}

@app.get("/analytics/unmatched")
def get_unmatched_queries(db: Session = Depends(get_db)):
    unmatched = db.query(QueryLog).filter(QueryLog.matched_condition == None).order_by(desc(QueryLog.timestamp)).limit(20).all()
    return [{"query": q.query_text, "timestamp": q.timestamp.isoformat()} for q in unmatched]

# Save feedback
@app.post("/feedback", response_model=FeedbackSchema)
def save_feedback(feedback: FeedbackSchema, db: Session = Depends(get_db)):
    entry = Feedback(**feedback.dict())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# Get feedback stats
@app.get("/feedback/stats")
def feedback_stats(db: Session = Depends(get_db)):
    total = db.query(Feedback).count()
    up = db.query(Feedback).filter_by(thumbs="up").count()
    down = db.query(Feedback).filter_by(thumbs="down").count()
    return {
        "total": total,
        "positive": up,
        "negative": down,
        "positive_percent": round((up / total) * 100, 2) if total else 0,
        "negative_percent": round((down / total) * 100, 2) if total else 0
    }

# Top recurring comments
@app.get("/feedback/top-comments")
def top_comments(db: Session = Depends(get_db)):
    comments = db.query(Feedback.comment).filter(Feedback.comment != "").all()
    counter = Counter([c[0] for c in comments])
    return counter.most_common(3)

# Flag poor responses
@app.get("/feedback/alerts")
def feedback_alerts(db: Session = Depends(get_db)):
    flagged = db.query(Feedback.response_text, func.count().label("count"))\
        .filter_by(thumbs="down")\
        .group_by(Feedback.response_text)\
        .having(func.count() > 3)\
        .all()
    return [{"response": r[0], "downvotes": r[1]} for r in flagged]

@app.get("/analytics/query-trends")
def query_trends(
    days: int = Query(7, ge=1, le=60, description="Number of recent days to include (including today)"),
    db: Session = Depends(get_db)
):
    """Return query counts for the last N days (default 7) including zero-count days.

    Frontend benefit: always yields a contiguous time series for consistent bar/line chart width.
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    # Fetch counts grouped by date within window
    rows = (
        db.query(func.date(QueryLog.timestamp).label("day"), func.count().label("count"))
        .filter(func.date(QueryLog.timestamp) >= start_date)
        .filter(func.date(QueryLog.timestamp) <= end_date)
        .group_by(func.date(QueryLog.timestamp))
        .all()
    )
    counts = {str(r.day): r.count for r in rows}
    series = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        key = str(d)
        series.append({"day": key, "count": counts.get(key, 0)})
    return series

@app.get("/analytics/top-queries")
def get_top_queries(db: Session = Depends(get_db)):
    result = (
        db.query(
            ConditionInfo.condition_en,
            ConditionInfo.intent_category
        )
        .order_by(desc(ConditionInfo.created_at))
        .limit(20)
        .all()
    )

    return [
        {
            "query": r.condition_en,
            "intent": r.intent_category or "Uncategorized",
            "count": 1  # Dummy count for frontend compatibility
        }
        for r in result
    ]

@app.post("/chat/save")
def save_chat(log: ChatLogCreate, db: Session = Depends(get_db)):
    entry = ChatLog(**log.dict())
    db.add(entry)
    db.commit()
    return {"status": "saved"}

@app.post("/kb/backup-original")
def backup_kb(db: Session = Depends(get_db)):
    try:
        originals = db.query(ConditionInfo).all()
        backup_fields = set(c.name for c in BackupCondition.__table__.columns)
        for item in originals:
            clean_data = {k: v for k, v in item.__dict__.items() if k != "_sa_instance_state" and k in backup_fields}
            # Fill missing fields with None
            for field in backup_fields:
                clean_data.setdefault(field, None)
            db.merge(BackupCondition(**clean_data))
        db.commit()
        return {"status": "backup created"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}

@app.post("/kb/restore-original")
def restore_kb(db: Session = Depends(get_db)):
    originals = db.query(BackupCondition).all()
    for item in originals:
        clean_data = {k: v for k, v in item.__dict__.items() if k != "_sa_instance_state"}
        db.merge(ConditionInfo(**clean_data))
    db.commit()
    return {"status": "restored"}

@app.get("/feedback/stats")
def feedback_stats(db: Session = Depends(get_db)):
    total = db.query(Feedback).count()
    up = db.query(Feedback).filter_by(thumbs="up").count()
    down = db.query(Feedback).filter_by(thumbs="down").count()
    return {
        "total": total,
        "positive": up,
        "negative": down,
        "positive_percent": round((up / total) * 100, 2) if total else 0,
        "negative_percent": round((down / total) * 100, 2) if total else 0
    }

@app.post("/admin/login")
def admin_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    uname = (username or "").strip().lower()
    if not uname:
        raise HTTPException(status_code=400, detail="Username required")
    admin = db.query(Admin).filter(Admin.username == uname).first()
    # Auto-provision default admin if table empty
    if not admin:
        existing_count = db.query(Admin).count()
        if existing_count == 0:
            # Create first admin with provided password
            hashed = get_password_hash(password)
            admin = Admin(username=uname, password=hashed)
            db.add(admin)
            db.commit()
            db.refresh(admin)
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    # Password verification with migration for legacy plaintext (if any)
    verified = False
    try:
        verified = verify_password(password, admin.password)
    except Exception:
        verified = False
    if not verified:
        # Plaintext fallback if stored value not a bcrypt hash
        if not (isinstance(admin.password, str) and admin.password.startswith("$2")) and password == admin.password:
            # Migrate to bcrypt
            try:
                admin.password = get_password_hash(password)
                db.add(admin)
                db.commit()
                db.refresh(admin)
                verified = True
            except Exception:
                db.rollback()
                verified = True  # allow this login attempt
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": admin.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/kb")
def get_kb_entries(admin: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(KBEntry).all()

@app.get("/analytics/user-queries")
def get_user_queries(email: str, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).filter(QueryLog.email == email).order_by(desc(QueryLog.timestamp)).limit(50).all()
    return [
        {
            "query": log.query_text,
            "intent": log.intent,
            "matched_condition": log.matched_condition,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]

@app.get("/feedback/all")
def get_all_feedback(db: Session = Depends(get_db)):
    result = db.query(Feedback).order_by(desc(Feedback.timestamp)).limit(100).all()
    return [
        {
            "query_text": f.query_text,
            "response_text": f.response_text,
            "thumbs": f.thumbs,
            "comment": f.comment,
            "sentiment": f.sentiment,
            "timestamp": f.timestamp.isoformat() if f.timestamp else "N/A"
        }
        for f in result
    ]

@app.get("/feedback/comment-summary")
def feedback_comment_summary(db: Session = Depends(get_db)):
    """Aggregate feedback comments (non-empty) with counts of up/down and total."""
    rows = db.query(Feedback.comment, Feedback.thumbs, func.count().label("cnt"))\
        .filter(Feedback.comment != None)\
        .filter(Feedback.comment != "")\
        .group_by(Feedback.comment, Feedback.thumbs)\
        .all()
    agg = {}
    for comment, thumb, cnt in rows:
        meta = agg.setdefault(comment, {"total": 0, "up": 0, "down": 0})
        meta["total"] += cnt
        if thumb == "up":
            meta["up"] += cnt
        elif thumb == "down":
            meta["down"] += cnt
    # Compute score = up - down and ratio
    summary = []
    for comment, stats in agg.items():
        total = stats["total"]
        up = stats["up"]
        down = stats["down"]
        ratio = (up / total) if total else 0
        summary.append({
            "comment": comment,
            "total": total,
            "up": up,
            "down": down,
            "positive_ratio": round(ratio, 3),
            "score": up - down
        })
    # Sort by score then total desc
    summary.sort(key=lambda x: (x["score"], x["total"]), reverse=True)
    return summary

@app.get("/analytics/user-query-table-today")
def get_user_query_table_today(db: Session = Depends(get_db)):
    import logging
    today = datetime.utcnow().date()
    try:
        logs = db.query(QueryLog).filter(func.date(QueryLog.timestamp) == today).all()
        results = []
        for log in logs:
            bot_resp = log.bot_response
            # Fallback for legacy (milestone 2) data: look up matching Message if bot_response absent
            if not bot_resp:
                msg = db.query(Message).filter(
                    Message.email == log.email,
                    Message.user_text == log.query_text,
                    func.date(Message.timestamp) == today
                ).order_by(desc(Message.timestamp)).first()
                if msg:
                    bot_resp = msg.bot_response
            results.append({
                "email": log.email,
                "query_text": log.query_text,
                "bot_response": bot_resp,
                "intent": log.intent,
                "entities": log.entities,
                "timestamp": log.timestamp.isoformat() if log.timestamp else "N/A"
            })
        return results
    except Exception as e:
        logging.error(f"Error in /analytics/user-query-table-today: {e}")
        return []

@app.get("/analytics/user-query-table-today-messages")
def get_user_query_table_today_messages(db: Session = Depends(get_db)):
    """Direct view based purely on Message table (legacy support for milestone 2)."""
    today = datetime.utcnow().date()
    msgs = db.query(Message).filter(func.date(Message.timestamp) == today).order_by(desc(Message.timestamp)).all()
    return [
        {
            "email": m.email,
            "query_text": m.user_text,
            "bot_response": m.bot_response,
            "intent": getattr(m, "intent", None),
            "timestamp": m.timestamp.isoformat() if m.timestamp else "N/A"
        }
        for m in msgs
    ]

# --- Analytics: Total Users & Queries Handled ---
@app.get("/analytics/total-users")
def get_total_users(db: Session = Depends(get_db)):
    count = db.query(User).count()
    return {"total_users": count}

@app.get("/analytics/total-queries")
def get_total_queries(db: Session = Depends(get_db)):
    count = db.query(QueryLog).count()
    return {"total_queries": count}

@app.get("/analytics/health-topics")
def get_health_topics(db: Session = Depends(get_db)):
    """Return count of distinct health topics / conditions in knowledge base."""
    try:
        count = db.query(func.count(ConditionInfo.condition_en)).scalar() or 0
        return {"health_topics": count}
    except Exception:
        return {"health_topics": 0}

# GET unknown queries for frontend (for compatibility)
@app.get("/analytics/unknown-queries-db")
def get_unknown_queries_db(db: Session = Depends(get_db)):
    # Unknown = unmatched queries (no matched_condition)
    unmatched = db.query(QueryLog).filter(QueryLog.matched_condition == None).order_by(desc(QueryLog.timestamp)).limit(100).all()
    return [
        {
            "query_text": q.query_text,
            "timestamp": q.timestamp.isoformat() if q.timestamp else "N/A",
            "email": q.email,
            "intent": q.intent,
            "bot_response": q.bot_response
        }
        for q in unmatched
    ]

# --- Additional Query Monitoring Endpoints ---
@app.get("/analytics/recent-queries")
def recent_queries(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).order_by(desc(QueryLog.timestamp)).limit(min(limit, 200)).all()
    return [
        {
            "timestamp": q.timestamp.isoformat() if q.timestamp else None,
            "email": q.email,
            "query_text": q.query_text,
            "intent": q.intent,
            "entities": q.entities,
            "matched_condition": q.matched_condition
        } for q in logs
    ]

@app.get("/analytics/intent-distribution")
def intent_distribution(db: Session = Depends(get_db)):
    rows = db.query(QueryLog.intent, func.count().label("count")).group_by(QueryLog.intent).order_by(desc("count")).all()
    return [{"intent": r.intent or "unknown", "count": r.count} for r in rows]

@app.get("/analytics/hourly-activity")
def hourly_activity(db: Session = Depends(get_db)):
    # Group by hour (UTC) for today
    today = datetime.utcnow().date()
    rows = db.query(
        func.strftime('%H', QueryLog.timestamp).label('hour'),
        func.count().label('count')
    ).filter(func.date(QueryLog.timestamp) == today).group_by('hour').order_by('hour').all()
    # Ensure all 24 hours represented
    counts = {r.hour: r.count for r in rows}
    return [{"hour": f"{h:02d}", "count": counts.get(f"{h:02d}", 0)} for h in range(24)]

@app.get("/analytics/top-unknown")
def top_unknown(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(
        QueryLog.query_text,
        func.count().label('count')
    ).filter(QueryLog.matched_condition == None).group_by(QueryLog.query_text).order_by(desc('count')).limit(limit).all()
    return [{"query_text": r.query_text, "count": r.count} for r in rows]

# -----------------------
# Chat History Fetch Endpoint
# -----------------------
@app.get("/chat/history")
def get_chat_history(email: str, db: Session = Depends(get_db)):
    logs = db.query(ChatLog).filter(ChatLog.user_id == email).order_by(desc(ChatLog.timestamp)).limit(100).all()
    return [
        {
            "email": log.user_id,
            "query": log.message,
            "response": log.response,
            "comment": log.feedback,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "N/A"
        }
        for log in logs
    ]
@app.get("/chat/history/me")
def get_my_chat_history(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Email claim missing in token")
    logs = db.query(ChatLog).filter(ChatLog.user_id == email.lower()).order_by(desc(ChatLog.timestamp)).limit(100).all()
    return [
        {
            "email": log.user_id,
            "query": log.message,
            "response": log.response,
            "comment": log.feedback,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "N/A",
            "query_lang": log.query_lang,
            "response_lang": log.response_lang

        }
        for log in logs
    ]
# -----------------------
# Chat History Save Endpoint
# -----------------------
@app.get("/admin/chat-history")
def admin_chat_history(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    logs = db.query(ChatLog).order_by(desc(ChatLog.timestamp)).limit(200).all()
    return [
        {
            "email": log.user_id,
            "query": log.message,
            "response": log.response,
            "feedback": log.feedback,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "N/A"
        }
        for log in logs
    ]
from fastapi import Body

@app.post("/chat/save-history")
def save_chat_history(entry: ChatHistoryEntry = Body(...), db: Session = Depends(get_db)):
    # Normalize email
    email_norm = entry.email.strip().lower() if entry.email else ""
    if not email_norm or not entry.query or not entry.response:
        raise HTTPException(status_code=400, detail="Missing required fields")
    # Try to find existing record (same user_id, message, timestamp within ±2 seconds)
    ts = datetime.fromisoformat(entry.timestamp) if entry.timestamp else datetime.utcnow()
    window_start = ts - timedelta(seconds=2)
    window_end = ts + timedelta(seconds=2)
    existing = db.query(ChatLog).filter(
        ChatLog.user_id == email_norm,
        ChatLog.message == entry.query,
        ChatLog.timestamp >= window_start,
        ChatLog.timestamp <= window_end
    ).order_by(ChatLog.timestamp.desc()).first()
    if existing:
        # Update feedback/comment if provided or update response (latest wins)
        if entry.comment:
            existing.feedback = entry.comment
        existing.response = entry.response
        existing.query_lang = entry.query_lang or "English"
        existing.response_lang = entry.response_lang or "English"
        db.add(existing)
        db.commit()
        return {"status": "updated"}
    # Insert new
    chat = ChatLog(
        user_id=email_norm,
        role="user",
        message=entry.query,
        response=entry.response,
        feedback=entry.comment,
        timestamp=ts,
         query_lang=entry.query_lang or "English",
        response_lang=entry.response_lang or "English",
    )
    db.add(chat)
    db.commit()
    return {"status": "inserted"}

# -----------------------
# Maintenance: Normalize & migrate legacy messages into chat_logs
# -----------------------
@app.post("/admin/maintenance/fix-chat")
def maintenance_fix_chat(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    # 1. Normalize user_id casing in chat_logs
    updated = db.execute(text("UPDATE chat_logs SET user_id = lower(user_id) WHERE user_id != lower(user_id)"))
    # 2. Count before migration
    pre_count = db.execute(text("SELECT COUNT(*) FROM chat_logs")).scalar() or 0
    migrate_sql = """
        INSERT INTO chat_logs (user_id, role, message, response, feedback, timestamp)
        SELECT m.email, 'user', m.user_text, m.bot_response, NULL, m.timestamp
        FROM messages m
        WHERE NOT EXISTS (
            SELECT 1 FROM chat_logs c
            WHERE c.user_id = lower(m.email)
              AND c.message = m.user_text
              AND ABS(strftime('%s', c.timestamp) - strftime('%s', m.timestamp)) <= 2
        );
    """
    db.execute(text(migrate_sql))
    db.commit()
    post_count = db.execute(text("SELECT COUNT(*) FROM chat_logs")).scalar() or 0
    inserted = post_count - pre_count
    return {
        "normalized_rows": updated.rowcount if hasattr(updated, 'rowcount') else None,
        "pre_count": pre_count,
        "post_count": post_count,
        "migrated_new_rows": inserted
    }

@app.delete("/chat/history/me")
def delete_my_chat_history(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Email claim missing in token")
    db.query(ChatLog).filter(ChatLog.user_id == email.lower()).delete()
    db.commit()
    return {"message": "Chat history deleted"}