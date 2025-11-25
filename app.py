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

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! 👋 Ich bin Berti. Tippe auf die Knöpfe oder sprich mit mir ins Mikrofon! 🎙️"}
    ]
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

# --- 4. MODELL ---
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Fehler beim Starten: {e}")

# --- 5. PERSÖNLICHKEIT (SYSTEM PROMPT) ---
system_prompt = """
Du bist "Berti", ein freundlicher Roboter-Freund für ein 6-jähriges Kind.
Du bist geduldig, lustig und schlau. Du duzt das Kind.

DEINE 4 MODI (Je nach Frage des Kindes):

1. **WISSEN (Standard):** - Wenn das Kind etwas fragt: Antworte kurz (max 3 Sätze). 
   - Nutze einfache Vergleiche. 
   - Stelle am Ende eine Impulsfrage ("Hast du das schon mal gesehen?").

2. **FUN FACTS (Stichwort 'Fakt'):** - Erzähle einen unglaublichen Fakt (Tiere oder Rekorde).

3. **WITZE (Stichwort 'Witz'):** - Erzähle einen kurzen, harmlosen Kinderwitz.

4. **GESCHICHTEN (Stichwort 'Geschichte'):** - Erzähle eine KURZE Geschichte (max. 6 Sätze).
   - Held: Ein Kind mit Superkraft "Empathie/Hilfsbereitschaft".
   - Ende mit einer Reflexionsfrage ("Was hättest du getan?").

FORMAT: Nutze **fette Schrift** für wichtige Wörter. Sei herzlich.
"""

# --- 6. CHAT ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# AUDIO PLAYER (AUTOPLAY) - Deine Logik
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True)
    st.caption("🔊 Berti spricht... (Zum Wiederholen Play drücken)")
    st.session_state.autoplay_audio = None

st.markdown("---")

# --- 7. EINGABE BEREICH ---

# A) BUTTONS (Für Witz, Fakt, Geschichte)
col1, col2, col3 = st.columns(3)
trigger_witz = col1.button("🤣 Witz", use_container_width=True)
trigger_fakt = col2.button("🦁 Fakt", use_container_width=True)
trigger_geschichte = col3.button("🦸 Geschichte", use_container_width=True)

# B) AUDIO EINGABE (Dein Code: Mit dynamischem Key für Reset)
st.write("### Sprich mit Berti:")
audio_value = st.audio_input("Aufnahme:", key=f"rec_{st.session_state.audio_key}")

# C) TEXT EINGABE
text_input = st.chat_input("Oder schreibe hier...")

# --- 8. LOGIK & VERARBEITUNG ---

# Variablen für den Prompt vorbereiten
user_content = None
content_type = None # "audio" oder "text"
prompt_instruction = ""

# Prüfen, was ausgelöst wurde (Priorität: Buttons > Audio > Text)
if trigger_witz:
    user_content = "Erzähle mir einen lustigen Witz!"
    content_type = "text"
elif trigger_fakt:
    user_content = "Erzähle mir einen spannenden Fun Fact!"
    content_type = "text"
elif trigger_geschichte:
    user_content = "Erzähle mir eine Superhelden-Geschichte über Empathie."
    content_type = "text"
elif audio_value:
    user_content = audio_value
    content_type = "audio"
elif text_input:
    user_content = text_input
    content_type = "text"

# Wenn eine Eingabe da ist, ab an die KI
if user_content:
    
    # 1. UI Update (User Message anzeigen)
    with st.chat_message("user"):
        if content_type == "audio":
            st.write("🎤 *(Sprachnachricht gesendet)*")
            user_msg_log = "🎤 *(Sprachnachricht)*"
            # Audio-Daten für Gemini vorbereiten
            user_data_part = {"mime_type": "audio/wav", "data": user_content.getvalue()}
            prompt_instruction = "Antworte auf dieses Audio eines Kindes (Deutsch):"
        else:
            st.markdown(user_content)
            user_msg_log = user_content
            # Text-Daten für Gemini vorbereiten
            user_data_part = user_content
            prompt_instruction = "Antworte auf diesen Text:"

    st.session_state.messages.append({"role": "user", "parts": user_msg_log})

    # 2. Kontext holen (Was hat Berti zuletzt gesagt?)
    last_bot_response = ""
    # Wir suchen die letzte Antwort vom Model
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "model":
            last_bot_response = msg["parts"]
            break

    # 3. KI Generierung
    with st.spinner('Berti hört zu...'):
        try:
            # Wir bauen den Prompt jedes Mal frisch zusammen (Stateless ist robuster hier)
            prompt_content = [
                system_prompt,
                f"WICHTIG - Kontext (Deine letzte Aussage war): {last_bot_response}",
                prompt_instruction,
                user_data_part
            ]

            # Aufruf an Gemini
            response = model.generate_content(prompt_content)
            
            if response:
                bot_text = response.text
                
                # Antwort anzeigen
                st.session_state.messages.append({"role": "model", "parts": bot_text})
                # Wir machen kein st.markdown() hier, weil der Rerun das gleich erledigt
                
                # Audio generieren (TTS)
                # Sternchen entfernen, damit gTTS nicht "Sternchen" vorliest
                clean_text = bot_text.replace("*", "").replace("#", "")
                
                tts = gTTS(text=clean_text, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                
                # Audio in Session State laden
                st.session_state.autoplay_audio = audio_fp.getvalue()
                
                # CRITICAL STEP: Key erhöhen, damit Audio-Input resettet wird!
                st.session_state.audio_key += 1
                
                # Seite neu laden, damit Audio spielt und Mikrofon leer ist
                st.rerun()

        except Exception as e:
            st.error(f"Oh, Berti ist kurz eingeschlafen. Fehler: {e}")
