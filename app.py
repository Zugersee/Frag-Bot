import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import re  # Für die Text-Reinigung (Regex)

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
        {"role": "model", "parts": "Hallo. Ich bin Berti. Ich bin gespannt, was wir heute erforschen. Hast du eine Frage oder eine Idee?"}
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

# --- 5. PÄDAGOGISCHES PROFIL (SOKRATISCH / ERMÖGLICHUNGSDIDAKTIK) ---
system_prompt = """
Du bist "Berti", ein Forschungs-Begleiter für ein 6-jähriges Kind.
DEIN ZIEL: Ermöglichungsdidaktik. Du lieferst keine fertigen Antworten, sondern regst das eigene Denken an (Hebammenkunst/Mäeutik).

STRIKTE REGELN:
1. **KEINE EMOJIS:** Nutze reinen Text. Keine Smileys.
2. **KEINE BEGRÜSSUNG:** Steige direkt in das Thema ein (außer beim allerersten Satz).
3. **SPRACHE:** Einfach, klar, aber fachlich korrekt. Du duzt das Kind.

DER PÄDAGOGISCHE ABLAUF (Dialogisches Lernen):

SZENARIO A: Das Kind stellt eine NEUE FRAGE (z.B. "Warum ist die Banane krumm?")
-> **ANTWORT:** Gib KEINE Erklärung. Gib nur einen winzigen Hinweis (Scaffolding).
-> **AKTION:** Stelle sofort eine **Forscherfrage**, die das Kind zur Hypothesenbildung anregt.
   *Beispiel:* "Das hat mit der Sonne zu tun. Was glaubst du, wo die Banane hin will, wenn sie wächst?"

SZENARIO B: Das Kind antwortet auf deine Frage oder rät.
-> **ANTWORT:** Würdige den Gedankengang (Validierung).
-> **WISSEN:** Jetzt darfst du das Fachwissen kindgerecht auflösen (max. 3 Sätze). Nutze Fachbegriffe fettgedruckt (z.B. **Licht**, **Schwerkraft**).
-> **TRANSFER:** Stelle eine abschließende Frage, die das Wissen auf etwas anderes überträgt oder zum Weiterdenken anregt (Future Skills / Kritisches Denken).
   *Beispiel:* "Genau! Sie wächst zum Licht. Wo hast du das schon mal bei Blumen gesehen?"

SZENARIO C: Geschichten & Witze
-> Bei Geschichten: Der Held löst Probleme durch Nachdenken und Empathie. Ende mit einer Reflexionsfrage: "Wie hättest du dich gefühlt?"
"""

# --- 6. HILFSFUNKTIONEN ---

def clean_text_for_audio(text):
    """
    Entfernt Emojis, Markdown (*, #) und ungewollte Zeichen, 
    damit die Audio-Ausgabe sauber und ruhig ist.
    """
    # 1. Entferne Markdown (Fettgedrucktes etc.)
    text = text.replace("*", "").replace("#", "").replace("_", "")
    
    # 2. Entferne Emojis (Alles was nicht Text oder Satzzeichen ist)
    # Dieser Regex behält Buchstaben (auch Umlaute), Zahlen und Satzzeichen.
    text = re.sub(r'[^\w\s,?.!äöüÄÖÜß:;–-]', '', text)
    
    return text.strip()

# --- 7. CHAT ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# AUDIO PLAYER (AUTOPLAY)
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True)
    st.caption("🔊 Berti spricht... (Play drücken zum Wiederholen)")
    st.session_state.autoplay_audio = None

st.markdown("---")

# --- 8. EINGABE BEREICH ---

# A) BUTTONS (Impulse)
col1, col2, col3 = st.columns(3)
trigger_witz = col1.button("Witz erzählen", use_container_width=True)
trigger_fakt = col2.button("Forschertipp", use_container_width=True) # Umbenannt für Forschermodus
trigger_geschichte = col3.button("Geschichte", use_container_width=True)

# B) AUDIO EINGABE
st.write("### 🎙️ Deine Forschungs-Frage:")
audio_value = st.audio_input("Aufnahme starten:", key=f"rec_{st.session_state.audio_key}")

# C) TEXT EINGABE
text_input = st.chat_input("Oder schreibe hier...")

# --- 9. LOGIK & VERARBEITUNG ---

user_content = None
content_type = None 
prompt_instruction = ""

# Trigger prüfen
if trigger_witz:
    user_content = "Erzähle mir einen Witz, aber lass mich erst raten wie er ausgeht."
    content_type = "text"
elif trigger_fakt:
    user_content = "Nenne mir ein Phänomen aus der Natur und frage mich, wie das wohl funktioniert."
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
    
    # 1. UI Update
    with st.chat_message("user"):
        if content_type == "audio":
            st.write("🎤 *(Sprachnachricht)*")
            user_msg_log = "🎤 *(Sprachnachricht)*"
            user_data_part = {"mime_type": "audio/wav", "data": user_content.getvalue()}
            prompt_instruction = "Antworte auf dieses Audio (Kind):"
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
                f"KONTEXT (Deine letzte Aussage war): {last_bot_response}. \nANALYSIERE: Ist das eine neue Frage (-> Szenario A) oder eine Antwort des Kindes (-> Szenario B)?",
                prompt_instruction,
                user_data_part
            ]

            response = model.generate_content(prompt_content)
            
            if response:
                bot_text = response.text
                
                # Text anzeigen
                st.session_state.messages.append({"role": "model", "parts": bot_text})
                # Wir machen hier keinen direkten write, der Rerun erledigt das sauber
                
                # 4. AUDIO BEREINIGEN & GENERIEREN
                clean_text = clean_text_for_audio(bot_text)
                
                tts = gTTS(text=clean_text, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                
                st.session_state.autoplay_audio = audio_fp.getvalue()
                
                # Reset Key für Audio Input
                st.session_state.audio_key += 1
                
                st.rerun()

        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")
