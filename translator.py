import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import tempfile
import os
from io import BytesIO
import numpy as np
import soundfile as sf

# Initialize speech recognizer
r = sr.Recognizer()

# Configure Streamlit page
st.set_page_config(
    page_title="🎤 English Teaching Translator",
    page_icon="🎤",
    layout="wide"
)

# Language options with Sindhi and Urdu
LANGUAGE_OPTIONS = {
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Chinese": "zh-CN",
    "Japanese": "ja-JP",
    "Sindhi": "sd-PK",
    "Urdu": "ur-PK"
}

# Sidebar configuration
with st.sidebar:
    st.title("🔑 Configuration")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")
    
    native_lang = st.selectbox(
        "Your native language:",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=5  # Default to Sindhi
    )
    
    st.markdown("---")
    st.info("Record audio using the button below, then click 'Process Recording'")

# Main app interface
st.title("🎤 English Teaching Translator")
st.markdown("### 1. Record Your Audio")

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'audio_available' not in st.session_state:
    st.session_state.audio_available = False
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None

# Audio recording function
def record_audio():
    with sr.Microphone() as source:
        st.info("Speak now...")
        audio = r.listen(source)
        st.session_state.audio_data = audio
        st.session_state.audio_available = True
        st.success("Recording complete!")

# Recording control buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🎤 Start Recording", disabled=st.session_state.recording):
        st.session_state.recording = True
        st.session_state.audio_available = False
        record_audio()
        st.session_state.recording = False
        st.rerun()

# Process recording button
if st.session_state.audio_available and st.button("🔍 Process Recording"):
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_data = st.session_state.audio_data
            with open(tmp.name, "wb") as f:
                f.write(audio_data.get_wav_data())
            temp_audio_path = tmp.name

        # Process with Gemini 1.5
        if api_key:
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

            # Recognize speech
            with st.spinner("Processing your audio..."):
                with sr.AudioFile(temp_audio_path) as source:
                    audio_data = r.record(source)
                    native_text = r.recognize_google(
                        audio_data,
                        language=LANGUAGE_OPTIONS[native_lang]
                    )
                
                # Generate concise lesson
                prompt = f"""
                Provide a focused English lesson for a {native_lang} speaker who said:
                "{native_text}"

                Include ONLY:
                1. Accurate English translation
                2. Key pronunciation tips (3-4 points)
                3. Main grammar points (2-3)
                4. 2 practice sentences
                
                Keep responses brief and pedagogical.
                """
                
                response = model.generate_content(prompt)
                lesson = response.text
                
                # Display results
                st.success("✅ Analysis Complete!")
                st.subheader("🔊 What You Said")
                st.write(native_text)
                
                st.subheader("📚 English Lesson")
                st.write(lesson)
                
                # Generate audio translation
                translation = lesson.split("1. ")[1].split("2. ")[0].replace("English translation:", "").strip()
                
                with st.spinner("Generating audio pronunciation..."):
                    tts = gTTS(translation, lang='en', slow=True)
                    audio_bytes = BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)
                    
                    st.subheader("🎧 Listen to Translation")
                    st.audio(audio_bytes, format="audio/mp3")
        
        # Clean up
        os.unlink(temp_audio_path)
        st.session_state.audio_available = False
        
    except sr.UnknownValueError:
        st.error("Could not understand audio. Please speak more clearly.")
    except sr.RequestError as e:
        st.error(f"Speech recognition service error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

# File upload fallback
st.markdown("---")
st.markdown("### Alternatively, upload an audio file:")
uploaded_file = st.file_uploader(
    "Upload WAV audio file",
    type=["wav"],
    key="audio_uploader"
)

if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            temp_audio_path = tmp.name

        st.audio(temp_audio_path, format="audio/wav")
        
        # Process with Gemini (same as above)
        # ... [include the same processing code as above]
        
        os.unlink(temp_audio_path)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
