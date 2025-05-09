import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

# Streamlit UI Configuration
st.set_page_config(page_title="🎤 English Teaching Translator", layout="wide")

# Sidebar for API Key Input
with st.sidebar:
    st.title("🔑 API Configuration")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")
    language_options = {
        "Spanish": "es-ES",
        "French": "fr-FR",
        "German": "de-DE",
        "Chinese": "zh-CN",
        "Japanese": "ja-JP",
        "Hindi": "hi-IN"
    }
    native_lang = st.selectbox("Your native language:", options=list(language_options.keys()))
    st.markdown("---")
    st.info("Allow microphone access when prompted by your browser")

# Main App Interface
st.title("🎤 English Teaching Translator")
st.markdown("Speak in your native language and get an English lesson!")

# Initialize session state
if 'audio_processed' not in st.session_state:
    st.session_state.audio_processed = False

# Audio recording via Streamlit
audio_bytes = st.audio(
    "record",
    format="audio/wav",
    start_label="🎤 Record (5 seconds)",
    stop_label="⏹ Stop",
    sample_rate=16000,
    key="audio_recorder"
)

# Process when API key is provided and audio is recorded
if api_key and audio_bytes:
    try:
        # Configure Gemini with user-provided API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-pro-latest",
            generation_config={
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 4096,
            }
        )

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            audio_file = tmp.name

        # Process audio and generate lesson
        @st.cache_data(show_spinner="Processing your audio...")
        def process_audio(audio_file, lang_code):
            r = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio = r.record(source)
            native_text = r.recognize_google(audio, language=lang_code)
            
            prompt = f"""
            As an expert English teacher, create a lesson for a {native_lang} speaker who said:
            "{native_text}"
            
            Include:
            1. Natural English translation
            2. IPA pronunciation guide
            3. Grammar breakdown
            4. 3 practice sentences (beginner to advanced)
            5. Common mistakes to avoid
            6. Cultural notes if relevant
            
            Format with clear markdown formatting.
            """
            
            response = model.generate_content(prompt)
            return native_text, response.text

        native_text, lesson = process_audio(audio_file, language_options[native_lang])
        
        # Display results
        st.subheader("🔊 What You Said")
        st.write(f"*{native_text}*")
        
        st.subheader("📚 English Lesson")
        st.markdown(lesson)
        
        # Generate and play audio translation
        if "1. Natural English translation" in lesson:
            translation = lesson.split("1. Natural English translation")[1].split("2. IPA pronunciation guide")[0].strip()
            
            with st.spinner("Generating audio pronunciation..."):
                tts = gTTS(translation, lang='en', slow=True)
                tts.save("translation.mp3")
                
                # Auto-play audio
                audio_file = open("translation.mp3", "rb")
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                
                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Lesson",
                        data=lesson,
                        file_name="english_lesson.txt",
                        mime="text/plain"
                    )
                with col2:
                    with open("translation.mp3", "rb") as f:
                        st.download_button(
                            label="🔊 Download Audio",
                            data=f,
                            file_name="pronunciation.mp3",
                            mime="audio/mp3"
                        )
        
        # Clean up
        os.unlink(audio_file)
        if os.path.exists("translation.mp3"):
            os.unlink("translation.mp3")
            
        st.session_state.audio_processed = True

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Please try recording again or check your API key")

elif api_key and not audio_bytes:
    st.warning("Please record your voice to get started")
elif not api_key:
    st.warning("Please enter your Gemini API key in the sidebar")
