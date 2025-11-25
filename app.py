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
if "autoplay_audio" not in st.session_state:
    st.session_state.autoplay_audio = None

# --- 4. MODELL ---
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Fehler: {e}")

# --- 5. PÄDAGOGISCHES PROFIL (FORSCHER-MODUS) ---
system_prompt = """
Du bist "Berti", ein Forschungs-Begleiter für ein 6-jähriges Kind.
DEIN ZIEL: Ermöglichungsdidaktik & Konstruktivismus. Du lieferst keine fertigen Antworten, sondern regst das eigene Denken an.

REGELN:
1. **EMOJIS:** Im Text darfst du sparsam Emojis nutzen (zur Auflockerung).
2. **KEINE BEGRÜSSUNG:** Steige direkt in das Thema ein.
3. **SPRACHE:** Einfach, klar, duzt das Kind.

DER PÄDAGOGISCHE ABLAUF:

SZENARIO A: Das Kind stellt eine NEUE FRAGE oder eine HYPOTHESE.
-> **AKTION:** Gib KEINE Erklärung. Validiere die Frage ("Spannende Idee!").
-> **FORSCHERFRAGE:** Stelle eine Frage zurück, die das Kind auf die Lösung bringt. Nutze Analogien aus dem Kinderalltag.
   *Beispiel:* Kind: "Warum schwimmt das Schiff?" -> Berti: "Gute Frage! Hast du mal versucht, einen schweren Stein und einen großen Ball ins Wasser zu legen? Was passiert da?"

SZENARIO B: Das Kind antwortet/rät oder löst das Rätsel.
-> **AKTION:** Lob den Denkprozess!
-> **WISSEN:** Jetzt darfst du das Fachwissen kurz auflösen (max. 3 Sätze). Fachbegriffe **fett**.
-> **TRANSFER:** Stelle eine neue Frage, die das Wissen erweitert.

SZENARIO C: Geschichten & Witze
-> Geschichten: Der Held (Kind) löst Probleme durch Nachdenken & Empathie. Ende mit Reflexionsfrage: "Was hättest du getan?"
"""

# --- 6. HILFSFUNKTIONEN ---

def clean_text_for_audio(text):
    """
    Entfernt Emojis und Markdown für eine saubere Sprachausgabe.
    """
    # 1. Entferne Markdown (*, #, _)
    text = text.replace("*", "").replace("#", "").replace("_", "")
    
    # 2. Entferne Emojis (Regex behält nur Buchstaben, Zahlen & Satzzeichen)
    # Erlaubt: Wortzeichen, Leerzeichen, Satzzeichen (. , ? ! : ; -) und deutsche Umlaute
    text = re.sub(r'[^\w\s,?.!äöüÄÖÜß:;–-]', '', text)
    
    return text.strip()

# --- 7. UI-LAYOUT (BUTTONS OBEN) ---

st.title("🎓 Frag Berti")

# Die Buttons ganz oben, damit sie immer sichtbar sind
col1, col2, col3 = st.columns(3)
trigger_witz = col1.button("🤣 Witz", use_container_width=True)
trigger_fakt = col2.button("🦁 Forschertipp", use_container_width=True)
trigger_geschichte = col3.button("🦸 Geschichte", use_container_width=True)

st.markdown("---")

# --- 8. CHAT VERLAUF ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 9. AUDIO PLAYER (BUG FIX) ---
# Wir spielen Audio NUR ab, wenn es Daten gibt UND wir gerade NICHT aufnehmen.
# Das 'autoplay=True' sorgt für sofortiges Abspielen.
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True)
    # WICHTIG: Sofort leeren, damit es beim nächsten Klick (z.B. auf Mikrofon) nicht nochmal spielt
    st.session_state.autoplay_audio = None 

# --- 10. EINGABE BEREICH ---

# Kleiner Abstand
st.write("") 
st.write("### 🎙️ Deine Forschungs-Frage:")

# A) AUDIO EINGABE
# Der Key sorgt dafür, dass das Widget resettet wird nach der Verarbeitung
audio_value = st.audio_input("Aufnahme starten:", key=f"rec_{st.session_state.audio_key}")

# B) TEXT EINGABE (Fallback)
text_input = st.chat_input("Oder schreibe hier...")

# --- 11. VERARBEITUNGSLOGIK ---

user_content = None
content_type = None 
prompt_instruction = ""

# Prioritäten prüfen
if trigger_witz:
    user_content = "Erzähle mir einen Witz, aber lass mich erst raten wie er ausgeht."
    content_type = "text"
elif trigger_fakt:
    user_content = "Nenne mir ein Natur-Phänomen. Erkläre es NICHT. Frage mich stattdessen, wie das wohl funktioniert."
    content_type = "text"
elif trigger_geschichte:
    user_content = "Erzähle eine Geschichte über ein Kind, das ein Problem durch Empathie löst. Frage mich am Ende, was ich getan hätte."
    content_type = "text"
elif audio_value:
    user_content = audio_value
    content_type = "audio"
elif text_input:
    user_content = text_input
    content_type = "text"

if user_content:
    
    # Bug-Fix Vorsichtsmaßnahme:
    # Wenn wir neuen Content verarbeiten, sicherstellen, dass altes Audio weg ist.
    st.session_state.autoplay_audio = None

    # 1. UI Update (User Message anzeigen)
    with st.chat_message("user"):
        if content_type == "audio":
            st.write("🎤 *(Sprachnachricht)*")
            user_msg_log = "🎤 *(Sprachnachricht)*"
            user_data_part = {"mime_type": "audio/wav", "data": user_content.getvalue()}
            prompt_instruction = "Höre dir das Kind genau an. Antworte pädagogisch (Szenario A oder B):"
        else:
            st.markdown(user_content)
            user_msg_log = user_content
            user_data_part = user_content
            prompt_instruction = "Antworte auf diesen Text:"

    st.session_state.messages.append({"role": "user", "parts": user_msg_log})

    # 2. Kontext holen
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
                f"KONTEXT (Deine letzte Aussage war): {last_bot_response}.",
                prompt_instruction,
                user_data_part
            ]

            response = model.generate_content(prompt_content)
            
            if response:
                bot_text = response.text
                
                # Text anzeigen
                st.session_state.messages.append({"role": "model", "parts": bot_text})
                # Kein st.markdown() hier nötig, der Rerun macht das gleich
                
                # 4. AUDIO BEREINIGEN & GENERIEREN
                clean_text = clean_text_for_audio(bot_text)
                
                tts = gTTS(text=clean_text, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                
                # Audio in Session State laden
                st.session_state.autoplay_audio = audio_fp.getvalue()
                
                # CRITICAL: Key erhöhen -> Das Audio-Input Widget wird komplett neu geladen
                # Das verhindert, dass die alte Aufnahme im Widget kleben bleibt.
                st.session_state.audio_key += 1
                
                st.rerun()

        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")
