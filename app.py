import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import re

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Berti", page_icon="🎓", layout="centered")

# --- 2. API KEY ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("API Key fehlt! Bitte in `secrets.toml` hinterlegen.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. Ich bin gespannt, was wir heute erforschen. Hast du eine Frage oder eine Idee?"}
    ]
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0

# WICHTIG: Wir trennen jetzt Daten und Autoplay-Status
if "last_audio_data" not in st.session_state:
    st.session_state.last_audio_data = None
if "trigger_autoplay" not in st.session_state:
    st.session_state.trigger_autoplay = False

# --- 4. MODELL ---
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Fehler: {e}")

# --- 5. PÄDAGOGISCHES PROFIL ---
system_prompt = """
Du bist "Berti", ein Forschungs-Begleiter für ein 6-jähriges Kind.
DEIN ZIEL: Ermöglichungsdidaktik & Konstruktivismus.

REGELN:
1. **EMOJIS:** Im Text erlaubt.
2. **KEINE BEGRÜSSUNG:** Direkt zum Thema.
3. **SPRACHE:** Einfach, klar, duzt das Kind.

ABLAUF:
SZENARIO A (Neue Frage): Keine Erklärung! Gib einen Hinweis + Forscherfrage.
SZENARIO B (Antwort Kind): Loben + kurzes Wissen + Transferfrage.
SZENARIO C (Geschichten): Held löst Problem durch Empathie.
"""

# --- 6. HILFSFUNKTIONEN ---
def clean_text_for_audio(text):
    text = text.replace("*", "").replace("#", "").replace("_", "")
    text = re.sub(r'[^\w\s,?.!äöüÄÖÜß:;–-]', '', text)
    return text.strip()

# --- 7. UI-LAYOUT (BUTTONS OBEN) ---
st.title("🎓 Frag Berti")

col1, col2, col3 = st.columns(3)
trigger_witz = col1.button("🤣 Witz", use_container_width=True)
trigger_fakt = col2.button("🦁 Forschertipp", use_container_width=True)
trigger_geschichte = col3.button("🦸 Geschichte", use_container_width=True)

st.markdown("---")

# --- 8. CHAT VERLAUF ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 9. AUDIO PLAYER (BUG FIXED) ---
# Hier ist der Trick: Wir schauen auf die Flagge 'trigger_autoplay'.
# Nur wenn die wahr ist, starten wir automatisch. Sonst zeigen wir den Player nur an (stumm).

if st.session_state.last_audio_data:
    should_play = st.session_state.trigger_autoplay
    
    st.audio(
        st.session_state.last_audio_data, 
        format='audio/mpeg', 
        autoplay=should_play
    )
    
    # WICHTIG: Sofort den Autoplay-Schalter für die Zukunft ausschalten!
    # Das Audio bleibt da (Daten), aber beim nächsten Klick (Record) bleibt es stumm.
    st.session_state.trigger_autoplay = False


# --- 10. EINGABE BEREICH ---
st.write("") 
st.write("### 🎙️ Deine Forschungs-Frage:")

# A) AUDIO EINGABE
audio_value = st.audio_input("Aufnahme starten:", key=f"rec_{st.session_state.audio_key}")

# B) TEXT EINGABE
text_input = st.chat_input("Oder schreibe hier...")

# --- 11. VERARBEITUNG ---
user_content = None
content_type = None 
prompt_instruction = ""

if trigger_witz:
    user_content = "Erzähle mir einen Witz, lass mich raten."
    content_type = "text"
elif trigger_fakt:
    user_content = "Nenne ein Natur-Phänomen. Frage mich, wie es funktioniert."
    content_type = "text"
elif trigger_geschichte:
    user_content = "Geschichte über Empathie. Frage mich am Ende was ich getan hätte."
    content_type = "text"
elif audio_value:
    user_content = audio_value
    content_type = "audio"
elif text_input:
    user_content = text_input
    content_type = "text"

if user_content:
    # 1. UI Update
    with st.chat_message("user"):
        if content_type == "audio":
            st.write("🎤 *(Sprachnachricht)*")
            user_msg_log = "🎤 *(Sprachnachricht)*"
            user_data_part = {"mime_type": "audio/wav", "data": user_content.getvalue()}
            prompt_instruction = "Höre dir das Kind an. Antworte pädagogisch:"
        else:
            st.markdown(user_content)
            user_msg_log = user_content
            user_data_part = user_content
            prompt_instruction = "Antworte auf diesen Text:"

    st.session_state.messages.append({"role": "user", "parts": user_msg_log})

    # 2. Kontext
    last_bot_response = ""
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "model":
            last_bot_response = msg["parts"]
            break

    # 3. KI Generierung
    with st.spinner('Berti überlegt...'):
        try:
            prompt_content = [
                system_prompt,
                f"KONTEXT: {last_bot_response}.",
                prompt_instruction,
                user_data_part
            ]

            response = model.generate_content(prompt_content)
            
            if response:
                bot_text = response.text
                st.session_state.messages.append({"role": "model", "parts": bot_text})
                
                # 4. AUDIO GENERIEREN
                clean_text = clean_text_for_audio(bot_text)
                tts = gTTS(text=clean_text, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                
                # Speichern der DATEN
                st.session_state.last_audio_data = audio_fp.getvalue()
                # Setzen des SCHALTERS auf AN (nur für jetzt!)
                st.session_state.trigger_autoplay = True
                
                # Reset Input Widget
                st.session_state.audio_key += 1
                
                st.rerun()

        except Exception as e:
            st.error(f"Fehler: {e}")
