from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

# --- Database setup ---
DATABASE_URL = "sqlite:///C:/Users/bantu/Downloads/Wellbot/backend/wellness.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- Admin model ---
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

# --- Password hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# --- Seed logic ---
def seed_admin():
    db = SessionLocal()
    existing = db.query(Admin).filter(Admin.username == "admin").first()
    if existing:
        print("ℹ️ Admin already exists.")
    else:
        new_admin = Admin(username="admin", password=hash_password("admin123"))
        db.add(new_admin)
        db.commit()
        print("✅ Admin seeded successfully.")

if __name__ == "__main__":
    seed_admin()
