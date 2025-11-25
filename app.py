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

# --- 4. BERTIS NEUE PERSÖNLICHKEIT (SOKRATES-MODUS) ---
system_prompt = """
Du bist "Berti", ein geduldiger, kluger und freundlicher Mentor für ein 6-jähriges Kind.
Dein Ziel: Das Kind beim Lernen begleiten und echtes Sachwissen vermitteln.

DEINE REGELN FÜR DEN DIALOG:
1. TONALITÄT: Ruhig, freundlich, wertschätzend. KEINE albernen Geräusche (kein Boing, Zisch, etc.).
2. METHODE (SOKRATES): Gib nicht sofort die komplette Lösung vor. Stelle stattdessen eine vereinfachende Gegenfrage oder gib einen Hinweis, der das Kind selbst auf die Lösung bringt.
3. SCHRITT-FÜR-SCHRITT: Zerlege komplexe Probleme in kleine, verdauliche Häppchen.
4. FAKTEN: Konzentriere dich auf echtes Sachwissen (Natur, Technik, Geschichte). Keine Halluzinationen oder Fantasie-Quatsch.
5. AUFLÖSUNG: Wenn das Kind die Lösung findet (oder gar nicht weiterkommt), bestätige die richtige Antwort klar und verständlich.
6. KONTINUITÄT: Beende deine Antwort IMMER mit einer sanften Gegenfrage, um das Gespräch am Laufen zu halten (z.B. "Hast du so etwas schon mal gesehen?" oder "Was glaubst du, passiert danach?").

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

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])

# --- 6. AUDIO LOGIK MIT GEDÄCHTNIS ---
audio_value = st.audio_input("Deine Antwort / Deine Frage:")

if audio_value:
    # A) Audio anzeigen
    with st.chat_message("user"):
        st.write("🎤 *(Audio Nachricht gesendet)*")
    st.session_state.messages.append({"role": "user", "parts": "🎤 *(Audio Nachricht)*"})

    # B) Kontext bauen (Was hat Berti zuletzt gesagt?)
    # Wir holen die letzte Antwort des Bots, damit er weiß, worum es geht
    last_bot_response = ""
    if len(st.session_state.messages) > 1:
        # Suche rückwärts nach der letzten Model-Nachricht
        for msg in reversed(st.session_state.messages[:-1]):
            if msg["role"] == "model":
                last_bot_response = msg["parts"]
                break
    
    # C) Nachdenken
    with st.spinner('Berti hört zu und denkt nach...'):
        try:
            # Wir bauen einen Prompt, der den Kontext enthält
            full_prompt_parts = [
                system_prompt,
                f"Kontext (Das hast du das Kind gerade gefragt): {last_bot_response}",
                "Antworte dem Kind jetzt auf seine Audio-Eingabe. Führe den Dialog weiter:",
                {"mime_type": "audio/mp3", "data": audio_value.getvalue()}
            ]

            response = model.generate_content(full_prompt_parts)
            bot_text = response.text

            # D) Text Antwort anzeigen
            with st.chat_message("model"):
                st.markdown(bot_text)
            
            # E) Audio generieren
            tts = gTTS(text=bot_text, lang='de')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            
            # WICHTIG: Bytes für den Browser vorbereiten
            audio_bytes = audio_fp.getvalue()
            
            # F) Abspielen
            st.audio(audio_bytes, format='audio/mp3', autoplay=True)

            # G) Speichern
            st.session_state.messages.append({"role": "model", "parts": bot_text})

        except Exception as e:
            st.error(f"Ein kleiner Fehler ist aufgetreten: {str(e)}")

# Reset Button
with st.sidebar:
    if st.button("Neues Thema starten 🔄"):
        st.session_state.messages = []
        st.rerun()
