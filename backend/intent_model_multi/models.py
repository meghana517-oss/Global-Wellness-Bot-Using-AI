from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# 🧑 User profile and authentication
class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    language = Column(String, default="English")
    hashed_password = Column(String, nullable=False)

# 💬 Dialogue intent and response mapping
class Dialogue(Base):
    __tablename__ = "dialogues"
    intent = Column(String, primary_key=True)
    response = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)

# 🩺 Symptom descriptions
class Symptom(Base):
    __tablename__ = "symptoms"
    symptom_name = Column(String, primary_key=True)
    description = Column(String, nullable=False)

# 💊 Medication suggestions
class Medication(Base):
    __tablename__ = "medications"
    condition = Column(String, primary_key=True)
    medicine_name = Column(String, nullable=False)

# 🆘 First aid instructions
class FirstAid(Base):
    __tablename__ = "first_aid"
    issue = Column(String, primary_key=True)
    steps = Column(String, nullable=False)

# 🌱 Wellness tips
class WellnessTip(Base):
    __tablename__ = "wellness_tips"
    id = Column(Integer, primary_key=True)
    tip_text = Column(String, nullable=False)
    category = Column(String, nullable=False)

# 📜 Message history for user-bot interactions
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    user_text = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
