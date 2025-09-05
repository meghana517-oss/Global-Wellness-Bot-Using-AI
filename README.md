🌊 WellBot – Global Wellness Chatbot

WellBot is a Global Wellness Hub that helps users register, log in, manage their profiles, and access wellness tips in multiple languages (English & Hindi).  
It is built with a Streamlit frontend and a FastAPI backend with JWT-based authentication.

🚀 Features
- 👤 User Authentication (Register, Login, Logout)
- 🔐 Secure JWT Authentication
- 📋 Profile Management (view & update details)
- 🌍 Multilingual Support (English & Hindi)
- 🔑 Forgot Password Reset
- 💡 Wellness Tips

--> Tech Stack
# Frontend
- Streamlit
- Python 'requests'

# Backend
- FastAPI
- SQLite (via SQLAlchemy)
- JWT (via python-jose)
- Passlib (bcrypt hashing)

--> How to Run
## Backend (FastAPI)
```bash
cd backend 
uvicorn main:app --reload

