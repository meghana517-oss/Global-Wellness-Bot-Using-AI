from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from main import Feedback, Base

DATABASE_URL = "sqlite:///./wellness.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

sample_feedback = [
    {
        "query_text": "tell me about dengue",
        "response_text": "Dengue is a mosquito-borne viral infection that causes flu-like illness and can develop into severe dengue.\nHigh fever\nEncourage rest, hydration, and paracetamol for fever. Avoid aspirin or ibuprofen.\nUse mosquito nets, wear long sleeves, and eliminate standing water around your home.\nThis information is for educational purposes only and should not be considered medical advice. Please consult a healthcare professional for personalized guidance.",
        "thumbs": "down",
        "comment": "can be more informative",
        "sentiment": "negative",
        "timestamp": datetime.utcnow()
    },
    {
        "query_text": "symptoms of typhoid",
        "response_text": "Typhoid is a bacterial infection caused by Salmonella typhi, typically spread through contaminated food or water.\nProlonged fever, weakness, stomach pain, headache, and loss of appetite.\nEncourage fluid intake, rest, and seek medical care for antibiotics.\nDrink clean water, wash hands before eating, and avoid street food in unsanitary conditions.\nThis information is for educational purposes only and should not be considered medical advice. Please consult a healthcare professional for personalized guidance.",
        "thumbs": "up",
        "comment": "this was helpful",
        "sentiment": "positive",
        "timestamp": datetime.utcnow()
    },
    {
        "query_text": "can u give first aid for cuts",
        "response_text": "Cuts are open wounds caused by sharp objects.\nBleeding, pain, redness, and swelling.\nClean the wound, apply pressure, and cover with a sterile bandage.\nUse protective gear and handle sharp tools carefully.\nThis information is for educational purposes only and should not be considered medical advice. Please consult a healthcare professional for personalized guidance.",
        "thumbs": "up",
        "comment": "yes . the response is good",
        "sentiment": "positive",
        "timestamp": datetime.utcnow()
    },
    {
        "query_text": "what are healthy sleep habits?",
        "response_text": "Sleep hygiene refers to habits that help you sleep well and wake refreshed.\nDifficulty falling asleep, frequent waking, daytime fatigue.\nMaintain a regular sleep schedule, avoid screens before bed, and create a calm environment.\nLimit caffeine, exercise regularly, and reduce stress.\nThis information is for educational purposes only and should not be considered medical advice.",
        "thumbs": "up",
        "comment": "this response was informative",
        "sentiment": "positive",
        "timestamp": datetime.utcnow()
    },
    {
        "query_text": "पानी की कमी और थकान से कैसे बचें",
        "response_text": "निर्जलीकरण तब होता है जब शरीर में तरल पदार्थ की कमी हो जाती है।\nथकान लगातार थकावट या ऊर्जा की कमी की भावना है।\nमुंह का सूखना, चक्कर आना, थकान, गहरे रंग का मूत्र और मूत्र की कमी।\nकम ऊर्जा, ध्यान केंद्रित करने में कठिनाई, नींद आना और कमजोरी।\nधीरे-धीरे पानी पिएं, ओआरएस का उपयोग करें और ठंडी जगह पर आराम करें।\nआराम करें, पानी पिएं, पौष्टिक भोजन करें और अत्यधिक मेहनत से बचें।\nगर्म मौसम या शारीरिक गतिविधि के दौरान नियमित रूप से पानी पिएं।\nसंतुलित दिनचर्या बनाए रखें, अच्छी नींद लें और तनाव को नियंत्रित करें।\nयह जानकारी केवल शैक्षिक उद्देश्यों के लिए है और इसे चिकित्सीय सलाह नहीं माना जाना चाहिए। कृपया व्यक्तिगत मार्गदर्शन के लिए स्वास्थ्य विशेषज्ञ से परामर्श करें।",
        "thumbs": "up",
        "comment": "यह उत्तर बहुत सहायक और स्पष्ट था, धन्यवाद!",
        "sentiment": "positive",
        "timestamp": datetime.utcnow()
    },
    {
        "query_text": "How to prevent mosquito bites?",
        "response_text": "Mosquito protection helps prevent diseases like dengue, malaria, and chikungunya.\nMosquito bites may cause itching, swelling, and risk of viral infection.\nClean the bite area, apply soothing lotion, and avoid scratching.\nUse mosquito nets, wear long sleeves, and eliminate standing water.\nThis information is for educational purposes only and should not be considered medical advice. Please consult a healthcare professional for personalized guidance.",
        "thumbs": "down",
        "comment": "can be more informative",
        "sentiment": "negative",
        "timestamp": datetime.utcnow()
    },
    {
        "query_text": "बच्चों का बुखार हो तो क्या करें",
        "response_text": "बुखार शरीर के तापमान में अस्थायी वृद्धि है, जो आमतौर पर संक्रमण के कारण होती है।\nउच्च तापमान, ठंड लगना, पसीना आना, सिरदर्द और थकान।\nआराम करें, हाइड्रेटेड रहें और बुखार कम करने के लिए पैरासिटामोल लें।\nस्वच्छता बनाए रखें और संक्रमित लोगों से संपर्क से बचें।\nयह जानकारी केवल शैक्षिक उद्देश्यों के लिए है और इसे चिकित्सीय सलाह नहीं माना जाना चाहिए। कृपया व्यक्तिगत मार्गदर्शन के लिए स्वास्थ्य विशेषज्ञ से परामर्श करें।",
        "thumbs": "up",
        "comment": "good one",
        "sentiment": "positive",
        "timestamp": datetime.utcnow()
    }
]

def seed_feedback():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    for fb in sample_feedback:
        db.add(Feedback(**fb))
    db.commit()
    db.close()
    print("✅ Seeded feedback table with sample entries.")

if __name__ == "__main__":
    seed_feedback()
