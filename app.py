import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Berti", page_icon="🎓", layout="centered")
st.title("🎓 Frag Berti")

# --- 2. API KEY ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("API Key fehlt! Bitte in `secrets.toml` hinterlegen.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 3. PERSÖNLICHKEIT ---
system_prompt = """
Du bist "Berti", ein freundlicher Roboter-Freund für ein 6-jähriges Kind.
Du bist geduldig, lustig und schlau. Du duzt das Kind.

DEINE 4 MODI:
1. **WISSEN (Standard):** Erkläre kurz (max 3 Sätze). Nutze Vergleiche. Stelle eine Impulsfrage.
2. **FUN FACTS:** Unglaubliches Wissen (Tiere, Rekorde).
3. **WITZE:** Kindgerechte Witze.
4. **GESCHICHTEN:** Kurze Story über ein Superhelden-Kind, das Probleme mit **Empathie & Hilfsbereitschaft** löst (nicht mit Gewalt). Ende mit einer Reflexionsfrage ("Was hättest du getan?").

FORMAT: Nutze **fette Schrift** für wichtige Wörter. Sei herzlich.
"""

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! 👋 Ich bin Berti. Du kannst mir schreiben oder einfach mit mir sprechen! Drücke auf das Mikrofon. 🎙️"}
    ]
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

# Chat initialisieren
if "chat" not in st.session_state:
    try:
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_prompt
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"Start-Fehler: {e}")
        st.stop()

# --- 5. HILFSFUNKTIONEN ---

def text_to_audio(text):
    """Macht aus Text -> Sprache (MP3)"""
    try:
        tts = gTTS(text=text, lang='de')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception:
        return None

def transcribe_audio(audio_bytes):
    """Nutzt Gemini, um das Audio des Kindes in Text umzuwandeln (Speech-to-Text)"""
    try:
        # Wir nutzen ein separates Modell-Objekt nur für die Transkription
        transcribe_model = genai.GenerativeModel("gemini-2.0-flash")
        response = transcribe_model.generate_content([
            "Höre dir dieses Audio an. Schreibe exakt auf, was das Kind gesagt hat (auf Deutsch). Antworte NUR mit dem Text, keine Kommentare.",
            {"mime_type": "audio/wav", "data": audio_bytes}
        ])
        return response.text
    except Exception as e:
        st.error(f"Konnte Audio nicht verstehen: {e}")
        return None

def verarbeite_nachricht(benutzer_text):
    """Zentrale Logik: Text -> AI -> Audio"""
    
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "parts": benutzer_text})
    
    # 2. AI Antwort generieren
    try:
        with st.spinner("Berti hört zu und überlegt..."):
            response = st.session_state.chat.send_message(benutzer_text)
            text = response.text
            
            # 3. Speichern
            st.session_state.messages.append({"role": "model", "parts": text})
            
            # 4. Audio generieren
            audio = text_to_audio(text)
            if audio:
                st.session_state.autoplay_audio = audio
            
    except Exception as e:
        st.error("Hoppla, Berti hat den Faden verloren. Probier es nochmal!")

# --- 6. CHAT VERLAUF ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 7. AUDIO AUSGABE (MIT WIEDERHOLUNG) ---
# Wir zeigen den Audio-Player IMMER an, wenn Audio da ist.
# Durch 'autoplay=True' startet es sofort.
# Das Kind kann einfach nochmal auf den "Play"-Knopf im Player drücken, um es zu wiederholen.
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True, key=f"audio_{st.session_state.audio_key}")
    # Wir inkrementieren den Key, damit beim nächsten Mal ein frischer Player kommt
    st.session_state.audio_key += 1 
    st.session_state.autoplay_audio = None # Reset, damit es nicht bei jedem Klick neu lädt, aber der Player bleibt sichtbar in der History ist schwierig, daher Player oben.

st.markdown("---")

# --- 8. EINGABE BEREICH (BUTTONS & MIKROFON) ---

st.write("### 1. Wähle ein Thema:")
col1, col2, col3 = st.columns(3)

# Buttons
if col1.button("🤣 Witz", use_container_width=True):
    verarbeite_nachricht("Erzähle mir einen Witz!")
    st.rerun()

if col2.button("🦁 Fakt", use_container_width=True):
    verarbeite_nachricht("Erzähle mir einen Fun Fact!")
    st.rerun()

if col3.button("🦸 Geschichte", use_container_width=True):
    verarbeite_nachricht("Erzähle mir eine Superhelden-Geschichte über Empathie.")
    st.rerun()

st.write("### 2. Oder sprich mit Berti:")

# A) AUDIO EINGABE (Das neue Feature!)
audio_value = st.audio_input("Drücke auf das Mikrofon 🎙️", key="recorder")

if audio_value:
    # Wir prüfen, ob wir dieses Audio schon verarbeitet haben, um Schleifen zu verhindern
    if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != audio_value:
        st.session_state.last_audio_id = audio_value
        
        # Audio Bytes holen
        audio_bytes = audio_value.getvalue()
        
        # Audio in Text umwandeln (Transkription)
        transcribed_text = transcribe_audio(audio_bytes)
        
        if transcribed_text:
            # Den Text an Berti senden
            verarbeite_nachricht(transcribed_text)
            st.rerun()

# B) TEXT EINGABE (Fallback)
text_input = st.chat_input("Oder tippe hier...")
if text_input:
    verarbeite_nachricht(text_input)
    st.rerun()
