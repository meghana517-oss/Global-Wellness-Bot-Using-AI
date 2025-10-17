# 🌍 Global Wellness Bot Using AI

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-frontend-green)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-blue)](https://fastapi.tiangolo.com/)
[![Rasa](https://img.shields.io/badge/Rasa-NLU-orange)](https://rasa.com/)

**Global Wellness Bot** (WellBot) is an AI-powered multilingual wellness assistant designed to promote mental and physical well-being through intelligent, language-adaptive conversations.

---

## 🚀 Features

✅ **User Management**  
- Register, login, and logout securely  
- JWT authentication for safe access  
- Profile view and update options  
- Forgot/reset password flow  

🧠 **AI-Powered Chatbot**  
- Engages users in wellness-related conversations  
- Offers guidance on fitness, emotions, stress, diet, and lifestyle  
- Uses NLP-based intent classification for contextual responses  

🌐 **Multilingual Support**  
- Supports **English and Hindi** (switch seamlessly)  
- Automatic translation of chatbot responses  

💬 **Query Intelligence & Knowledge Base**  
- Predefined wellness intents (symptoms, prevention, meditation, etc.)  
- Knowledge base with structured, editable data for training  

🧩 **Admin Dashboard**  
- Add/edit wellness knowledge base entries   
- View query logs and chat statistics  

💡 **Interactive UI (Streamlit)**  
- Clean, minimal interface for real-time chat  
- Multi-tab layout: Chat, History, Admin, Settings  
- Dynamic translation and theme toggle  

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **Database** | SQLite (via SQLAlchemy) |
| **Authentication** | JWT (via python-jose) |
| **Password Hashing** | Passlib (bcrypt) |
| **Translation** | Hugging Face / Google Translate API |
| **AI Logic** | Custom NLP + Intent Classification |
| **Cache** | Streamlit Cache / Redis (optional) |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/meghana517-oss/Global-Wellness-Bot-Using-AI.git
cd Global-Wellness-Bot-Using-AI

2️⃣ Backend Setup (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

3️⃣ Frontend Setup (Streamlit)
cd frontend
pip install -r requirements.txt
streamlit run app.py

🏃 Running the Bot with Rasa
1️⃣ Train the Rasa Model
cd rasa
rasa train

2️⃣ Start Rasa Servers
Open two terminals inside rasa/:
(a) Rasa NLU & Core API
rasa run --enable-api
(b) Rasa Actions Server
rasa run actions

3️⃣ End-to-End Flow
graph TD
A[User Message in Streamlit] --> B[FastAPI /respond endpoint]
B --> C[Rasa NLU & Dialogue]
C --> D[Custom Actions (actions.py / actions_kb.py)]
D --> E[FastAPI Response to Streamlit]
E --> F[Translated Reply Shown to User]

📂 Project Structure

Global-Wellness-Bot-Using-AI/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── dialogue_manager.py
│   ├── dialogue_state_machine.py
│   ├── nlu.py
│   ├── nlu_multi.py
│   ├── knowledge_base.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── respond_route.py
│   └── intent_model_multi/
│       ├── classification_report.txt
│       ├── config.json
│       ├── label_map.json
│       ├── special_tokens_map.json
│       ├── tokenizer.json
│       ├── tokenizer_config.json
│       └── vocab.txt
│
├── frontend/
│   ├── app.py
│   └── components/
│
├── rasa/
│   ├── data/
│   │   ├── domain.yml
│   │   ├── nlu.yml
│   │   ├── stories.yml
│   │   └── rules.yml
│   └── actions/
│       ├── __init__.py
│       ├── actions.py
│       └── actions_kb.py
│
├── data_structured/
│   ├── condition_aliases.json
│   ├── intent_dataset.jsonl
│   └── structured_conditions_verified.json
│
├── requirements.txt
├── README.md
└── LICENSE

-> Chatbot Workflow

graph TD
A[User Query] --> B[Language Detection]
B --> C[Translation (if Hindi)]
C --> D[Intent Classification Model]
D --> E[Response Generator / KB Lookup]
E --> F[Translate Back (if needed)]
F --> G[Display Response in Streamlit UI]

-> Example Use Cases

तनाव और मूड में उतार-चढ़ाव कैसे संभालें
पानी की कमी और थकान से कैसे बचें
डेंगू के लक्षण क्या हैं
बच्चों का बुखार हो तो क्या करें
जलने पर प्राथमिक उपचार क्या करें?
what are healthy sleep habits?
How to prevent mosquito bites?
Is ORS good for dehydration?
Which medicine is used for fever?
First aid for cuts and bleeding
Symptoms of malaria and how to treat it
Tips to reduce stress naturally

---

## 🖼️ Screenshots

### 🗣️ Chatbot in Hindi
![Chatbot Hindi](screenshots/chatbot_hindi.png)

### 💬 Chatbot in English
![Chatbot English](screenshots/chatbot_english.png)

### 📊 Admin Dashboard – Overview
![Admin Overview](screenshots/admin_overview.png)

### 📚 Admin Dashboard – Knowledge Base Management
![Admin KB](screenshots/admin_kb.png)

### 📈 Admin Dashboard – Feedback Monitoring
![Feedback Monitoring](screenshots/admin_feedback.png)

### 👥 Admin Dashboard – User Management
![User Management](screenshots/admin_user_management.png)

-> Future Enhancements

Integration with wearable devices (Fitbit, Garmin)
Sentiment-based personalized wellness plans
Voice assistant support (speech-to-text + TTS)

-> 📜 License
This project is licensed under the MIT License.

-> 👩‍💻 Author

Meghana
 🔗 [GitHub](https://github.com/meghana517-oss)

💬 Passionate about AI, NLP, and wellness technologies.