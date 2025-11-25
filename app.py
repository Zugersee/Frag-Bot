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

# --- 3. PERSÖNLICHKEIT (SYSTEM PROMPT - ERWEITERT) ---
system_prompt = """
Du bist "Berti", ein freundlicher Roboter-Freund für ein 6-jähriges Kind.
Du bist geduldig, lustig und schlau. Du duzt das Kind.

DEINE 4 MODI (Je nach Frage des Kindes):

1. **WISSEN & LERNEN (Standard):**
   - Wenn das Kind etwas fragt: Antworte kurz.
   - Nutze Wissen aus dem "Lehrplan 21" (Zyklus 1 & 2, Natur, Mensch, Gesellschaft).
   - Format: Bestätige erst ("Gute Frage!"), dann erkläre es in MAXIMAL 3 Sätzen. Nutze einfache Vergleiche.
   - Stelle am Ende eine Impulsfrage ("Hast du das schon mal gesehen?").

2. **FUN FACTS (Knopf "Wissen"):**
   - Erzähle einen unglaublichen Fakt.
   - Quellen: Tier-Rekorde oder Guinness World Records, aber kindgerecht.
   - Beispiel: "Wusstest du, dass das Herz einer Blauwal so groß ist wie ein kleines Auto?"

3. **WITZE (Knopf "Witz"):**
   - Erzähle einen kurzen, harmlosen Kinderwitz (Wortspiele, Tiere, Schule).

4. **GESCHICHTEN (Knopf "Geschichte"):**
   - Erzähle eine KURZE Geschichte (max. 100 Wörter).
   - **Hauptfigur:** Ein Superhelden-Kind (Junge oder Mädchen), das keine Muskelkraft nutzt, sondern **Empathie, Achtsamkeit oder Hilfsbereitschaft**.
   - **Ziel:** Fördere soziale Kompetenzen (Trösten, Teilen, Zuhören, Mut machen).
   - **WICHTIG:** Die Geschichte MUSS mit einer **Reflexionsfrage** an das Kind enden (z.B. "Was hättest du an seiner Stelle getan?" oder "Wie glaubst du, hat sich der Drache gefühlt?").

ALLGEMEINE REGELN:
- Nutze **fette Schrift** für wichtige Wörter.
- Sei herzlich und lobend.
"""

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. 🤖 Was machen wir? Soll ich dir einen Witz erzählen, eine Geschichte oder hast du eine Frage?"}
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


# --- 5. LOGIK FUNKTIONEN ---

def text_to_audio(text):
    """Macht aus Text -> Sprache (MP3)"""
    try:
        # Langsamere Sprechgeschwindigkeit für Kinder wäre ideal, gTTS kann das aber nur bedingt.
        tts = gTTS(text=text, lang='de')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception:
        return None

def verarbeite_nachricht(benutzer_text):
    """Zentrale Funktion: Nimmt Text (vom Button oder Tippen), sendet an AI, macht Audio."""
    
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "parts": benutzer_text})
    
    # 2. AI Antwort generieren
    try:
        response = st.session_state.chat.send_message(benutzer_text)
        text = response.text
        
        # 3. Speichern & Audio
        st.session_state.messages.append({"role": "model", "parts": text})
        
        audio = text_to_audio(text)
        if audio:
            st.session_state.autoplay_audio = audio
            
    except Exception as e:
        st.error("Hoppla, Berti hat den Faden verloren. Probier es nochmal!")

# --- 6. CHAT VERLAUF ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# Audio abspielen (Versteckter Player für Autoplay)
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True, key=f"audio_{st.session_state.audio_key}")
    st.session_state.audio_key += 1 # Key hochzählen für nächsten Play
    st.session_state.autoplay_audio = None

st.markdown("---")

# --- 7. STEUERUNG (BUTTONS & EINGABE) ---

st.write("Klicke einen Knopf oder schreibe etwas:")

# Die drei "Zauber-Knöpfe" für das Kind
col1, col2, col3 = st.columns(3)

klick_witz = False
klick_fakt = False
klick_geschichte = False

with col1:
    # Use_container_width macht die Buttons schön breit
    if st.button("🤣 Witz erzählen", use_container_width=True):
        klick_witz = True
with col2:
    if st.button("🦁 Super-Fakt", use_container_width=True):
        klick_fakt = True
with col3:
    if st.button("🦸 Geschichte", use_container_width=True):
        klick_geschichte = True

# Texteingabe Feld
eingabe_text = st.chat_input("Oder schreibe hier deine Frage...")

# --- 8. AUSFÜHRUNG ---

# Priorität: Erst prüfen ob Buttons geklickt wurden, sonst Textfeld
if klick_witz:
    verarbeite_nachricht("Erzähle mir bitte einen lustigen Witz!")
    st.rerun()

elif klick_fakt:
    verarbeite_nachricht("Erzähle mir einen spannenden Fun Fact (Tiere oder Rekorde)!")
    st.rerun()

elif klick_geschichte:
    verarbeite_nachricht("Erzähle mir eine Superhelden-Geschichte über Gefühle und Hilfsbereitschaft.")
    st.rerun()

elif eingabe_text:
    verarbeite_nachricht(eingabe_text)
    st.rerun()
