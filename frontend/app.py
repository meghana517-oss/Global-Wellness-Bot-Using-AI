import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from googletrans import Translator
import time
from functools import lru_cache
try:
    from deep_translator import GoogleTranslator as DeepGoogleTranslator
except Exception:
    DeepGoogleTranslator = None

API_URL = API_URL = "http://127.0.0.1:8000"
translator = Translator()

# -----------------------
# Cached fetch helpers
# -----------------------
@st.cache_data(ttl=60, show_spinner=False)
def cached_query_trends(days: int, headers: dict):
    try:
        res = requests.get(f"{API_URL}/analytics/query-trends?days={days}", headers=headers)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def localize_dates(date_list, lang):
    if lang != "Hindi":
        return date_list
    # Hindi month mapping
    months = {
        "01": "जन", "02": "फ़र", "03": "मार्च", "04": "अप्रै", "05": "मई", "06": "जून",
        "07": "जुल", "08": "अग", "09": "सित", "10": "अक्टू", "11": "नव", "12": "दिस"
    }
    localized = []
    for d in date_list:
        try:
            # Try YYYY-MM-DD
            parts = d.split('-')
            if len(parts) == 3:
                y, m, day = parts
                localized.append(f"{day} {months.get(m,m)}")
            # Try DD/MM/YYYY
            elif '/' in d:
                day, m, y = d.split('/')
                localized.append(f"{day} {months.get(m,m)}")
            # Try MM/DD/YYYY
            elif len(parts) == 3 and int(parts[0]) <= 12:
                m, day, y = parts
                localized.append(f"{day} {months.get(m,m)}")
            else:
                localized.append(d)
        except Exception:
            localized.append(d)
    return localized

# -----------------------
# Dynamic Translation Function
# -----------------------
@lru_cache(maxsize=5000)
def _auto_translate_cached(text: str, dest: str) -> str:
    """Internal cached auto translation using googletrans first, then deep_translator.
    This reduces repeated network calls for the same UI strings.
    """
    if not text:
        return text
    # Try primary googletrans instance (already instantiated as 'translator')
    try:
        return translator.translate(text, dest=dest).text
    except Exception:
        pass
    # Fallback: deep_translator if available
    if DeepGoogleTranslator is not None:
        try:
            return DeepGoogleTranslator(source="auto", target=dest).translate(text)
        except Exception:
            pass
    # Last resort: return original
    return text

def translate(text, lang):
    # Custom curated overrides for critical UX phrases (more reliable than MT)
    hindi_fallback = {
        "This email is already registered. Please login instead.": "यह ईमेल पहले से पंजीकृत है। कृपया लॉगिन करें।",
        "Registration successful!": "पंजीकरण सफल रहा!",
    "Registration successful! Please login.": "पंजीकरण सफल रहा! कृपया लॉगिन करें।",
        "Login successful!": "लॉगिन सफल रहा!",
    "Login successful! Please view your profile.": "लॉगिन सफल रहा! कृपया अपनी प्रोफ़ाइल देखें।",
    "Email already registered. Login successful! Redirecting to profile...": "ईमेल पहले से पंजीकृत है। लॉगिन सफल! प्रोफ़ाइल पर ले जाया जा रहा है...",
        "⚠ This email is already registered. Please login instead.": "⚠ यह ईमेल पहले से पंजीकृत है। कृपया लॉगिन करें।",
        "⚠ No account found with this email. Please register first.": "⚠ इस ईमेल से कोई खाता नहीं मिला। कृपया पहले पंजीकरण करें।",
        "⚠ Incorrect password. Please try again or reset it.": "⚠ पासवर्ड गलत है। कृपया पुनः प्रयास करें या इसे रीसेट करें।",
        "Profile updated successfully.": "प्रोफ़ाइल सफलतापूर्वक अपडेट की गई।",
        "Password must be at least 6 characters.": "पासवर्ड कम से कम 6 अक्षरों का होना चाहिए।",
        "Email and password cannot be empty.": "ईमेल और पासवर्ड खाली नहीं हो सकते।",
        "Please login first.": "कृपया पहले लॉगिन करें।",
        "Failed to fetch profile. Please login again.": "प्रोफ़ाइल प्राप्त करने में विफल। कृपया पुनः लॉगिन करें।",
        "Wellness Tips for You": "आपके लिए वेलनेस टिप्स",
        "Wellness Tips": "वेलनेस टिप्स",
        "Stay hydrated.": "पानी पीते रहें।",
        "Exercise regularly.": "नियमित व्यायाम करें।",
        "Eat balanced meals.": "संतुलित भोजन करें।",
        "Your Profile Details": "आपकी प्रोफ़ाइल जानकारी",
        "Profile Overview": "प्रोफ़ाइल अवलोकन",
        "Logout successful.": "आप सफलतापूर्वक लॉगआउट हो गए हैं।",
        "Password reset successful.": "पासवर्ड रीसेट सफल रहा।",
        "Registration failed": "पंजीकरण विफल रहा।",
        "Login failed": "लॉगिन विफल रहा।",
        "Failed to update profile.": "प्रोफ़ाइल अपडेट करने में विफल।",
        "Password reset failed": "पासवर्ड रीसेट विफल रहा।",
        "Feedback submitted successfully.": "प्रतिक्रिया सफलतापूर्वक सबमिट की गई।",
        "Failed to submit feedback.": "प्रतिक्रिया सबमिट करने में विफल।",
        "Add New Entry": "नई प्रविष्टि जोड़ें",
        "Edit/Delete Existing Entry": "मौजूदा प्रविष्टि संपादित/हटाएं",
        "Entry added (demo only)": "प्रविष्टि जोड़ी गई (डेमो के लिए)",
        "Admin login successful!": "एडमिन लॉगिन सफल रहा!",
        "Invalid admin credentials.": "अमान्य एडमिन क्रेडेंशियल्स।",
        "Failed to fetch KB entries.": "KB प्रविष्टियाँ प्राप्त करने में विफल।",
        "Total Users": "कुल उपयोगकर्ता",
        "Unmatched Queries Today": "आज की अप्रयुक्त क्वेरीज़",
        "Top 10 Questions": "शीर्ष 10 प्रश्न",
        "Positive Feedback %": "सकारात्मक प्रतिक्रिया %",
        "Negative Feedback %": "नकारात्मक प्रतिक्रिया %",
        "Top Feedbacks": "शीर्ष प्रतिक्रियाएँ",
        "Unmatched Queries": "अप्रयुक्त क्वेरीज़",
        "Expand your KB by reviewing these queries.": "इन क्वेरीज़ की समीक्षा करके अपना KB बढ़ाएँ।"
    }
    if lang == "Hindi":
        if text in hindi_fallback:
            return hindi_fallback[text]
        # Use cached auto translation pipeline
        return _auto_translate_cached(text, "hi")
    return text


# Top-level language detection helper used across the app
def detect_lang_from_text(text: str) -> str:
    """Return 'Hindi' if text contains Devanagari characters, else 'English'."""
    if not isinstance(text, str) or not text:
        return "English"
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        return "Hindi"
    return "English"

# -----------------------
# Helpers: Content Translation for Tables
# -----------------------
def translate_text_for_display(text: str, lang: str):
    """Translate a single string to Hindi for display if needed.
    Skips if already contains Devanagari characters or is obviously non-linguistic.
    """
    if lang != "Hindi" or not isinstance(text, str):
        return text


    t = text.strip()
    if not t:
        return text
    # Skip if already Hindi (has Devanagari)
    if any('\u0900' <= ch <= '\u097F' for ch in t):
        return text
    # Skip very short tokens or emails / URLs
    lower_t = t.lower()
    if '@' in lower_t or lower_t.startswith('http'):
        return text
    if len(t) < 3:
        return text
    try:
        return translate(t, lang)
    except Exception:
        return text

def localize_dataframe_content(df: pd.DataFrame, lang: str, columns: list):
    """Return a copy of df with specified textual columns translated for display."""
    if lang != "Hindi":
        return df
    if df is None or df.empty:
        return df
    df_loc = df.copy()
    for col in columns:
        if col in df_loc.columns:
            try:
                df_loc[col] = df_loc[col].astype(str).apply(lambda v: translate_text_for_display(v, lang))
            except Exception:
                pass
    return df_loc

# -----------------------
# Helper: Save a single chat turn to backend (idempotent by (email, query, timestamp))
# -----------------------
def save_chat_turn(email: str, query: str, response: str, comment: str, timestamp: str):
    if not email or not query or not response:
        return
    payload = {
        "email": email.strip().lower(),
        "query": query,
        "response": response,
        "comment": comment or "",
        "timestamp": timestamp,
        # Default language metadata - can be overridden per-turn when available
        "query_lang": st.session_state.language,
        "response_lang": st.session_state.language
    }
    try:
        headers = {}
        if st.session_state.get("token"):
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        res = requests.post(f"{API_URL}/chat/save-history", json=payload, headers=headers, timeout=5)
        # Retry once without / with auth swapped if 401
        if res.status_code == 401 and "Authorization" not in headers and st.session_state.get("token"):
            headers["Authorization"] = f"Bearer {st.session_state.token}"
            res = requests.post(f"{API_URL}/chat/save-history", json=payload, headers=headers, timeout=5)
        if res.status_code == 401 and st.session_state.get("debug_chat"):
            # Log token presence debugging
            token_present = bool(st.session_state.get("token"))
        if st.session_state.get("debug_chat"):
            body = None
            try:
                body = res.text[:200]
            except Exception:
                body = None
            log = st.session_state.get("chat_debug_log", [])
            log.append({
                "event": "save_chat_turn",
                "status": res.status_code,
                "payload": payload,
                "auth_used": "Authorization" in headers,
                "response_snippet": body
            })
            st.session_state.chat_debug_log = log[-50:]
    except Exception as e:
        if st.session_state.get("debug_chat"):
            log = st.session_state.get("chat_debug_log", [])
            log.append({
                "event": "save_chat_turn_error",
                "error": str(e),
                "payload": payload
            })
            st.session_state.chat_debug_log = log[-50:]

# -----------------------
# Session State Defaults
# -----------------------
DEFAULT_SESSION = {
    "language": "English",
    "token": None,
    "last_login": None,
    "email": "",
    "full_name": "",
    "age": 18,
    "chat_history": [],
    "last_query": "",
    "admin_logged_in": False,
    "admin_token": None,
    "admin_tab": None,
    "admin_just_logged_in": False,
    "debug_chat": False,
    "chat_debug_log": []
}
for k, v in DEFAULT_SESSION.items():
    if k not in st.session_state:
        st.session_state[k] = v
# -----------------------
# Sidebar Setup
# -----------------------
st.sidebar.title(translate("🌐 Navigation", st.session_state.language))
st.sidebar.write(f"Current language: {st.session_state.language}")

lang_choice = st.sidebar.radio(
    translate("🌍 Language", st.session_state.language),
    ["English", "Hindi"],
    index=["English", "Hindi"].index(st.session_state.language)
)

if lang_choice != st.session_state.language:
    st.session_state.language = lang_choice

    # ✅ Strictly filter chat history by selected language
    def normalize_chat_history(lang):
            filtered = []
            for turn in st.session_state.chat_history:
                # Use recorded metadata if present, otherwise detect from text
                q_lang = turn.get("query_lang") or detect_lang_from_text(turn.get("query", ""))
                r_text = turn.get("response_en") or turn.get("response_hi") or turn.get("response", "")
                r_lang = turn.get("response_lang") or detect_lang_from_text(r_text)
                if q_lang == lang and r_lang == lang:
                    # ensure metadata present for future switches
                    turn["query_lang"] = q_lang
                    turn["response_lang"] = r_lang
                    filtered.append(turn)
            st.session_state.chat_history = filtered

    normalize_chat_history(lang_choice)
    st.rerun()

# ✅ Now build the menu
def build_menu():
    lang = st.session_state.language
    home = translate("Home", lang)
    register = translate("Register", lang)
    login = translate("Login", lang)
    profile = translate("Profile", lang)
    logout = translate("Logout", lang)
    chatbot = translate("Chatbot", lang)
    admin_lbl = translate("Admin", lang)
    items = [home]
    if not st.session_state.get("token"):
        items += [register, login, chatbot]
    else:
        items += [profile, chatbot, logout]
    if admin_lbl not in items:
        items.append(admin_lbl)
    return items

menu = build_menu()

# Fix: Set menu_choice before selectbox if redirect is pending
if st.session_state.get("pending_redirect"):
    st.session_state.menu_choice = st.session_state.pending_redirect
    st.session_state.pending_redirect = None
    st.rerun()

choice = st.sidebar.selectbox(translate("📌 Menu", st.session_state.language), menu, key="menu_choice")

# -----------------------
# Clean box component
def clean_box(title, content_lines):
    content_html = "<br>".join([f"<span style='color:black;'>{line}</span>" for line in content_lines])
    st.markdown(f"""
        <div style="background-color:white;padding:20px;border-radius:10px;border:1px solid #ddd;margin-bottom:20px;">
            <h4 style="color:black;margin-top:0;">{title}</h4>
            <p style="font-size:16px;line-height:1.6;">{content_html}</p>
        </div>
    """, unsafe_allow_html=True)

# -----------------------
# Home Page
# -----------------------
if choice == translate("Home", st.session_state.language):
    st.title(translate("Welcome to WellBot", st.session_state.language))
    st.markdown(f"### {translate('🌿 Daily Affirmation', st.session_state.language)}")
    st.success(translate("You are strong, capable, and worthy of wellness.", st.session_state.language))
    st.markdown(f"### {translate('🧘 Begin Your Wellness Journey', st.session_state.language)}")
    st.info(translate("Use the sidebar to explore features like chatbot, profile, and feedback.", st.session_state.language))

# -----------------------
# Registration
elif choice == translate("Register", st.session_state.language):
    st.subheader(translate("Register", st.session_state.language))
    # If already logged in, don't auto-redirect; inform user.
    if st.session_state.get("token"):
        st.info(translate("You are already logged in. Go to your profile or logout first to register a new account.", st.session_state.language))
        go_col1, go_col2 = st.columns(2)
        with go_col1:
            if st.button(translate("Go to Profile", st.session_state.language)):
                st.session_state.menu_choice = translate("Profile", st.session_state.language)
                st.rerun()
        with go_col2:
            if st.button(translate("Logout", st.session_state.language)):
                preserved_lang = st.session_state.language
                for key in DEFAULT_SESSION:
                    st.session_state[key] = DEFAULT_SESSION[key]
                st.session_state.language = preserved_lang
                st.success(translate("You have been logged out.", st.session_state.language))
                st.rerun()
        st.stop()
    with st.form("register_form", clear_on_submit=False):
        email = st.text_input(translate("Email", st.session_state.language), value=st.session_state.email)
        full_name = st.text_input(translate("Full Name", st.session_state.language), value=st.session_state.full_name)
        age = st.number_input(translate("Age", st.session_state.language), min_value=1, max_value=120, step=1, value=st.session_state.age)
        language = st.selectbox(translate("Preferred Language", st.session_state.language), ["English", "Hindi"])
        password = st.text_input(translate("Password", st.session_state.language), type="password")
        auto_login_existing = st.checkbox(translate("Auto-login if email already registered", st.session_state.language), value=True)
        st.caption(translate("🔐 Password must be at least 6 characters long.", st.session_state.language))
        submit = st.form_submit_button(translate("Submit", st.session_state.language))

        if submit:
            if len(password) < 6:
                st.error(translate("⚠ Password must be at least 6 characters.", st.session_state.language))
            else:
                norm_email = email.strip().lower()
                res = requests.post(f"{API_URL}/register", json={
                    "email": norm_email, "full_name": full_name,
                    "age": age, "language": language, "password": password
                })
                if res.status_code == 200:
                    # Clear any login state and force redirect to Login
                    preserved_lang = st.session_state.language
                    for key in DEFAULT_SESSION:
                        st.session_state[key] = DEFAULT_SESSION[key]
                    st.session_state.language = preserved_lang
                    st.session_state.email = norm_email
                    st.success(translate("Registration successful! Please login.", st.session_state.language))
                    st.session_state.pending_redirect = translate("Login", st.session_state.language)
                    st.rerun()
                elif res.status_code == 400 and res.json().get("detail") == "User already exists":
                    st.info(translate("⚠ This email is already registered. Please login instead.", st.session_state.language))
                    st.session_state.pending_redirect = translate("Login", st.session_state.language)
                    st.rerun()
                else:
                    st.error(res.json().get("detail", translate("Registration failed", language)))

#------------------------
# Login
elif choice == translate("Login", st.session_state.language):

    st.subheader(translate("Login", st.session_state.language))
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(translate("Email", st.session_state.language), value=st.session_state.get("email", ""))
        password = st.text_input(translate("Password", st.session_state.language), type="password")
        submit = st.form_submit_button(translate("Submit", st.session_state.language))

        if submit:
            if not email or not password:
                st.error(translate("⚠ Email and password cannot be empty.", st.session_state.language))
            else:
                norm_email = email.strip().lower()
                res = requests.post(f"{API_URL}/token", json={"email": norm_email, "password": password})
                if res.status_code == 200:
                    st.session_state.token = res.json()["access_token"]
                    st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.email = norm_email
                    lang = st.session_state.language
                    st.success(translate("Login successful! Please view your profile.", lang))
                    # Redirect user to Profile after short delay
                    st.session_state.pending_redirect = translate("Profile", st.session_state.language)
                    time.sleep(0.4)
                    st.rerun()
                else:
                    # Differentiate user-not-found vs wrong password using /user-exists endpoint
                    try:
                        exists_res = requests.get(f"{API_URL}/user-exists", params={"email": norm_email})
                        exists_json = exists_res.json() if exists_res.status_code == 200 else {"exists": None}
                        if exists_json.get("exists") is False:
                            st.warning(translate("⚠ No account found with this email. Please register first.", st.session_state.language))
                        else:
                            st.error(translate("⚠ Incorrect password. Please try again or reset it.", st.session_state.language))
                    except Exception:
                        st.error(res.json().get("detail", translate("Login failed", st.session_state.language)))



# -----------------------
# Profile
elif choice == translate("Profile", st.session_state.language):
    if not st.session_state.token:
        st.warning(translate("⚠ Please login first.", st.session_state.language))
    else:
        st.subheader(translate("Profile", st.session_state.language))
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        res = requests.get(f"{API_URL}/profile", headers=headers)

        if res.status_code == 200:
            profile = res.json()
            st.session_state.update({
                "email": profile["email"],
                "full_name": profile["full_name"],
                "age": profile["age"]
            })
        else:
            st.error(translate("❌ Failed to fetch profile. Please login again.", st.session_state.language))
            st.session_state.token = None
            st.stop()

        st.markdown("### " + translate("👤 Your Profile Details", st.session_state.language))
        profile_lines = [
            f"{translate('Email', st.session_state.language)}: {st.session_state.email}",
            f"{translate('Full Name', st.session_state.language)}: {st.session_state.full_name}",
            f"{translate('Age', st.session_state.language)}: {st.session_state.age}",
            f"{translate('Preferred Language', st.session_state.language)}: {translate(st.session_state.language, st.session_state.language)}",
            f"{translate('Last Login', st.session_state.language)}: {st.session_state.last_login}"
        ]

        # --- Personalized Greeting & Avatar ---
        colA, colB = st.columns([1,5])
        with colA:
            st.markdown("""
                <div style='width:90px;height:90px;border-radius:50%;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-size:2.5em;color:#2563eb;margin-bottom:10px;'>
                    <span>{}</span>
                </div>
            """.format(st.session_state.full_name[:1] if st.session_state.full_name else "👤"), unsafe_allow_html=True)
        with colB:
            st.markdown(f"## {translate('Hello', st.session_state.language)}, {st.session_state.full_name or st.session_state.email}!")
            st.markdown(f"*{translate('You are strong, capable, and worthy of wellness.', st.session_state.language)}*")
        clean_box(translate("👤 Profile Overview", st.session_state.language), profile_lines)

        st.markdown("### " + translate("Wellness Tips for You", st.session_state.language))
        tips_en = ["Stay hydrated.", "Exercise regularly.", "Eat balanced meals."]
        tips_lines = [f"🌿 {translate(tip, st.session_state.language)}" for tip in tips_en]
        clean_box(translate("🌿 Wellness Tips", st.session_state.language), tips_lines)

        # --- Show Chat History Table ---
        st.markdown("### " + translate("Your Chat History", st.session_state.language))
        try:
            norm_email = st.session_state.email.strip().lower() if st.session_state.email else ""
            headers = {}
            if st.session_state.get("token"):
                headers["Authorization"] = f"Bearer {st.session_state.token}"
            chat_res = requests.get(f"{API_URL}/chat/history/me", headers=headers)
            if chat_res.status_code == 200:
                try:
                    chat_data = chat_res.json()
                except Exception as parse_e:
                    st.error(translate("Failed to parse chat history response.", st.session_state.language) + f" {parse_e}")
                    chat_data = []
                if chat_data:
                    df_chat = pd.DataFrame(chat_data)
                    show_cols = [c for c in ["timestamp","query","response","comment"] if c in df_chat.columns]
                    st.dataframe(df_chat[show_cols])
                    # Add delete button
                    if st.button(translate("Delete Chat History", st.session_state.language)):
                        del_res = requests.delete(f"{API_URL}/chat/history/me", headers=headers)
                        if del_res.status_code == 200:
                            st.success(translate("Chat history deleted.", st.session_state.language))
                            st.session_state.chat_history = []
                            st.rerun()
                        else:
                            st.error(translate("Failed to delete chat history.", st.session_state.language))
                else:
                    st.info(translate("No chat history found.", st.session_state.language))
                    # Debug button: fetch last chat entry for this email
                    if st.button(translate("Show Last Chat Entry (Debug)", st.session_state.language)):
                        debug_res = requests.get(f"{API_URL}/chat/history/me", headers=headers)
                        if debug_res.status_code == 200:
                            try:
                                debug_data = debug_res.json()
                            except Exception:
                                debug_data = []
                            if debug_data:
                                st.write(translate("Last Chat Entry:", st.session_state.language))
                                st.json(debug_data[0])
                            else:
                                st.info(translate("No chat entry found for this email.", st.session_state.language))
                        else:
                            st.error(translate("Failed to fetch last chat entry.", st.session_state.language) + f" (HTTP {debug_res.status_code})")
            else:
                snippet = chat_res.text[:200] if hasattr(chat_res, 'text') else ''
                st.warning(translate("Failed to load chat history.", st.session_state.language) + f" (HTTP {chat_res.status_code})")
                if snippet:
                    st.caption(snippet)
        except Exception as e:
            st.error(translate("Error loading chat history:", st.session_state.language) + f" {e}")

        with st.expander(translate("✏️ Update Profile", st.session_state.language)):
            with st.form("update_profile_form"):
                new_full_name = st.text_input(translate("Full Name", st.session_state.language), value=st.session_state.full_name)
                new_age = st.number_input(translate("Age", st.session_state.language), min_value=1, max_value=120, value=st.session_state.age)
                new_language = st.selectbox(translate("Preferred Language", st.session_state.language), ["English", "Hindi"], index=["English", "Hindi"].index(st.session_state.language))
                submit = st.form_submit_button(translate("Update", st.session_state.language))
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
                        st.success(translate("Profile updated successfully.", st.session_state.language))
                    else:
                        st.error(translate("Failed to update profile.", st.session_state.language))

    # --- Change Password (secure) ---
    with st.expander(translate("🔒 Change Password", st.session_state.language)):
        st.caption(translate("Enter your current password and a new one.", st.session_state.language))
        with st.form("change_pw_form_secure"):
            current_pw = st.text_input(translate("Current Password", st.session_state.language), type="password")
            new_pw = st.text_input(translate("New Password", st.session_state.language), type="password")
            confirm_pw = st.text_input(translate("Confirm New Password", st.session_state.language), type="password")
            submit_pw = st.form_submit_button(translate("Change Password", st.session_state.language))
            if submit_pw:
                if not (current_pw and new_pw and confirm_pw):
                    st.warning(translate("Please fill all fields.", st.session_state.language))
                elif len(new_pw) < 6:
                    st.warning(translate("New password must be at least 6 characters.", st.session_state.language))
                elif new_pw != confirm_pw:
                    st.warning(translate("New passwords do not match.", st.session_state.language))
                elif current_pw == new_pw:
                    st.warning(translate("New password must be different from current password.", st.session_state.language))
                else:
                    try:
                        headers_cp = {"Authorization": f"Bearer {st.session_state.token}"}
                        cp_res = requests.post(
                            f"{API_URL}/auth/change-password",
                            json={"current_password": current_pw, "new_password": new_pw},
                            headers=headers_cp
                        )
                        if cp_res.status_code == 200:
                            st.success(translate("Password changed successfully.", st.session_state.language))
                        else:
                            detail = None
                            try:
                                detail = cp_res.json().get("detail")
                            except Exception:
                                pass
                            st.error(detail or translate("Failed to change password.", st.session_state.language))
                    except Exception as e:
                        st.error(translate("Error changing password:", st.session_state.language) + f" {e}")

    # Separate expander (cannot nest) for forgotten current password fallback
    with st.expander(translate("❓ Forgot Current Password?", st.session_state.language)):
        st.caption(translate("Request a reset token and set a new password if you can't remember the current one.", st.session_state.language))
        reset_email_prof = st.text_input(translate("Email", st.session_state.language), value=st.session_state.email, key="reset_email_profile")
        if st.button(translate("Request Reset Token", st.session_state.language), key="request_reset_token_profile"):
            try:
                resp = requests.post(f"{API_URL}/auth/request-password-reset", json={"email": reset_email_prof.strip().lower()})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "issued":
                        st.session_state.profile_reset_token = data.get("token")
                        st.success(translate("Reset token issued. Check your email or paste below.", st.session_state.language))
                    else:
                        st.info(translate("User not found or no reset required.", st.session_state.language))
                else:
                    st.error(translate("Failed to request reset token.", st.session_state.language))
            except Exception as e:
                st.error(translate("Error requesting reset token:", st.session_state.language) + f" {e}")

        reset_token_prof = st.text_input(translate("Enter Reset Token", st.session_state.language), value=st.session_state.get("profile_reset_token", ""), key="profile_reset_token_input")
        new_pw_token_prof = st.text_input(translate("New Password", st.session_state.language), type="password", key="profile_new_pw_token")
        confirm_pw_token_prof = st.text_input(translate("Confirm New Password", st.session_state.language), type="password", key="profile_confirm_pw_token")
        if st.button(translate("Reset Password", st.session_state.language), key="profile_submit_token_pw"):
            if not (reset_token_prof and new_pw_token_prof and confirm_pw_token_prof):
                st.warning(translate("Please fill all fields.", st.session_state.language))
            elif len(new_pw_token_prof) < 6:
                st.warning(translate("New password must be at least 6 characters.", st.session_state.language))
            elif new_pw_token_prof != confirm_pw_token_prof:
                st.warning(translate("New passwords do not match.", st.session_state.language))
            else:
                try:
                    resp = requests.post(
                        f"{API_URL}/auth/reset-password",
                        json={"token": reset_token_prof, "new_password": new_pw_token_prof}
                    )
                    if resp.status_code == 200:
                        st.success(translate("Password reset successfully. Please login again for security.", st.session_state.language))
                        # Force logout for safety after reset
                        preserved_lang = st.session_state.language
                        email_preserve = st.session_state.email
                        for key in list(st.session_state.keys()):
                            if key not in ["language"]:
                                del st.session_state[key]
                        st.session_state.language = preserved_lang
                        st.session_state.email = email_preserve
                    else:
                        detail = None
                        try:
                            detail = resp.json().get("detail")
                        except Exception:
                            pass
                        st.error(detail or translate("Failed to reset password.", st.session_state.language))
                except Exception as e:
                    st.error(translate("Error resetting password:", st.session_state.language) + f" {e}")

# -----------------------
# Logout (only appears when logged in due to dynamic menu)
elif choice == translate("Logout", st.session_state.language):
    preserved_lang = st.session_state.get("language", "English")
    for key in DEFAULT_SESSION:
        st.session_state[key] = DEFAULT_SESSION[key]
    st.session_state.language = preserved_lang
    st.success(translate("You have been logged out.", st.session_state.language))
    st.rerun()

# -----------------------
# Chatbot Interface
elif choice == translate("Chatbot", st.session_state.language):
    if not st.session_state.get("token"):
        st.warning(translate("Please login to use the chatbot.", st.session_state.language))
        c1, c2 = st.columns(2)
        with c1:
            if st.button(translate("Go to Login", st.session_state.language)):
                st.session_state.menu_choice = translate("Login", st.session_state.language)
                st.rerun()
        with c2:
            if st.button(translate("Register", st.session_state.language)):
                st.session_state.menu_choice = translate("Register", st.session_state.language)
                st.rerun()
        st.stop()
    import difflib
    # Load known conditions/intents for fuzzy matching (cache for session)
    if "known_conditions" not in st.session_state:
        st.session_state.known_conditions = []
        try:
            # First try a lightweight endpoint (if it exists in future)
            res = requests.get(f"{API_URL}/kb/conditions", timeout=5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and all(isinstance(x, str) for x in data):
                    st.session_state.known_conditions = data
            # Fallback: use /kb full objects
            if not st.session_state.known_conditions:
                res2 = requests.get(f"{API_URL}/kb", timeout=8)
                if res2.status_code == 200:
                    data2 = res2.json()
                    names = []
                    if isinstance(data2, list):
                        for entry in data2:
                            if isinstance(entry, dict):
                                en = entry.get("condition_en")
                                hi = entry.get("condition_hi")
                                if en: names.append(en)
                                if hi: names.append(hi)
                    # Deduplicate while preserving order
                    seen = set()
                    deduped = []
                    for n in names:
                        if n not in seen:
                            seen.add(n)
                            deduped.append(n)
                    st.session_state.known_conditions = deduped
        except Exception as e:
            # Leave list empty; optionally log if debug enabled later
            if st.session_state.get("debug_chat"):
                st.session_state.chat_debug_log.append({"event":"known_conditions_load_error","error":str(e)})
    # Bilingual Chatbot Interface
    UI_TEXT = {
        "English": {
            "title": "WellBot – Global Wellness Chatbot",
            "caption": "Current language: English",
            "instruction": "Ask a wellness question",
            "input_label": "Your query",
            "submit_button": "Send",
            "conversation_header": "Conversation",
            "user_label": "You",
            "bot_label": "WellBot"
        },
        "Hindi": {
            "title": "वेलबॉट – वैश्विक स्वास्थ्य सहायक",
            "caption": "वर्तमान भाषा: हिंदी",
            "instruction": "स्वास्थ्य प्रश्न पूछें ",
            "input_label": "आपका प्रश्न",
            "submit_button": "भेजें",
            "conversation_header": "बातचीत",
            "user_label": "आप",
            "bot_label": "वेलबॉट"
        }
    }

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""

    lang = st.session_state.language
    lang_code = "en" if lang == "English" else "hi"
    text = UI_TEXT[lang]

    # Inject enhanced CSS for chat UI
    st.markdown(
        """
        <style>
        .chat-wrapper {max-width:780px; margin:0 auto;}
        .chat-scroll {max-height:520px; overflow-y:auto; padding-right:6px;}
        .chat-container {display:flex; gap:8px; align-items:flex-start;}
        .avatar {width:38px; height:38px; border-radius:50%; background:#e2e8f0; display:flex; align-items:center; justify-content:center; font-weight:600; font-size:0.75rem; color:#334155; flex-shrink:0; box-shadow:0 0 0 1px #cbd5e1 inset;}
        .avatar.bot {background:#2563eb; color:#fff; box-shadow:none;}
        .bubble {padding:10px 14px; border-radius:18px; margin:6px 0 2px; line-height:1.4; font-size:0.92rem; position:relative; max-width:560px;}
        .user-bubble {background:#2563eb; color:#fff; border-top-right-radius:4px; margin-left:auto;}
        .bot-bubble {background:#f1f5f9; color:#111827; border-top-left-radius:4px;}
        .meta {font-size:0.63rem; opacity:0.6; margin:0 4px 12px;}
        .row-user {flex-direction:row-reverse;}
        .row-user .meta {text-align:right;}
        .suggest-row {margin:2px 0 8px 46px; display:flex; flex-wrap:wrap; gap:6px;}
        .suggest-btn {background:#e2e8f0; padding:4px 10px; border-radius:14px; font-size:0.7rem; cursor:pointer; transition:background .15s;}
        .suggest-btn:hover {background:#cbd5e1;}
        .typing-dots {display:inline-flex; gap:4px;}
        .typing-dots span {width:6px; height:6px; background:#64748b; border-radius:50%; animation:blink 1s infinite ease-in-out;}
        .typing-dots span:nth-child(2){animation-delay:.2s}
        .typing-dots span:nth-child(3){animation-delay:.4s}
        @keyframes blink {0%,80%,100%{opacity:.2} 40%{opacity:1}}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title(text["title"])
    st.caption(text["caption"])
    st.write(text["instruction"])

    # Initialize hidden fuzzy matching defaults (no public debug UI)
    if "fuzzy_cutoff" not in st.session_state:
        st.session_state.fuzzy_cutoff = 0.75
    # Ensure debug flags off in production
    st.session_state.debug_chat = False

    # Helper to append chat turns
    def add_turn(query, resp_en, resp_hi):
            # Annotate new turn with detected language metadata for both query and response
            q_lang = detect_lang_from_text(query)
            # Prefer explicit response language if provided, else detect from content
            r_text = resp_en or resp_hi or ""
            r_lang = detect_lang_from_text(r_text)
            st.session_state.chat_history.append({
                "query": query,
                "response_en": resp_en,
                "response_hi": resp_hi,
                "ts": datetime.now().isoformat(),
                "query_lang": q_lang,
                "response_lang": r_lang
            })

    if "awaiting" not in st.session_state:
        st.session_state.awaiting = False

    with st.form("chat_form"):
        query = st.text_input(text["input_label"], value=st.session_state.last_query, disabled=st.session_state.awaiting)
        submitted = st.form_submit_button(text["submit_button"], disabled=st.session_state.awaiting)

        if submitted and query.strip() and not st.session_state.awaiting:
            st.session_state.awaiting = True
            # Fuzzy match/correct query if typo
            orig_query = query.strip()
            best_match = orig_query
            if st.session_state.known_conditions:
                # Map lower-case -> original for case recovery
                lower_map = {c.lower(): c for c in st.session_state.known_conditions if isinstance(c, str)}
                matches = difflib.get_close_matches(
                    orig_query.lower(),
                    list(lower_map.keys()),
                    n=1,
                    cutoff=float(st.session_state.get("fuzzy_cutoff", 0.75))
                )
                if matches:
                    best_match = lower_map[matches[0]]
            st.session_state.last_query = best_match
            # Optimistic add of user message; bot typing placeholder
            # Optimistic user entry with language metadata
            q_lang = detect_lang_from_text(orig_query)
            st.session_state.chat_history.append({
                "query": orig_query,
                "corrected_query": best_match if best_match != orig_query else "",
                "response_en": "",
                "response_hi": "",
                "ts": datetime.now().isoformat(),
                "pending": True,
                "query_lang": q_lang,
                # response_lang will be set once response arrives
            })
            try:
                kb_headers = {}
                if st.session_state.get("token"):
                    kb_headers["Authorization"] = f"Bearer {st.session_state.token}"
                res = requests.post(f"{API_URL}/kb/respond", json={"text": best_match}, headers=kb_headers)
                res.raise_for_status()
                data = res.json()
                # Structured formatting for known queries
                def format_response(data, lang_code):
                    labels = {
                        "en": {
                            "condition": "Condition",
                            "description": "Description",
                            "possible_symptom": "Possible Symptom",
                            "first_aid_tips": "First Aid Tips",
                            "prevention_tips": "Prevention Tips",
                            "disclaimer": "Disclaimer"
                        },
                        "hi": {
                            "condition": "स्थिति",
                            "description": "विवरण",
                            "possible_symptom": "संभावित लक्षण",
                            "first_aid_tips": "प्राथमिक उपचार सुझाव",
                            "prevention_tips": "रोकथाम सुझाव",
                            "disclaimer": "अस्वीकरण"
                        }
                    }
                    parts = []
                    # Condition (show all names if multiple)
                    if "conditions" in data and isinstance(data["conditions"], list):
                        conds = ", ".join([c.get(lang_code, "") for c in data["conditions"] if c.get(lang_code)])
                        if conds:
                            parts.append(f"**{labels[lang_code]['condition']}:**\n{conds}")
                    # Other fields
                    for key in ["description", "possible_symptom", "first_aid_tips", "prevention_tips", "disclaimer"]:
                        if key in data and isinstance(data[key], dict) and data[key].get(lang_code, "").strip():
                            label = labels[lang_code][key]
                            value = data[key][lang_code].strip()
                            parts.append(f"**{label}:**\n{value}")
                    return "\n\n".join(parts)
                # --- Process and populate chatbot response (moved out of format_response to avoid unreachable code) ---
                if isinstance(data, dict):
                    if data.get("fallback") and "message" in data:
                        response_en = data["message"].get("en", "")
                        response_hi = data["message"].get("hi", "")
                        suggestions = data.get("suggestions", [])
                    else:
                        response_en = format_response(data, "en")
                        response_hi = format_response(data, "hi")
                        # Basic heuristic suggestions (first condition names or keywords)
                        suggestions = []
                        if isinstance(data.get("conditions"), list):
                            suggestions = [c.get(lang_code, c.get("en")) for c in data["conditions"]][:3]
                    if not response_en.strip():
                        response_en = "⚠️ Sorry, I couldn't find information on that."
                    if not response_hi.strip():
                        response_hi = "⚠️ माफ़ कीजिए, उस विषय पर जानकारी नहीं मिली।"
                    # Replace pending entry with completed bot answer
                    for item in reversed(st.session_state.chat_history):
                        if item.get("pending") and item["query"] == query:
                            item["response_en"] = response_en
                            item["response_hi"] = response_hi
                            item["pending"] = False
                            item["suggestions"] = suggestions
                            # Mark response language
                            # Prefer explicit content detection on the response_en/hi pair
                            resp_text_for_detect = response_en or response_hi or ""
                            item["response_lang"] = detect_lang_from_text(resp_text_for_detect)
                            # Autosave (only once) if user logged in
                            if st.session_state.get("email") and not item.get("saved"):
                                email_norm = st.session_state.get("email", "").strip().lower()
                                ts_val = item.get("ts", datetime.now().isoformat())
                                # Save using per-item language metadata where possible
                                qlang = item.get("query_lang") or st.session_state.language
                                rlang = item.get("response_lang") or st.session_state.language
                                # Prefer storing English response text canonically
                                save_chat_turn(email_norm, item["query"], response_en or response_hi or "", "", ts_val)
                                item["saved"] = True
                            break
                    st.session_state.last_query = ""
            except Exception as e:
                st.error(f"Failed to get response: {e}")
            finally:
                st.session_state.awaiting = False
            st.rerun()

    # -------------------------------
    # Show Chat History
    # -------------------------------
    if st.session_state.chat_history:
        st.subheader(text["conversation_header"])
        with st.container():
            for item in st.session_state.chat_history:
                ts_fmt = datetime.fromisoformat(item["ts"]).strftime("%H:%M") if item.get("ts") else ""

                # ✅ Choose correct language response or fallback
                response_to_show = item.get("response_en") if lang_code == "en" else item.get("response_hi")
                if not response_to_show:
                    raw_response = item.get("response_en") or item.get("response_hi") or ""
                    response_to_show = translate(raw_response, lang_code)

                is_pending = item.get("pending", False)
                user_bubble = item["query"]

                # 🧍‍♀️ User row
                st.markdown(
                    f"<div class='chat-container row-user'>"
                    f"<div class='avatar'>{text['user_label'][:1]}</div>"
                    f"<div style='flex:1'>"
                    f"<div class='bubble user-bubble'>{user_bubble}</div>"
                    f"<div class='meta'>{text['user_label']} • {ts_fmt}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )

                # 🤖 Bot row
                if is_pending:
                    bot_content = "<div class='typing-dots'><span></span><span></span><span></span></div>"
                else:
                    bot_content = response_to_show

                # Safely build suggestions
                suggestion_html = ""
                if item.get("suggestions") and not is_pending:
                    suggestion_buttons = []
                    for s in item.get("suggestions", []):
                        if s:
                            safe_s = s.replace("'", "\\'")
                            suggestion_buttons.append(
                                f"<span class='suggest-btn' onclick=\"window.parent.postMessage({{'setQuery':'{safe_s}'}}, '*')\">{s}</span>"
                            )
                    suggestion_html = "<div class='suggest-row'>" + "".join(suggestion_buttons) + "</div>"

                st.markdown(
                    f"<div class='chat-container'>"
                    f"<div class='avatar bot'>{text['bot_label'][:1]}</div>"
                    f"<div style='flex:1'>"
                    f"<div class='bubble bot-bubble'>{bot_content}</div>"
                    f"<div class='meta'>{text['bot_label']} • {ts_fmt}</div>"
                    f"{suggestion_html}"
                    f"</div></div>",
                    unsafe_allow_html=True
                )

            # Feedback UI only on last completed bot response
            last_complete = None
            for it in reversed(st.session_state.chat_history):
                if not it.get('pending'):
                    last_complete = it
                    break
            if last_complete:
                response_to_show = last_complete["response_en"] if lang_code == "en" else last_complete["response_hi"]
                feedback_labels = {
                    "English": {
                        "feedback_prompt": "Was this response helpful?",
                        "comment_label": "Leave a comment (optional)",
                        "submit_button": "Submit Feedback",
                        "success": "Feedback submitted successfully.",
                        "error": "Failed to submit feedback."
                    },
                    "Hindi": {
                        "feedback_prompt": "क्या यह उत्तर सहायक था?",
                        "comment_label": "टिप्पणी छोड़ें (वैकल्पिक)",
                        "submit_button": "प्रतिक्रिया सबमिट करें",
                        "success": "प्रतिक्रिया सफलतापूर्वक सबमिट की गई।",
                        "error": "प्रतिक्रिया सबमिट करने में विफल।"
                    }
                }
                fb_text = feedback_labels[lang]
                st.markdown(f"#### 🙋 {fb_text['feedback_prompt']}")
                col1, col2 = st.columns([1,5])
                with col1:
                    st.markdown("<span style='color:#22c55e;font-size:1.1em;'>👍 = Positive</span><br><span style='color:#ef4444;font-size:1.1em;'>👎 = Negative</span>", unsafe_allow_html=True)
                    thumbs = st.radio(
                        "Feedback",
                        ["👍", "👎"],
                        label_visibility="collapsed",
                        key=f"thumb_{last_complete['ts']}"
                    )
                with col2:
                    comment = st.text_input(fb_text["comment_label"], key=f"comment_{last_complete['ts']}")
                if st.button(fb_text["submit_button"], key=f"submit_{last_complete['ts']}"):
                    # Map thumbs to value
                    thumbs_val = "up" if thumbs == "👍" else "down"
                    feedback_payload = {
                        "query_text": last_complete["query"],
                        "response_text": response_to_show,
                        "thumbs": thumbs_val,
                        "comment": comment,
                        "intent": ""
                    }
                    try:
                        # Use API_URL and include auth header for feedback endpoint
                        fb_headers = {}
                        if st.session_state.get("token"):
                            fb_headers["Authorization"] = f"Bearer {st.session_state.token}"
                        fb_res = requests.post(f"{API_URL}/feedback", json=feedback_payload, headers=fb_headers, timeout=5)
                        fb_res.raise_for_status()
                        # Re-save / upsert chat history WITH comment using helper (ensures auth + debug logging)
                        norm_email = st.session_state.get("email", "").strip().lower()
                        if norm_email:
                            ts_val = last_complete.get("ts", datetime.now().isoformat())
                            save_chat_turn(norm_email, last_complete["query"], response_to_show, comment, ts_val)
                            last_complete["saved"] = True
                        st.success(fb_text["success"])
                    except Exception as e:
                        st.error(f"{fb_text['error']} {e}")
            # (Removed legacy per-message feedback block to avoid duplication)

# -----------------------
# Admin Tab Functions (Define First)
# -----------------------
def show_kb_management(T):
    st.markdown("### " + T["admin_add_edit"])

    lang = st.session_state.language
    lang_code = "hi" if lang == "Hindi" else "en"

    try:
        headers = {"Authorization": f"Bearer {st.session_state.admin_token}"} if st.session_state.get("admin_token") else {}
        res = requests.get(f"{API_URL}/kb", headers=headers)
        res.raise_for_status()
        kb_data = res.json()
    except Exception as e:
        st.error(f"{T['admin_load_fail']}: {e}")
        kb_data = []

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = None

    def kb_form(edit_data=None):
        def field(label, key, value=""):
            return st.text_area(label, value=value, key=key)

        # Only show fields for current language; always keep canonical English condition_en (used as key)
        if lang_code == "en":
            condition_en = st.text_input(T["condition_label"], value=(edit_data.get("condition_en") if edit_data else ""), key="condition_en")
            intent_category = st.text_input(T["intent_label"], value=(edit_data.get("intent_category") if edit_data else ""), key="intent_category_en")
            description = field(T["description_label"], "description_en", (edit_data.get("description_en") if edit_data else ""))
            symptom = field(T["symptom_label"], "symptom_en", (edit_data.get("symptom_en") if edit_data else ""))
            first_aid = field(T["first_aid_label"], "first_aid_en", (edit_data.get("first_aid_en") if edit_data else ""))
            prevention = field(T["prevention_label"], "prevention_en", (edit_data.get("prevention_en") if edit_data else ""))
            disclaimer = field(T["disclaimer_label"], "disclaimer_en", (edit_data.get("disclaimer_en") if edit_data else ""))
        else:  # Hindi UI
            # We still need condition_en as identifier; show a subtle read-only display if editing
            condition_en_val = (edit_data.get("condition_en") if edit_data else st.session_state.get("condition_en",""))
            st.text_input(T["condition_label"] + " (EN)", value=condition_en_val, key="condition_en")
            condition_hi = st.text_input(T["condition_label"] + " (हिंदी)", value=(edit_data.get("condition_hi") if edit_data else ""), key="condition_hi")
            intent_category = st.text_input(T["intent_label"], value=(edit_data.get("intent_category") if edit_data else ""), key="intent_category_en")
            description = field(T["description_label"], "description_hi", (edit_data.get("description_hi") if edit_data else ""))
            symptom = field(T["symptom_label"], "symptom_hi", (edit_data.get("symptom_hi") if edit_data else ""))
            first_aid = field(T["first_aid_label"], "first_aid_hi", (edit_data.get("first_aid_hi") if edit_data else ""))
            prevention = field(T["prevention_label"], "prevention_hi", (edit_data.get("prevention_hi") if edit_data else ""))
            disclaimer = field(T["disclaimer_label"], "disclaimer_hi", (edit_data.get("disclaimer_hi") if edit_data else ""))

        if st.button("💾 " + T["save_button"]):
            payload = {"condition_en": st.session_state.get("condition_en",""), "intent_category": st.session_state.get("intent_category_en","")}
            # Attach fields per language present in session_state
            for fld in ["description_en","symptom_en","first_aid_en","prevention_en","disclaimer_en","description_hi","symptom_hi","first_aid_hi","prevention_hi","disclaimer_hi","condition_hi"]:
                if fld in st.session_state and st.session_state[fld]:
                    payload[fld] = st.session_state[fld]
            headers = {"Authorization": f"Bearer {st.session_state.admin_token}"} if st.session_state.get("admin_token") else {}
            try:
                if edit_data:
                    res = requests.put(f"{API_URL}/kb/{edit_data['condition_en']}", json=payload, headers=headers)
                else:
                    res = requests.post(f"{API_URL}/kb", json=payload, headers=headers)
                st.success("✅ " + T["admin_save_success"])
                st.session_state.edit_mode = None
                st.rerun()
            except Exception as e:
                st.error(f"{T['admin_save_fail']}: {e}")

    st.markdown("### " + T["admin_existing"])
    intent_hi_map = {
        "Diseases & Conditions": "बीमारियाँ और स्थितियाँ",
        "Lifestyle & Prevention": "जीवनशैली और रोकथाम",
        "First Aid & Emergency": "प्राथमिक उपचार और आपातकालीन स्थिति",
        "Wellness & Mental Health": "स्वास्थ्य और मानसिक स्वास्थ्य",
        "Symptoms & Diagnosis": "लक्षण और निदान",
        "Special Cases & Care": "विशेष मामले और देखभाल",
        "Others": "अन्य",
        "Uncategorized": "अवर्गीकृत"
    }
    # --- Fetch feedback summary for KB flagging ---
    try:
        fb_summary = requests.get(f"{API_URL}/feedback/comment-summary").json()
    except Exception:
        fb_summary = []
    # Map: condition_en -> negative ratio
    neg_map = {}
    for row in fb_summary:
        cond = row.get("comment", "").lower()
        neg_ratio = row.get("negative_ratio", 0)
        neg_map[cond] = neg_ratio
    neg_threshold = st.session_state.get("neg_feedback_threshold", 0.4)
    for item in kb_data:
        condition_display = item.get(f"condition_{lang_code}", item["condition_en"])
        expander_label = condition_display if condition_display else "KB Entry"
        # Flag if negative feedback ratio exceeds threshold
        flag = False
        cond_key = item["condition_en"].lower()
        for k in neg_map:
            if cond_key in k:
                if neg_map[k] >= neg_threshold:
                    flag = True
                    break
        flag_icon = "❗" if flag else ""
        with st.expander(f"{flag_icon} {expander_label}"):
            intent_en = item.get("intent_category_en", item.get("intent_category", ""))
            intent_hi = item.get("intent_category_hi", "")
            # Show intent category in Hindi if available and Hindi selected, else English
            if lang_code == "hi":
                intent_display = intent_hi if intent_hi else intent_hi_map.get(intent_en, intent_en)
            else:
                intent_display = intent_en
            st.write(f"**{T['intent_label']}:** {intent_display}")
            if flag:
                st.warning(translate("This entry has high negative feedback. Please review.", st.session_state.language))
            st.write(f"**{T['description_label']}:** {item.get(f'description_{lang_code}', '')}")
            st.write(f"**{T['symptom_label']}:** {item.get(f'symptom_{lang_code}', '')}")
            st.write(f"**{T['first_aid_label']}:** {item.get(f'first_aid_{lang_code}', '')}")
            st.write(f"**{T['prevention_label']}:** {item.get(f'prevention_{lang_code}', '')}")
            st.write(f"**{T['disclaimer_label']}:** {item.get(f'disclaimer_{lang_code}', '')}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📝 {T['edit_button']} {expander_label}", key=f"edit_{item['condition_en']}"):
                    st.session_state.edit_mode = item
                    st.rerun()
            with col2:
                headers = {"Authorization": f"Bearer {st.session_state.admin_token}"} if st.session_state.get("admin_token") else {}
                if st.button(f"🗑️ {T['delete_button']} {expander_label}", key=f"delete_{item['condition_en']}" ):
                    try:
                        res = requests.delete(f"{API_URL}/kb/{item['condition_en']}", headers=headers)
                        st.success("🗑️ " + T["admin_delete_success"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"{T['admin_delete_fail']}: {e}")

    kb_form(edit_data=st.session_state.edit_mode)

# --- Admin Dashboard Block ---
if choice == translate("Admin", st.session_state.language):
    st.title(translate("Admin Dashboard", st.session_state.language))
    # --- Early login gate BEFORE creating tabs ---
    if not st.session_state.admin_logged_in:
        st.markdown("### 🔐 " + translate("Login", st.session_state.language))
        admin_user = st.text_input(translate("Username", st.session_state.language), key="admin_user")
        admin_pass = st.text_input(translate("Password", st.session_state.language), type="password", key="admin_pass")
        if st.button(translate("Login", st.session_state.language)):
            uname = (admin_user or "").strip().lower()
            pwd = (admin_pass or "").strip()
            if not uname or not pwd:
                st.warning(translate("Please enter both username and password", st.session_state.language))
            else:
                try:
                    res = requests.post(
                        f"{API_URL}/admin/login",
                        data={"username": uname, "password": pwd},
                        timeout=10
                    )
                    if res.status_code != 200:
                        detail = ""
                        try:
                            detail = res.json().get("detail", "")
                        except Exception:
                            detail = res.text[:200]
                        st.error(f"❌ {translate('Admin login failed', st.session_state.language)} ({res.status_code}) {detail}")
                    else:
                        token = res.json().get("access_token")
                        if not token:
                            st.error(translate("Login succeeded but no token returned", st.session_state.language))
                        else:
                            st.session_state.admin_logged_in = True
                            st.session_state.admin_token = token
                            st.session_state.admin_just_logged_in = True
                            st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ {translate('Admin login failed', st.session_state.language)}: {e}")
        st.stop()

    # --- Now safe to build tabs ---
    tab_labels = [
        translate("Overview", st.session_state.language),
        translate("Knowledge Base", st.session_state.language),
        translate("Analytics & Trends", st.session_state.language),
        translate("Feedback Monitoring", st.session_state.language),
        translate("Query Intelligence", st.session_state.language),
        translate("User Management", st.session_state.language),
        translate("System", st.session_state.language)
    ]
    # Create tabs fresh each run; storing Streamlit element objects in session_state can trigger internal 'setIn' errors
    tabs = st.tabs(tab_labels)
    # Map label -> index for readability
    idx_map = {lbl: i for i, lbl in enumerate(tab_labels)}
    overview_idx = idx_map[translate("Overview", st.session_state.language)]
    kb_idx = idx_map[translate("Knowledge Base", st.session_state.language)]
    analytics_idx = idx_map[translate("Analytics & Trends", st.session_state.language)]
    feedback_idx = idx_map[translate("Feedback Monitoring", st.session_state.language)]
    query_intel_idx = idx_map[translate("Query Intelligence", st.session_state.language)]
    user_mgmt_idx = idx_map[translate("User Management", st.session_state.language)]
    system_idx = idx_map[translate("System", st.session_state.language)]

    # --- Negative feedback threshold slider (persist in session state) ---
    if "neg_feedback_threshold" not in st.session_state:
        st.session_state.neg_feedback_threshold = 0.4  # default 40%
    st.sidebar.markdown("---")
    st.sidebar.subheader(translate("Alert Settings", st.session_state.language))
    st.session_state.neg_feedback_threshold = st.sidebar.slider(
        translate("Negative Feedback Alert Threshold (%)", st.session_state.language),
        min_value=0.1, max_value=0.9, value=float(st.session_state.neg_feedback_threshold), step=0.01
    )

    # Helper for headers
    def _auth_headers():
        return {"Authorization": f"Bearer {st.session_state.admin_token}"} if st.session_state.get("admin_token") else {}

    # Safety: ensure tabs exists
    if 'tabs' not in locals():
        st.error("tabs not initialized – please reload the Admin page.")
        st.stop()
    # --- Overview Tab (High-level snapshot) ---
    with tabs[overview_idx]:
        st.header(translate("Overview", st.session_state.language))
        headers = _auth_headers()
        colA1, colA2, colA3, colA4, colA5 = st.columns(5)
        with colA1:
            try:
                r = requests.get(f"{API_URL}/analytics/total-users", headers=headers)
                total_users = r.json().get("total_users", 0) if r.status_code == 200 else 0
            except Exception:
                total_users = 0
            st.metric(translate("Total Users", st.session_state.language), total_users)
        with colA2:
            try:
                r = requests.get(f"{API_URL}/analytics/health-topics", headers=headers)
                health_topics = r.json().get("health_topics", 0) if r.status_code == 200 else 0
            except Exception:
                health_topics = 0
            st.metric(translate("Health Topics", st.session_state.language), health_topics)
        with colA3:
            try:
                fb_stats_inline = requests.get(f"{API_URL}/feedback/stats").json()
            except Exception:
                fb_stats_inline = {}
            pos_pct_inline = f"{fb_stats_inline.get('positive',0) / max(fb_stats_inline.get('total',1),1) * 100:.1f}%"
            st.metric(translate("Positive Feedback %", st.session_state.language), pos_pct_inline)
        with colA4:
            try:
                q = requests.get(f"{API_URL}/analytics/total-queries", headers=headers)
                total_queries = q.json().get("total_queries", 0) if q.status_code == 200 else 0
            except Exception:
                total_queries = 0
            st.metric(translate("Queries Handled", st.session_state.language), total_queries)
        with colA5:
            try:
                unmatched = requests.get(f"{API_URL}/analytics/unmatched", headers=headers).json()
            except Exception:
                unmatched = []
            st.metric(translate("Unmatched Queries Today", st.session_state.language), len(unmatched) if isinstance(unmatched, list) else 0)
        # Quick trend sparkline
        with st.expander(translate("Recent Query Volume (last 7 days)", st.session_state.language), expanded=True):
            trends7 = cached_query_trends(7, headers)
            if isinstance(trends7, list) and trends7:
                df7 = pd.DataFrame(trends7)
                # Use localized x-axis labels for Hindi instead of default English date strings
                try:
                    x_labels7 = localize_dates(df7['day'].tolist(), st.session_state.language)
                except Exception:
                    x_labels7 = df7['day'].tolist()
                fig7 = go.Figure()
                fig7.add_trace(go.Scatter(
                    x=x_labels7,
                    y=df7['count'],
                    mode='lines+markers',
                    line=dict(color='#2563eb', width=3),
                    marker=dict(size=6)
                ))
                fig7.update_layout(
                    height=220,
                    margin=dict(t=10,l=40,r=20,b=40),
                    xaxis_title=translate('Day', st.session_state.language),
                    yaxis_title=translate('Queries', st.session_state.language),
                    plot_bgcolor='white'
                )
                fig7.update_xaxes(showgrid=False)
                fig7.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
                st.plotly_chart(fig7, use_container_width=True)
            else:
                st.caption(translate("Not enough data for trend.", st.session_state.language))

        # --- Knowledge Base Management Tab ---
        with tabs[kb_idx]:
            st.header(translate("Knowledge Base Management", st.session_state.language))
            show_kb_management({
                "admin_add_edit": translate("Add/Edit KB Entry", st.session_state.language),
                "admin_load_fail": translate("Failed to load KB entries", st.session_state.language),
                "admin_save_success": translate("Entry saved successfully", st.session_state.language),
                "admin_save_fail": translate("Failed to save entry", st.session_state.language),
                "admin_existing": translate("Existing KB Entries", st.session_state.language),
                "admin_delete_success": translate("Entry deleted successfully", st.session_state.language),
                "admin_delete_fail": translate("Failed to delete entry", st.session_state.language),
                "condition_label": translate("Condition Name", st.session_state.language),
                "intent_label": translate("Intent Category", st.session_state.language),
                "description_label": translate("Description", st.session_state.language),
                "symptom_label": translate("Possible Symptom", st.session_state.language),
                "first_aid_label": translate("First Aid Tips", st.session_state.language),
                "prevention_label": translate("Prevention Tips", st.session_state.language),
                "disclaimer_label": translate("Disclaimer", st.session_state.language),
                "save_button": translate("Save", st.session_state.language),
                "edit_button": translate("Edit", st.session_state.language),
                "delete_button": translate("Delete", st.session_state.language)
            })

        # --- Analytics & Trends Tab ---
        with tabs[analytics_idx]:
            st.header(translate("Analytics & Trends", st.session_state.language))
            headers = _auth_headers()
            col_r1, col_r2 = st.columns([2,1])
            with col_r2:
                range_days = st.selectbox(translate("Range (days)", st.session_state.language), [7,14,30], index=1, key="qh_range")
            with col_r1:
                st.markdown(f"#### {translate('Queries Handled Over Time', st.session_state.language)}")
            trends = cached_query_trends(range_days, headers)
            if isinstance(trends, list) and trends:
                df_trend = pd.DataFrame(trends)
                if len(df_trend) >= 3:
                    df_trend['ma3'] = df_trend['count'].rolling(3).mean()
                x_labels = localize_dates(df_trend['day'].tolist(), st.session_state.language)
                fig_q = go.Figure()
                fig_q.add_trace(go.Bar(x=x_labels, y=df_trend['count'], name=translate('Queries', st.session_state.language), marker_color='#2563eb'))
                if 'ma3' in df_trend:
                    fig_q.add_trace(go.Scatter(x=x_labels, y=df_trend['ma3'], mode='lines+markers', name=translate('3-day Avg', st.session_state.language), line=dict(color='#f59e0b', width=3)))
                fig_q.update_layout(margin=dict(t=40,l=40,r=20,b=40), height=360, legend_orientation='h', legend_yanchor='bottom', legend_y=1.02)
                fig_q.update_layout(yaxis_title=translate('Queries', st.session_state.language), xaxis_title=translate('Day', st.session_state.language))
                st.plotly_chart(fig_q, use_container_width=True)
            else:
                st.info(translate("No trend data available.", st.session_state.language))
            # Category distribution pie
            st.markdown("### 🧠 " + translate("Top Query Categories", st.session_state.language))
            try:
                res = requests.get(f"{API_URL}/kb/categories")
                data = res.json()
                df = pd.DataFrame(data)
                category_hi = {
                    "Diseases & Conditions": "बीमारियाँ और स्थितियाँ",
                    "Lifestyle & Prevention": "जीवनशैली और रोकथाम",
                    "First Aid & Emergency": "प्राथमिक उपचार और आपातकालीन स्थिति",
                    "Wellness & Mental Health": "स्वास्थ्य और मानसिक स्वास्थ्य",
                    "Symptoms & Diagnosis": "लक्षण और निदान",
                    "Special Cases & Care": "विशेष मामले और देखभाल",
                    "Others": "अन्य",
                    "Uncategorized": "अवर्गीकृत"
                }
                if st.session_state.language == "Hindi":
                    df["translated"] = df["category"].map(category_hi).fillna(df["category"])
                else:
                    df["translated"] = df["category"]
                fig = px.pie(
                    names=df["translated"],
                    values=df["count"],
                    hole=0.3,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(title_text=translate("Top Query Categories", st.session_state.language), title_font_size=16)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(translate("Failed to load category distribution:", st.session_state.language) + f" {e}")
            colA, colB = st.columns(2)
            with colA:
                st.subheader(translate("Intent Distribution", st.session_state.language))
                try:
                    intent_dist = requests.get(f"{API_URL}/analytics/intent-distribution", headers=headers).json()
                    if isinstance(intent_dist, list) and intent_dist:
                        df_int = pd.DataFrame(intent_dist)
                        df_int = df_int[df_int["intent"] != "kb_lookup"]
                        intent_hi_map = {
                            "Diseases & Conditions": "बीमारियाँ और स्थितियाँ",
                            "Lifestyle & Prevention": "जीवनशैली और रोकथाम",
                            "First Aid & Emergency": "प्राथमिक उपचार और आपातकालीन स्थिति",
                            "Wellness & Mental Health": "स्वास्थ्य और मानसिक स्वास्थ्य",
                            "Symptoms & Diagnosis": "लक्षण और निदान",
                            "Special Cases & Care": "विशेष मामले और देखभाल",
                            "Others": "अन्य",
                            "Uncategorized": "अवर्गीकृत",
                            "unknown": "अज्ञात"
                        }
                        if st.session_state.language == "Hindi":
                            df_int["intent_display"] = df_int["intent"].map(intent_hi_map).fillna(df_int["intent"])
                        else:
                            df_int["intent_display"] = df_int["intent"]
                        st.bar_chart(df_int.set_index("intent_display")["count"])
                except Exception as e:
                    st.warning(translate("Failed to load intent distribution", st.session_state.language) + f": {e}")
            with colB:
                st.subheader(translate("Hourly Activity (UTC Today)", st.session_state.language))
                try:
                    hourly = requests.get(f"{API_URL}/analytics/hourly-activity", headers=headers).json()
                    if isinstance(hourly, list) and hourly:
                        df_hr = pd.DataFrame(hourly)
                        st.line_chart(df_hr.set_index("hour")["count"])
                except Exception as e:
                    st.warning(translate("Failed to load hourly activity", st.session_state.language) + f": {e}")

        # --- Feedback Monitoring Tab (refactored for fewer duplicate requests & caching) ---
        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_feedback_stats():
            try:
                r = requests.get(f"{API_URL}/feedback/stats")
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            return {}

        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_feedback_summary():
            try:
                r = requests.get(f"{API_URL}/feedback/comment-summary")
                if r.status_code == 200:
                    data = r.json()
                    return data if isinstance(data, list) else []
            except Exception:
                pass
            return []

        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_all_feedback(auth_headers):
            try:
                r = requests.get(f"{API_URL}/feedback/all", headers=auth_headers)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            return []

        with tabs[feedback_idx]:
            st.header(translate("Feedback Monitoring", st.session_state.language))
            headers = _auth_headers()
            st.markdown("### 📊 " + translate("Feedback Sentiment Overview", st.session_state.language))
            stats = _cached_feedback_stats()
            if stats:
                positive = stats.get("positive", 0)
                neutral = stats.get("neutral", 0)
                negative = stats.get("negative", 0)
                total = stats.get("total") or (positive + neutral + negative)
                # Build bar data excluding Neutral as requested
                df_bar = pd.DataFrame([
                    {"Sentiment": translate("Positive", st.session_state.language), "Count": positive},
                    {"Sentiment": translate("Negative", st.session_state.language), "Count": negative}
                ])
                # (Neutral still influences percentage metrics via 'total' but is hidden from the chart)
                try:
                    fig = px.bar(
                        df_bar,
                        x="Sentiment",
                        y="Count",
                        color="Sentiment",
                        text="Count",
                        title=translate("Feedback Sentiment Overview", st.session_state.language)
                    )
                    fig.update_layout(
                        xaxis_title=translate("Sentiment", st.session_state.language),
                        yaxis_title=translate("Count", st.session_state.language)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(translate("Failed to render feedback chart:", st.session_state.language) + f" {e}")
                col_pos, col_neg, col_tot = st.columns(3)
                with col_pos:
                    pct_pos = (positive / total * 100) if total else 0
                    st.metric(translate("Positive Feedback %", st.session_state.language), f"{pct_pos:.1f}%")
                with col_neg:
                    pct_neg = (negative / total * 100) if total else 0
                    st.metric(translate("Negative Feedback %", st.session_state.language), f"{pct_neg:.1f}%")
                with col_tot:
                    st.metric(translate("Total Feedback", st.session_state.language), total)
            else:
                st.info(translate("No feedback stats available yet.", st.session_state.language))

            st.markdown(translate("Top Feedbacks", st.session_state.language))
            summary = _cached_feedback_summary()
            if summary:
                top_rows = summary[:10]
                table_lines = [
                    "| " + translate("Comment", st.session_state.language) + " | 👍 | 👎 | " + translate("Total", st.session_state.language) + " | % + | Score |",
                    "| --- | ---: | ---: | ---: | ---: | ---: |"
                ]
                for row in top_rows:
                    comment_txt = translate(row.get("comment", ""), st.session_state.language)[:80]
                    pos_ratio = row.get('positive_ratio', 0)
                    pct = f"{pos_ratio*100:.0f}%"
                    table_lines.append(f"| {comment_txt} | {row.get('up',0)} | {row.get('down',0)} | {row.get('total',0)} | {pct} | {row.get('score','')} |")
                st.markdown("\n".join(table_lines))
            else:
                st.info(translate("No feedback comments yet.", st.session_state.language))

            st.markdown("### 📝 " + translate("All Feedback Entries", st.session_state.language))
            feedbacks = _cached_all_feedback(headers)
            if feedbacks:
                try:
                    df_fb = pd.DataFrame(feedbacks)
                    if "sentiment" in df_fb.columns:
                        df_fb["sentiment"] = df_fb["sentiment"].replace({None: "", "": "", "neutral": ""})
                        df_fb["sentiment"] = df_fb.apply(lambda r: r["sentiment"] if r["sentiment"] else ("👍" if r.get("thumbs")=="up" else ("👎" if r.get("thumbs")=="down" else "")), axis=1)
                    elif "thumbs" in df_fb.columns:
                        df_fb["sentiment"] = df_fb["thumbs"].map({"up": "👍", "down": "👎"})
                    show_cols = [c for c in ["timestamp","query_text","response_text","comment","sentiment"] if c in df_fb.columns]
                    df_show = df_fb[show_cols]
                    df_show = localize_dataframe_content(df_show, st.session_state.language, ["query_text", "response_text", "comment", "sentiment"])
                    if st.session_state.language == "Hindi":
                        col_map = {
                            "timestamp": "समय",
                            "query_text": "प्रश्न",
                            "response_text": "उत्तर",
                            "comment": "टिप्पणी",
                            "sentiment": "भावना"
                        }
                        df_show.columns = [col_map.get(c, c) for c in df_show.columns]
                    st.dataframe(df_show)
                    # CSV download remains
                    csv = df_show.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=translate("Download Feedback CSV", st.session_state.language),
                        data=csv,
                        file_name="feedback.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(translate("Failed to process feedback entries:", st.session_state.language) + f" {e}")
            else:
                st.info(translate("No feedback entries found.", st.session_state.language))

        # --- Query Intelligence Tab (refactored, safe, cached) ---
        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_user_query_table(auth_headers):
            try:
                r = requests.get(f"{API_URL}/analytics/user-query-table-today", headers=auth_headers)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            return []

        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_recent_queries(auth_headers):
            try:
                r = requests.get(f"{API_URL}/analytics/recent-queries", headers=auth_headers)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            return []

        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_top_unknown(auth_headers):
            try:
                r = requests.get(f"{API_URL}/analytics/top-unknown", headers=auth_headers)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            return []

        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_unmatched(auth_headers):
            try:
                r = requests.get(f"{API_URL}/analytics/unmatched", headers=auth_headers)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            return []

        with tabs[query_intel_idx]:
            st.header(translate("Query Intelligence", st.session_state.language))
            headers = _auth_headers()

            # --- User Query Table ---
            st.markdown("### " + translate("User Query Table", st.session_state.language))
            data = _cached_user_query_table(headers)
            if data:
                df = pd.DataFrame(data)
                columns = ["email", "query_text", "bot_response", "intent", "entities", "timestamp"]
                df_show = df[[c for c in columns if c in df.columns]]
                df_show = localize_dataframe_content(df_show, st.session_state.language,
                                                     ["query_text", "bot_response", "intent", "entities"])
                if st.session_state.language == "Hindi":
                    col_map = {
                        "email": "ईमेल",
                        "query_text": "प्रश्न",
                        "bot_response": "बॉट उत्तर",
                        "intent": "इरादा",
                        "entities": "इकाइयाँ",
                        "timestamp": "समय"
                    }
                    df_show.columns = [col_map.get(c, c) for c in df_show.columns]
                st.dataframe(df_show)
            else:
                st.info(translate("No user queries found for today.", st.session_state.language))

            # --- Recent Queries ---
            st.markdown("### " + translate("Recent Queries", st.session_state.language))
            recent = _cached_recent_queries(headers)
            if isinstance(recent, list) and recent:
                df_recent = pd.DataFrame(recent)
                show_cols = [c for c in ["timestamp", "email", "query_text", "intent", "entities", "matched_condition"]
                             if c in df_recent.columns]
                df_show = df_recent[show_cols]
                df_show = localize_dataframe_content(df_show, st.session_state.language,
                                                     ["query_text", "intent", "entities", "matched_condition"])
                if st.session_state.language == "Hindi":
                    col_map = {
                        "timestamp": "समय",
                        "email": "ईमेल",
                        "query_text": "प्रश्न",
                        "intent": "इरादा",
                        "entities": "इकाइयाँ",
                        "matched_condition": "मिली स्थिति"
                    }
                    df_show.columns = [col_map.get(c, c) for c in df_show.columns]
                st.dataframe(df_show)
            else:
                st.info(translate("No recent queries found.", st.session_state.language))

            # --- Unknown Queries ---
            st.markdown("### " + translate("Unknown Queries", st.session_state.language))
            top_unknown = _cached_top_unknown(headers)
            if isinstance(top_unknown, list) and top_unknown:
                df_unknown = pd.DataFrame(top_unknown)
                df_unknown = localize_dataframe_content(df_unknown, st.session_state.language,
                                                        ["query_text", "intent", "bot_response"])
                if st.session_state.language == "Hindi":
                    col_map = {
                        "query_text": "प्रश्न",
                        "intent": "इरादा",
                        "bot_response": "बॉट उत्तर",
                        "count": "गणना"
                    }
                    df_unknown.columns = [col_map.get(c, c) for c in df_unknown.columns]
                st.dataframe(df_unknown)
            else:
                st.info(translate("No unknown queries found.", st.session_state.language))

            # --- Latest Unmatched Samples ---
            st.markdown("### " + translate("Latest Unmatched Samples", st.session_state.language))
            unmatched = _cached_unmatched(headers)
            if isinstance(unmatched, list) and unmatched:
                df_un = pd.DataFrame(unmatched)
                if 'query' in df_un.columns and 'query_text' not in df_un.columns:
                    df_un.rename(columns={'query': 'query_text'}, inplace=True)

                intent_hi_map = {
                    "Diseases & Conditions": "बीमारियाँ और स्थितियाँ",
                    "disease_info": "बीमारियाँ और स्थितियाँ",
                    "Lifestyle & Prevention": "जीवनशैली और रोकथाम",
                    "lifestyle": "जीवनशैली और रोकथाम",
                    "First Aid & Emergency": "प्राथमिक उपचार और आपातकालीन स्थिति",
                    "first_aid": "प्राथमिक उपचार और आपातकालीन स्थिति",
                    "Wellness & Mental Health": "स्वास्थ्य और मानसिक स्वास्थ्य",
                    "wellness": "स्वास्थ्य और मानसिक स्वास्थ्य",
                    "Symptoms & Diagnosis": "लक्षण और निदान",
                    "symptom": "लक्षण और निदान",
                    "Special Cases & Care": "विशेष मामले और देखभाल",
                    "special_case": "विशेष मामले और देखभाल",
                    "Others": "अन्य",
                    "other": "अन्य",
                    "Uncategorized": "अवर्गीकृत",
                    "uncategorized": "अवर्गीकृत"
                }

                if st.session_state.language == "Hindi" and "intent" in df_un.columns:
                    df_un["intent"] = df_un["intent"].map(intent_hi_map).fillna(df_un["intent"])

                df_un = localize_dataframe_content(df_un, st.session_state.language, ["query_text"])
                if st.session_state.language == "Hindi":
                    col_map = {
                        "query_text": "प्रश्न",
                        "intent": "इरादा",
                        "timestamp": "समय"
                    }
                    df_un.columns = [col_map.get(c, c) for c in df_un.columns]

                st.dataframe(df_un)
            else:
                st.info(translate("No unmatched queries right now.", st.session_state.language))

            st.caption(translate("Expand your KB by reviewing unmatched and unknown queries.",
                                 st.session_state.language))

        # --- User Management Tab ---
        with tabs[user_mgmt_idx]:
            st.header(translate("User Management", st.session_state.language))

            with st.expander(translate("Registered Users", st.session_state.language), expanded=False):
                if st.button(translate("Fetch User List", st.session_state.language)):
                    try:
                        res = requests.get(f"{API_URL}/admin/list-users")
                        if res.status_code == 200:
                            users = res.json()
                            if users:
                                df_users = pd.DataFrame(users)
                                st.dataframe(df_users)
                            else:
                                st.info(translate("No users found.", st.session_state.language))
                        else:
                            st.error(translate("Failed to fetch user list.", st.session_state.language))
                    except Exception as e:
                        st.error(translate("Error fetching user list:", st.session_state.language) + f" {e}")

            st.markdown("### " + translate("All User Chat History", st.session_state.language))
            try:
                res = requests.get(f"{API_URL}/admin/chat-history", headers=_auth_headers())
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        df = pd.DataFrame(data)
                        columns = ["email", "query", "response", "feedback", "timestamp"]
                        df_show = df[[c for c in columns if c in df.columns]]
                        df_show = localize_dataframe_content(df_show, st.session_state.language,
                                                             ["query", "response", "feedback"])
                        if st.session_state.language == "Hindi":
                            col_map = {
                                "email": "ईमेल",
                                "query": "प्रश्न",
                                "response": "उत्तर",
                                "feedback": "प्रतिक्रिया",
                                "timestamp": "समय"
                            }
                            df_show.columns = [col_map.get(c, c) for c in df_show.columns]
                        st.dataframe(df_show)
                    else:
                        st.info(translate("No chat history found.", st.session_state.language))
                else:
                    st.warning(translate("Failed to load chat history.", st.session_state.language))
            except Exception as e:
                st.error(translate("Error loading chat history:", st.session_state.language) + f" {e}")

        # --- System Tab ---
        with tabs[system_idx]:
            st.header(translate("System", st.session_state.language))
            st.subheader(translate("Knowledge Base Maintenance", st.session_state.language))
            st.write(translate("Use these admin tools to safeguard or restore the original knowledge base.",
                               st.session_state.language))

            c1, c2 = st.columns(2)
            headers = _auth_headers()

            with c1:
                if st.button("🗄️ " + translate("Backup Current KB", st.session_state.language)):
                    try:
                        r = requests.post(f"{API_URL}/kb/backup-original", headers=headers, timeout=10)
                        if r.status_code == 200:
                            st.success(translate("Backup created successfully.", st.session_state.language))
                        else:
                            st.error(translate("Failed to create backup.", st.session_state.language)
                                     + f" (HTTP {r.status_code})")
                    except Exception as e:
                        st.error(translate("Error while creating backup:", st.session_state.language) + f" {e}")

            with c2:
                if st.button("♻️ " + translate("Restore Original KB", st.session_state.language)):
                    confirm = st.checkbox(translate("Confirm restore (overwrites current KB)",
                                                    st.session_state.language), key="confirm_restore_kb")
                    if not confirm:
                        st.warning(translate("Please tick the confirmation checkbox to proceed with restore.",
                                             st.session_state.language))
                    else:
                        try:
                            r = requests.post(f"{API_URL}/kb/restore-original", headers=headers, timeout=15)
                            if r.status_code == 200:
                                st.success(translate("Knowledge base restored from original backup.",
                                                     st.session_state.language))
                                st.info(translate("You may need to refresh the page to see updated entries.",
                                                  st.session_state.language))
                            else:
                                st.error(translate("Failed to restore knowledge base.",
                                                   st.session_state.language) + f" (HTTP {r.status_code})")
                        except Exception as e:
                            st.error(translate("Error while restoring knowledge base:",
                                               st.session_state.language) + f" {e}")

            st.markdown("---")
            st.caption(translate("System utilities and future environment health checks will appear here.",
                                 st.session_state.language))
