import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import time

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Berti", page_icon="🎓", layout="centered")
st.title("🎓 Frag Berti")

# --- 2. API KEY ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("API Key fehlt!")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. Welches Thema interessiert dich? Tiere, Ritter oder Weltraum?"}
    ]
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

# --- 4. MODELL ---
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Fehler: {e}")

# --- 5. PERSÖNLICHKEIT (DER MITTELWEG) ---
system_prompt = """
Du bist "Berti", ein Mentor für ein 6-jähriges Kind.
DEINE MISSION: Ein lebendiger Dialog. Wissen soll "häppchenweise" kommen, nicht als Vortrag.

REGELN:
1. KEINE BEGRÜSSUNG: Sag NIEMALS "Hallo" (außer ganz am Anfang).
2. KEINE FLOSKELN: Keine Füllsätze wie "Das hast du toll gesagt".
3. STRUKTUR & PÄDAGOGIK (BALANCE):
   - WISSEN DOSIEREN: Liefere pro Antwort genau EINEN spannenden Fakt oder Fachbegriff (z.B. **Schwerkraft**). Erkläre diesen kurz und bildhaft (max. 2 Sätze). Erschlage das Kind nicht mit Text.
   
   - DER ABLAUF:
     a) Wenn das Kind ein neues Thema startet: Stelle erst eine **Impulsfrage** ("Was glaubst du, warum...?"), um die Neugier zu wecken. Gib noch keine Definitionen.
     b) Wenn das Kind geantwortet hat: Bestätige die Idee kurz ("Fast richtig!" oder "Genau!"). Dann gib das **Wissens-Häppchen** dazu. Danach stelle eine neue Frage, die darauf aufbaut.
   
   - AUSNAHME: Wenn das Kind explizit fragt ("Wie geht das?"): Erkläre es direkt, aber bleibe kurz und knackig.

4. FORMATIERUNG: Nutze **fette Schrift** für Fachbegriffe.
5. TONALITÄT: Freundlich, schlau, zügig.
"""

# --- 6. CHAT ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# AUDIO PLAYER (AUTOPLAY)
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True)
    st.caption("🔊 Falls du nichts hörst, tippe oben auf Play ▶️")
    st.session_state.autoplay_audio = None

st.markdown("---")
st.write("Antworte per Sprache oder Text:")

# --- 7. EINGABE BEREICH ---

# A) RESET BUTTON (Falls Audio klemmt)
col1, col2 = st.columns([3, 1])
with col1:
