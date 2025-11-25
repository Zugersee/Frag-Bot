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

# --- 3. SESSION STATE (GEDÄCHTNIS) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. Welches Thema interessiert dich? Tiere, Ritter oder Weltraum?"}
    ]
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

# --- 4. MODELL (GEHIRN) ---
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Fehler: {e}")

# --- 5. PERSÖNLICHKEIT ---
system_prompt = """
Du bist "Berti", ein Mentor für ein 6-jähriges Kind.
DEINE REGELN:

1. KEINE BEGRÜSSUNG: Sag NIEMALS "Hallo", "Guten Tag" oder ähnliches am Anfang. Starte DIREKT mit dem Inhalt.
2. KEINE FLOSKELN: Vermeide Sätze wie "Das ist eine tolle Frage" oder "Sehr gut beobachtet". Das macht den Dialog zu langsam.
3. STRUKTUR (WISSEN + FRAGE):
   - Bestätige kurz die Aussage des Kindes.
   - Liefere SOFORT passendes Fachwissen oder einen Fachbegriff (kindgerecht erklärt). Warte damit nicht.
   - Beende den Satz mit einer gezielten Frage, die das Wissen vertieft.
4. TONALITÄT: Freundlich, aber sachbezogen und zügig.
"""

# --- 6. CHAT ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mp3', autoplay=True)
    st.session_state.autoplay_audio = None

st.markdown("---")
st.caption("Sprich jetzt deine Antwort ein:")

# --- 7. AUDIO EINGABE ---
audio_value = st.audio_input("Aufnahme:", key=f"rec_{st.session_state.audio_key}")

if audio_value:
    with st.chat_message("user"):
        st.write("🎤 *(Audio gesendet)*")
    st.session_state.messages.append({"role": "user", "parts": "🎤 *(Audio)*"})

    last_bot_response = ""
    if len(st.session_state.messages) > 1:
        for msg in reversed(st.session_state.messages[:-1]):
            if msg["role"] == "model":
                last_bot_response = msg["parts"]
                break

    with st.spinner('Berti hört zu...'):
        try:
            prompt_content = [
                system_prompt,
                f"Kontext (Deine letzte Aussage war): {last_bot_response}",
                "Führe den Dialog zügig weiter. Antworte auf dieses Audio:",
                {"mime_type": "audio/mp3", "data": audio_value.getvalue()}
            ]

            response = None
            for attempt in range(3):
                try:
                    response = model.generate_content(prompt_content)
                    break
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(2)
                        continue
                    else:
                        raise e

            if response:
                bot_text = response.text
                st.session_state.messages.append({"role": "model", "parts": bot_text})
                
                tts = gTTS(text=bot_text, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.session_state.autoplay_audio = audio_fp.getvalue()
                
                st.session_state.audio_key += 1
                st.rerun()

        except Exception as e:
            st.error(f"Fehler: {e}")
