import streamlit as st
import requests
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="WellBot – Your Wellness Hub", page_icon="🌊", layout="wide")

# -----------------------
# Clean Box Component
# -----------------------
def clean_box(title, content_lines):
    content_html = "<br>".join([f"<span style='color:black;'>{line}</span>" for line in content_lines])
    st.markdown(f"""
        <div style="
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        ">
            <h4 style="color: black; margin-top:0;">{title}</h4>
            <p style="font-size:16px; line-height:1.6;">{content_html}</p>
        </div>
    """, unsafe_allow_html=True)

# -----------------------
# Session Defaults
# -----------------------
DEFAULT_SESSION = {
    "token": None,
    "lang": "English",
    "last_login": None,
    "email": "",
    "full_name": "",
    "age": 25,
    "language": "English"
}
for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -----------------------
# Translations
# -----------------------
translations = {
    "English": {
        "home": "Home", "register": "Register", "login": "Login", "profile": "Profile",
        "forgot_pw": "Forgot Password", "logout": "Logout",
        "home_title": "🌊 Welcome to WellBot – Your Global Wellness Companion",
        "home_msg": "Use the sidebar to Register or Login. Once logged in, explore your Profile for wellness tips.",
        "affirmation": "You are doing better than you think. Every small step counts. 💙",
        "reg_success": "🎉 Registration Successful! Please login.",
        "login_success": "✅ Login Successful! Please go to Profile to view your details.",
        "update_success": "✅ Profile updated successfully!",
        "update_fail": "❌ Failed to update profile",
        "tips": ["Stay hydrated 💧", "Practice mindfulness 🧘", "Exercise regularly 🏃"]
    },
    "Hindi": {
        "home": "होम", "register": "रजिस्टर", "login": "लॉगिन", "profile": "प्रोफ़ाइल",
        "forgot_pw": "पासवर्ड भूल गए", "logout": "लॉगआउट",
        "home_title": "🌊 वेलबॉट – आपका वैश्विक वेलनेस साथी",
        "home_msg": "साइडबार से पंजीकरण करें या लॉगिन करें। लॉगिन के बाद प्रोफ़ाइल में वेलनेस टिप्स देखें।",
        "affirmation": "आप उम्मीद से बेहतर कर रहे हैं। हर छोटा कदम मायने रखता है। 💙",
        "reg_success": "🎉 पंजीकरण सफल! कृपया लॉगिन करें।",
        "login_success": "✅ लॉगिन सफल! कृपया अपनी जानकारी देखने के लिए प्रोफ़ाइल पर जाएं।",
        "update_success": "✅ प्रोफ़ाइल सफलतापूर्वक अपडेट की गई!",
        "update_fail": "❌ प्रोफ़ाइल अपडेट विफल",
        "tips": ["पानी पिएं 💧", "माइंडफुलनेस का अभ्यास करें 🧘", "नियमित व्यायाम करें 🏃"]
    }
}
T = translations[st.session_state.lang]

# -----------------------
# Sidebar Navigation
# -----------------------
st.sidebar.title("🌐 Navigation")
choice = st.sidebar.radio("Go to", [T["home"], T["register"], T["login"], T["profile"], T["forgot_pw"], T["logout"]])

# Language Switcher
lang_choice = st.sidebar.radio("🌍 Language", ["English", "Hindi"])
if lang_choice != st.session_state.lang:
    st.session_state.lang = lang_choice
    st.rerun()
T = translations[st.session_state.lang]

# -----------------------
# Home Page
# -----------------------
if choice == T["home"]:
    st.title(T["home_title"])
    st.markdown("### 🌱 Daily Affirmation")
    st.success(T["affirmation"])
    st.markdown("### 🧭 How to Begin")
    st.info(T["home_msg"])

# -----------------------
# Registration
# -----------------------
elif choice == T["register"]:
    st.subheader(T["register"])
    with st.form("register_form", clear_on_submit=False):
        email = st.text_input("Email", value=st.session_state.email)
        full_name = st.text_input("Full Name", value=st.session_state.full_name)
        age = st.number_input("Age", min_value=1, max_value=120, step=1, value=st.session_state.age)
        language = st.selectbox("Preferred Language", ["English", "Hindi"], index=["English", "Hindi"].index(st.session_state.language))
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Register")

        if submit:
            res = requests.post(f"{API_URL}/register", json={
                "email": email, "full_name": full_name,
                "age": age, "language": language, "password": password
            })
            if res.status_code == 200:
                st.session_state.token = None
                st.session_state.last_login = None
                st.session_state.email = email
                st.session_state.full_name = full_name
                st.session_state.age = age
                st.session_state.language = language
                placeholder = st.empty()
                for dots in ["", ".", "..", "..."]:
                    placeholder.success(T["reg_success"] + dots)
                    time.sleep(0.4)
                placeholder.success(T["reg_success"])
            else:
                st.error(res.json().get("detail", "Registration failed"))

# -----------------------
# Login
# -----------------------
elif choice == T["login"]:
    st.subheader(T["login"])
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", value=st.session_state.get("email", ""))
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            res = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
            if res.status_code == 200:
                st.session_state.token = res.json()["access_token"]
                st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.email = email
                placeholder = st.empty()
                for dots in ["", ".", "..", "..."]:
                    placeholder.success(T["login_success"] + dots)
                    time.sleep(0.4)
                placeholder.success(T["login_success"])
            else:
                st.error(res.json().get("detail", "Login failed"))
# -----------------------
# Profile
# -----------------------
elif choice == T["profile"]:
    if not st.session_state.token:
        st.warning("⚠ Please login first.")
    else:
        st.subheader(T["profile"])
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        res = requests.get(f"{API_URL}/profile", headers=headers)

        if res.status_code == 200:
            profile = res.json()
            st.session_state.email = profile["email"]
            st.session_state.full_name = profile["full_name"]
            st.session_state.age = profile["age"]
            st.session_state.language = profile["language"]
        else:
            st.error("❌ Failed to fetch profile. Please login again.")
            st.session_state.token = None
            st.stop()

        st.markdown("### 👤 Your Profile Details")
        profile_lines = [
            f" Email: {st.session_state.email}",
            f" Full Name: {st.session_state.full_name}",
            f" Age: {st.session_state.age}",
            f" Preferred Language: {st.session_state.language}",
            f" Last Login: {st.session_state.last_login}"
        ]
        clean_box("👤 Profile Overview", profile_lines)

        st.markdown("### Wellness Tips for You")
        tips_lines = [f"🌿 {tip}" for tip in T["tips"]]
        clean_box("🌿 Wellness Tips", tips_lines)

        with st.expander("✏️ Update Profile"):
            with st.form("update_profile_form"):
                new_full_name = st.text_input("Full Name", value=st.session_state.full_name)
                new_age = st.number_input("Age", min_value=1, max_value=120, value=st.session_state.age)
                new_language = st.selectbox("Preferred Language", ["English", "Hindi"], index=["English", "Hindi"].index(st.session_state.language))
                submit = st.form_submit_button("Update")

                if submit:
                    res = requests.put(f"{API_URL}/profile", headers=headers, json={
                        "full_name": new_full_name,
                        "age": new_age,
                        "language": new_language
                    })
                    if res.status_code == 200:
                        st.session_state.full_name = new_full_name
                        st.session_state.age = new_age
                        st.session_state.language = new_language
                        st.success(T["update_success"])
                    else:
                        st.error(T["update_fail"])

# -----------------------
# Forgot Password
# -----------------------
elif choice == T["forgot_pw"]:
    st.subheader(T["forgot_pw"])
    with st.form("forgot_pw_form"):
        email = st.text_input("Email", value=st.session_state.get("email", ""))
        new_password = st.text_input("New Password", type="password")
        submit = st.form_submit_button("Reset Password")

        if submit:
            res = requests.put(f"{API_URL}/forgot-password", json={
                "email": email,
                "new_password": new_password
            })
            if res.status_code == 200:
                st.success("✅ " + T["login"] + " again with your new password.")
            else:
                st.error(res.json().get("detail", "Password reset failed"))

# -----------------------
# Logout
# -----------------------
elif choice == T["logout"]:
    for key in DEFAULT_SESSION:
        st.session_state[key] = DEFAULT_SESSION[key]
    st.success("✅ Logged out successfully!")
