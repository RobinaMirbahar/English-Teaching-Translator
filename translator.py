import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os
from io import BytesIO
import base64
from pydub import AudioSegment

# Configure Streamlit page
st.set_page_config(
    page_title="🎤 English Teaching Translator",
    page_icon="🎤",
    layout="wide"
)

# Language options
LANGUAGE_OPTIONS = {
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh",
    "Japanese": "ja",
    "Sindhi": "sd",
    "Urdu": "ur"
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

# Audio recorder component
def audio_recorder():
    st.markdown("### Record Your Voice")
    audio_bytes = st.audio(
        "Click to record",
        format="audio/wav",
        start_label="🎤 Start",
        stop_label="⏹ Stop",
        key="audio_recorder"
    )
    return audio_bytes

# Main app interface
st.title("🎤 English Teaching Translator")

# Input method selection
input_method = st.radio(
    "Choose input method:",
    ["Record Audio", "Upload Audio File"],
    horizontal=True
)

audio_data = None

if input_method == "Record Audio":
    audio_data = audio_recorder()
elif input_method == "Upload Audio File":
    st.markdown("### Upload Audio File")
    uploaded_file = st.file_uploader(
        "Choose an audio file (WAV or MP3)",
        type=["wav", "mp3"],
        key="audio_uploader"
    )
    if uploaded_file:
        audio_data = uploaded_file.read()

# Process audio when available
if audio_data and api_key:
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            if isinstance(audio_data, bytes):  # Uploaded file
                tmp.write(audio_data)
            else:  # Recorded audio
                tmp.write(audio_data.getvalue())
            temp_audio_path = tmp.name

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")

        with st.spinner("🔍 Processing your audio..."):
            # Process with Gemini's native audio understanding
            response = model.generate_content(
                [
                    f"Provide a comprehensive English lesson for a {native_lang} speaker based on this audio. "
                    f"Include: 1) Exact English translation, 2) Pronunciation guide, "
                    f"3) Grammar analysis, 4) Practice sentences, 5) Common mistakes",
                    genai.upload_file(temp_audio_path)
                ]
            )
            
            lesson = response.text
            
            # Display results
            st.success("✅ Analysis Complete!")
            
            # Extract and display translation
            if "1)" in lesson:
                translation = lesson.split("1)")[1].split("2)")[0].strip()
                st.subheader("🔊 Translation")
                st.write(translation)
                
                # Generate audio pronunciation
                with st.spinner("🔊 Generating audio pronunciation..."):
                    tts = gTTS(translation, lang='en', slow=True)
                    audio_bytes = BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)
                    
                    st.subheader("🎧 Listen to Translation")
                    st.audio(audio_bytes, format="audio/mp3")
            
            # Display full lesson
            st.subheader("📚 English Lesson")
            st.markdown(lesson)
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Lesson",
                    data=lesson,
                    file_name="english_lesson.txt",
                    mime="text/plain"
                )
            with col2:
                st.download_button(
                    label="🔊 Download Audio",
                    data=audio_bytes.getvalue(),
                    file_name="pronunciation.mp3",
                    mime="audio/mp3"
                )
    
        # Clean up
        os.unlink(temp_audio_path)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
elif audio_data and not api_key:
    st.warning("🔑 Please enter your Gemini API key in the sidebar")
else:
    st.info("👆 Please record or upload audio to begin")

# Requirements section
st.markdown("---")
st.markdown("""
**Requirements:**
google-generativeai>=0.3.0
gtts>=2.3.1
streamlit>=1.32.0
pydub>=0.25.1

""")
