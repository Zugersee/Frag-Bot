import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import time

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Berti", page_icon="🎓", layout="centered")
st.title("🎓 Frag Berti")

# --- 2. API KEY ---
# Stelle sicher, dass GOOGLE_API_KEY in deiner secrets.toml existiert
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("API Key fehlt! Bitte in `secrets.toml` hinterlegen.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. PERSÖNLICHKEIT (SYSTEM PROMPT) ---
# **WICHTIG:** Die Definition muss VOR dem Session State Block stehen, der sie verwendet!
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

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. Welches Thema interessiert dich? Tiere, Ritter oder Weltraum?"}
    ]
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

if "chat" not in st.session_state:
    # Initialisiere den Chat-Client mit dem System-Prompt
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Erstelle ein neues Chat-Objekt
        st.session_state.chat = model.start_chat()
        
        # Füge den System-Prompt als erste unsichtbare Nachricht hinzu
        st.session_state.chat.history.append({"role": "system", "parts": system_prompt})
        
        # Füge die Begrüßung des Modells in die Historie (für das UI) ein
        st.session_state.chat.history.append(st.session_state.messages[0])
        
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Modells/Chats: {e}")
        st.stop()


# --- 5. HILFSFUNKTIONEN ---

def text_to_audio(text):
    """Konvertiert Text in eine abspielbare MP3-Datei (Bytes)."""
    try:
        # Erstelle das gTTS-Objekt. Wichtig: Sprache auf Deutsch einstellen!
        tts = gTTS(text=text, lang='de')
        
        # Speichere die Audio-Daten in einem In-Memory-Byte-Stream (io.BytesIO)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception as e:
        st.error(f"Fehler bei der Audio-Generierung (gTTS): {e}")
        return None

def reset_audio():
    """Setzt den Audio-Key zurück, um Fehler im Streamlit-Player zu beheben."""
    st.session_state.audio_key += 1
    st.success("Audio-Player wurde zurückgesetzt.")


# --- 6. CHAT ANZEIGEN ---
# Zeige nur die sichtbaren Nachrichten (ab Index 1, da Index 0 die Begrüßung ist)
for msg in st.session_state.messages:
    # Der System-Prompt wird nicht im UI angezeigt, da er nur für das Modell ist.
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["parts"])

# AUDIO PLAYER (AUTOPLAY)
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True, key=f"audio_{st.session_state.audio_key}")
    st.caption("🔊 Falls du nichts hörst, tippe oben auf Play ▶️")
    st.session_state.autoplay_audio = None

st.markdown("---")


# --- 7. EINGABE BEREICH ---

# A) RESET BUTTON
col1, col2 = st.columns([3, 1])
with col2: # Der Reset-Knopf kommt in die schmalere Spalte
    st.button("Audio Reset 🔄", on_click=reset_audio)

# B) CHAT EINGABE UND LOGIK
prompt = st.chat_input("Deine Frage an Berti...")

if prompt:
    # 1. Benutzer-Nachricht hinzufügen und anzeigen
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Spinner anzeigen, während Gemini antwortet
    with st.chat_message("model"):
        with st.spinner("Berti denkt nach..."):
            try:
                # 3. Gemini aufrufen
                response = st.session_state.chat.send_message(prompt)
                
                model_response_text = response.text
                
                # 4. Antwort zur Session State und UI hinzufügen
                st.session_state.messages.append({"role": "model", "parts": model_response_text})
                st.markdown(model_response_text)
                
                # 5. Text in Audio umwandeln
                audio_bytes = text_to_audio(model_response_text)
                
                if audio_bytes:
                    # 6. Audio für Autoplay speichern
                    st.session_state.autoplay_audio = audio_bytes
                    
            except Exception as e:
                st.error(f"Fehler bei der Gemini-Antwort: {e}")
                
    # Wichtig: Streamlit neu ausführen, um das neue Audio-Element zu laden und abzuspielen
    st.rerun()
