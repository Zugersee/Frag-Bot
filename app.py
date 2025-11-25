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
    st.error("API Key fehlt! Bitte in `secrets.toml` hinterlegen.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. PERSÖNLICHKEIT (SYSTEM PROMPT) ---
system_prompt = """
Du bist "Berti", ein freundlicher Mentor für ein 6-jähriges Kind.
DEINE MISSION: Ein lebendiger Dialog. Wissen soll "häppchenweise" kommen.

REGELN:
1. KORREKTUR: Wenn das Kind "Hallo" sagt, darfst du auch "Hallo" sagen. Sonst keine Begrüßung.
2. KEINE FLOSKELN: Keine Füllsätze wie "Das hast du toll gesagt".
3. STRUKTUR & PÄDAGOGIK:
   - Liefere pro Antwort genau EINEN spannenden Fakt oder Fachbegriff (z.B. **Schwerkraft**).
   - Erkläre diesen kurz und bildhaft (max. 2 Sätze).
   - ABLAUF:
     a) Neues Thema: Stelle erst eine **Impulsfrage** ("Was glaubst du, warum...?").
     b) Antwort erhalten: Bestätige kurz ("Genau!"), gib dann das **Wissens-Häppchen**, dann stelle eine neue Frage.
     c) Frage "Wie geht das?": Erkläre es direkt, kurz und knackig.

4. FORMATIERUNG: Nutze **fette Schrift** für Fachbegriffe.
5. TONALITÄT: Freundlich, schlau, zügig, duzt das Kind.
"""

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    # Start-Nachricht nur für die Anzeige (UI), nicht für das Modell-Gedächtnis zwingend nötig
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. 🤖 Welches Thema interessiert dich? Tiere 🦁, Ritter ⚔️ oder Weltraum 🚀?"}
    ]

if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

# Chat-Objekt initialisieren
if "chat" not in st.session_state:
    try:
        # HIER IST DIE VERBESSERUNG: system_instruction direkt im Konstruktor
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_prompt
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"Fehler beim Starten: {e}")
        st.stop()


# --- 5. HILFSFUNKTIONEN ---
def text_to_audio(text):
    """Konvertiert Text in MP3."""
    try:
        tts = gTTS(text=text, lang='de')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception as e:
        return None

def reset_audio():
    st.session_state.audio_key += 1

# --- 6. CHAT ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# AUDIO PLAYER (Unsichtbar abspielen)
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True, key=f"audio_{st.session_state.audio_key}")
    st.session_state.autoplay_audio = None

st.markdown("---")

# --- 7. EINGABE ---

# Kleiner Trick: Reset Button diskret unten rechts, falls Eltern helfen müssen
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("🔇 Reset", help="Klicken, falls Audio hängt", on_click=reset_audio):
        pass

prompt = st.chat_input("Schreibe hier deine Frage...")

if prompt:
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Berti antwortet
    with st.chat_message("model"):
        with st.spinner("Berti überlegt..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                text = response.text
                
                # UI Update
                st.session_state.messages.append({"role": "model", "parts": text})
                st.markdown(text)
                
                # Audio generieren
                audio = text_to_audio(text)
                if audio:
                    st.session_state.autoplay_audio = audio
                    
            except Exception as e:
                st.error("Oh, Berti ist kurz eingeschlafen. Versuch es nochmal!")
                
    st.rerun()
