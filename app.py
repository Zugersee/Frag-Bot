import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# --- 1. SEITEN KONFIGURATION ---
st.set_page_config(
    page_title="Berti der Roboter",
    page_icon="🤖",
    layout="centered"
)

# --- 2. API KEY SICHERHEITSPRÜFUNG ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Achtung: Der Google API Key fehlt noch in den Streamlit Secrets!")
    st.info("Gehe in Streamlit zu 'Settings' -> 'Secrets' und trage ihn ein.")
    st.stop()

# API konfigurieren
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. DAS GEHIRN (VERSIONS-FIX) ---
# WICHTIG: Hier nutzen wir 'gemini-2.0-flash' da dieser auf deiner Liste verfügbar war.
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Kritischer Fehler beim Starten des Modells: {e}")

# --- 4. BERTIS PERSÖNLICHKEIT (SYSTEM PROMPT) ---
system_prompt = """
Du bist "Berti", ein lustiger, kugelrunder Roboter-Freund für einen 6-jährigen Jungen.
Dein Ziel: Wissen vermitteln, Spaß haben und Neugier wecken.

DEINE REGELN:
1. TONALITÄT: Herzlich, witzig, du machst gerne mal kleine Quatsch-Geräusche (schreibe sie als Text: *Boing*, *Zisch*, *Ratter*).
2. SPRACHE: Nutze sehr einfaches Deutsch, kurze Hauptsätze. Keine schwierigen Fremdwörter.
3. LÄNGE: Halte dich kurz! Maximal 3-4 Sätze pro Antwort.
4. PÄDAGOGIK: Gib nicht immer sofort die Lösung vor. Hilf dem Kind, selbst darauf zu kommen.
5. INHALT: Du kennst dich super mit Tieren, Rittern, Weltraum und Mathe (Zahlen bis 20) aus.
6. GRENZEN: Du hast KEIN Internet für Live-Daten. Wenn er fragt "Wie ist das Wetter?", sag lustig: 
   "Ich wohne doch im Computer! Guck mal selbst raus!"
7. WITZE: Erzähle gerne kindgerechte Witze.

Du bist ein Freund, kein Lehrer. Sei begeistert!
"""

# --- 5. APP OBERFLÄCHE ---
st.title("🤖 Frag Berti!")
st.write("Hallo! Ich bin Berti. Klick unten auf das Mikrofon und frag mich was!")

# Chat-Verlauf initialisieren
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! *Zisch* Ich bin bereit! Was wollen wir entdecken?"}
    ]

# Den bisherigen Chat anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])

# --- 6. AUDIO EINGABE & VERARBEITUNG ---
audio_value = st.audio_input("Sprich mit Berti")

if audio_value:
    # A) Audio verarbeiten und anzeigen
    with st.chat_message("user"):
        st.write("🎤 *(Audio Nachricht gesendet)*")
    st.session_state.messages.append({"role": "user", "parts": "🎤 *(Audio Nachricht)*"})

    # B) Lade-Animation anzeigen
    with st.spinner('Berti denkt nach... *Ratter Ratter*'):
        try:
            # C) Anfrage an Gemini senden (Multimodal: Audio + Prompt)
            response = model.generate_content([
                system_prompt, 
                "Antworte dem Kind auf diese Audio-Aufnahme. Sei lustig!", 
                {"mime_type": "audio/mp3", "data": audio_value.getvalue()}
            ])
            
            bot_text = response.text

            # D) Antwort anzeigen
            with st.chat_message("model"):
                st.markdown(bot_text)
            
            # E) Text zu Audio umwandeln
            tts = gTTS(text=bot_text, lang='de')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            
            # WICHTIG: Datei-Zeiger zurücksetzen!
            audio_fp.seek(0)
            
            # F) Audio automatisch abspielen
            st.audio(audio_fp, format='audio/mp3', autoplay=True)

            # G) Antwort im Verlauf speichern
            st.session_state.messages.append({"role": "model", "parts": bot_text})

        except Exception as e:
            st.error(f"Oh nein, Berti hat einen Schluckauf! *Hicks* (Fehler: {str(e)})")

# Reset Button
with st.sidebar:
    if st.button("Neues Gespräch starten 🔄"):
        st.session_state.messages = []
        st.rerun()
