import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# --- 1. SEITEN KONFIGURATION ---
st.set_page_config(
    page_title="Berti der Wissens-Bot",
    page_icon="🎓",
    layout="centered"
)

# --- 2. API KEY PRÜFUNG ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Achtung: Der Google API Key fehlt noch in den Streamlit Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. DAS GEHIRN ---
try:
    # Wir bleiben bei 2.0-flash, das ist schnell und klug
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Fehler beim Starten des Modells: {e}")

# --- 4. BERTIS PERSÖNLICHKEIT (SOKRATES-MODUS) ---
system_prompt = """
Du bist "Berti", ein geduldiger, kluger und freundlicher Mentor für ein 6-jähriges Kind.
Dein Ziel: Das Kind beim Lernen begleiten und echtes Sachwissen vermitteln.

DEINE REGELN FÜR DEN DIALOG:
1. TONALITÄT: Ruhig, freundlich, wertschätzend. KEINE albernen Geräusche.
2. METHODE (SOKRATES): Gib nicht sofort die komplette Lösung vor. Stelle vereinfachende Gegenfragen.
3. SCHRITT-FÜR-SCHRITT: Zerlege komplexe Probleme.
4. FAKTEN: Konzentriere dich auf echtes Sachwissen (Natur, Technik, Geschichte).
5. KONTINUITÄT: Beende deine Antwort IMMER mit einer Frage, damit der Dialog weitergeht.

Sprache: Einfaches, klares Deutsch. Kurze Sätze.
"""

# --- 5. APP OBERFLÄCHE ---
st.title("🎓 Frag Berti")
st.write("Hallo! Ich bin Berti. Lass uns gemeinsam etwas Neues lernen.")

# Chat-Verlauf initialisieren
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin bereit. Welches Thema interessiert dich heute? Tiere, Sterne oder vielleicht Ritter?"}
    ]
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])

st.markdown("---")
st.caption("Drücke auf das Mikrofon, um zu antworten. Für eine **neue** Antwort, nimm einfach nochmal auf!")

# --- 6. NUR AUDIO EINGABE ---
audio_value = st.audio_input("Sprich jetzt mit Berti:")

# --- 7. VERARBEITUNG ---
if audio_value:
    # Prüfen, ob es wirklich eine NEUE Aufnahme ist (Loop-Schutz)
    if audio_value != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_value

        # A) Nutzer-Audio anzeigen
        with st.chat_message("user"):
            st.write("🎤 *(Audio gesendet)*")
        st.session_state.messages.append({"role": "user", "parts": "🎤 *(Audio)*"})

        # B) Kontext holen (Berti muss wissen, was er selbst zuletzt gefragt hat)
        last_bot_response = ""
        if len(st.session_state.messages) > 1:
            for msg in reversed(st.session_state.messages[:-1]):
                if msg["role"] == "model":
                    last_bot_response = msg["parts"]
                    break
        
        # C) Nachdenken & Antworten
        with st.spinner('Berti hört zu und denkt nach...'):
            try:
                # Prompt bauen
                prompt_content = [
                    system_prompt,
                    f"Kontext (Deine letzte Frage war): {last_bot_response}",
                    "Führe den Dialog weiter. Antworte auf dieses Audio:",
                    {"mime_type": "audio/mp3", "data": audio_value.getvalue()}
                ]

                response = model.generate_content(prompt_content)
                bot_text = response.text

                # D) Antwort anzeigen
                with st.chat_message("model"):
                    st.markdown(bot_text)
                st.session_state.messages.append({"role": "model", "parts": bot_text})
                
                # E) Sprechen (TTS)
                tts = gTTS(text=bot_text, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_bytes = audio_fp.getvalue()
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)

            except Exception as e:
                st.error(f"Ein kleiner Fehler ist aufgetreten: {str(e)}")

# Reset Button
with st.sidebar:
    if st.button("Neues Thema starten 🔄"):
        st.session_state.messages = []
        st.session_state.last_audio_id = None
        st.rerun()
