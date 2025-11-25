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

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hallo! Ich bin Berti. Welches Thema interessiert dich? Tiere, Ritter oder Weltraum?"}
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

# --- 5. PERSÖNLICHKEIT ---
system_prompt = """
Du bist "Berti", ein Mentor für ein 6-jähriges Kind.
DEINE REGELN:

1. KEINE BEGRÜSSUNG: Sag NIEMALS "Hallo" am Anfang (außer beim allerersten Satz).
2. KEINE FLOSKELN: Keine Sätze wie "Tolle Frage".
3. STRUKTUR & PÄDAGOGIK (WICHTIG):
   - Phase 1 (Neues Thema): Gib NICHT sofort die Lösung/Fachbegriffe. Stelle erst eine Frage, die zum Beobachten oder Vermuten anregt (z.B. "Was glaubst du, warum das so ist?" oder "Hast du das schon mal genau angesehen?").
   - Phase 2 (Kind hat vermutet): JETZT bestätige die Idee und liefere das Fachwissen/Fachbegriffe (z.B. **Geotropismus**). Erkläre es einfach.
4. FORMATIERUNG: Nutze gerne **fette Schrift** für wichtige Wörter im Text, aber sprich sie ganz normal aus.
5. TONALITÄT: Freundlich, sachbezogen, zügig.
"""

# --- 6. CHAT ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# AUDIO PLAYER (AUTOPLAY)
if st.session_state.autoplay_audio:
    st.audio(st.session_state.autoplay_audio, format='audio/mpeg', autoplay=True)
    st.caption("🔊 Falls du nichts hörst, tippe oben auf Play ▶️")
    st.session_state.autoplay_audio = None

st.markdown("---")
st.write("Antworte per Sprache oder Text:")

# --- 7. EINGABE BEREICH ---

# A) RESET BUTTON (Falls Audio klemmt)
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Mikrofon klemmt? Klicke hier:")
with col2:
    if st.button("Neu 🔄"):
        st.session_state.audio_key += 1
        st.rerun()

# B) AUDIO EINGABE
audio_value = st.audio_input("Aufnahme:", key=f"rec_{st.session_state.audio_key}")

# C) TEXT EINGABE (Fallback)
text_input = st.chat_input("Oder schreibe deine Antwort hier...")

# --- 8. VERARBEITUNG ---
user_content = None
content_type = None # "audio" oder "text"

# Prüfen was reinkam
if audio_value:
    user_content = audio_value
    content_type = "audio"
elif text_input:
    user_content = text_input
    content_type = "text"

if user_content:
    # 1. Nutzer-Nachricht anzeigen
    with st.chat_message("user"):
        if content_type == "audio":
            st.write("🎤 *(Audio gesendet)*")
            user_msg_log = "🎤 *(Audio)*"
            # Daten für Prompt vorbereiten
            user_data_part = {"mime_type": "audio/mp3", "data": user_content.getvalue()}
            prompt_instruction = "Antworte auf dieses Audio:"
        else:
            st.write(user_content)
            user_msg_log = user_content
            # Daten für Prompt vorbereiten
            user_data_part = f"Der Nutzer schreibt: {user_content}"
            prompt_instruction = "Antworte auf diesen Text:"

    st.session_state.messages.append({"role": "user", "parts": user_msg_log})

    # 2. Kontext holen
    last_bot_response = ""
    if len(st.session_state.messages) > 1:
        for msg in reversed(st.session_state.messages[:-1]):
            if msg["role"] == "model":
                last_bot_response = msg["parts"]
                break

    # 3. KI Denken lassen
    with st.spinner('Berti denkt nach...'):
        try:
            prompt_content = [
                system_prompt,
                f"Kontext (Deine letzte Aussage war): {last_bot_response}",
                prompt_instruction,
                user_data_part
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
                
                # Sternchen entfernen für Audio
                text_for_audio = bot_text.replace("*", "").replace("_", "")
                
                tts = gTTS(text=text_for_audio, lang='de')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.session_state.autoplay_audio = audio_fp.getvalue()
                
                # WICHTIG: Audio-Widget resetten für nächste Runde
                st.session_state.audio_key += 1
                st.rerun()

        except Exception as e:
            st.error(f"Fehler: {e}")
