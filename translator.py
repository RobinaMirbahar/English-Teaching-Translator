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

# Recording control buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🎤 Start Recording", disabled=st.session_state.recording):
        st.session_state.recording = True
        st.session_state.audio_available = False
        st.rerun()

with col2:
    if st.button("⏹ Stop Recording", disabled=not st.session_state.recording):
        st.session_state.recording = False
        st.session_state.audio_available = True
        st.rerun()

# Status indicators
if st.session_state.recording:
    st.warning("Recording... Speak now. Click 'Stop Recording' when done.")
elif st.session_state.audio_available:
    st.success("Recording complete! Click 'Process Recording' below")

# Process recording button
if st.session_state.audio_available and st.button("🔍 Process Recording"):
    try:
        # For demo purposes - in production you'd use actual recorded audio
        # Here we'll use a temporary WAV file as placeholder
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            # Create silent audio as placeholder (replace with real recording)
            sf.write(tmp.name, np.zeros(44100), 44100)
            temp_audio_path = tmp.name

        # Process with Gemini 1.5 (most current version)
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

            # Simulate speech recognition (replace with real implementation)
            native_text = "This is a sample text in your native language"
            
            # Generate lesson
            prompt = f"""
            Create a comprehensive English lesson for a {native_lang} speaker who said:
            "{native_text}"

            Include these sections with Markdown formatting:
            
            ### 1. English Translation
            [Provide natural English equivalent]
            
            ### 2. Pronunciation Guide
            - IPA transcription
            - Syllable breakdown
            - Stress patterns
            
            ### 3. Grammar Analysis
            [Explain key grammatical structures]
            
            ### 4. Practice Exercises
            - 3 simple sentences (beginner)
            - 2 complex sentences (intermediate)
            - 1 dialogue example (advanced)
            
            ### 5. Common Mistakes
            [What learners typically get wrong]
            
            ### 6. Cultural Notes
            [Relevant cultural context]
            """
            
            response = model.generate_content(prompt)
            lesson = response.text
            
            # Display results
            st.success("✅ Analysis Complete!")
            st.subheader("🔊 What You Said")
            st.code(native_text, language="text")
            
            st.subheader("📚 English Lesson")
            st.markdown(lesson)
            
            # Generate audio translation
            if "### 1. English Translation" in lesson:
                translation = "This is the English translation"  # Replace with actual translation
                
                with st.spinner("🔊 Generating audio pronunciation..."):
                    tts = gTTS(translation, lang='en', slow=True)
                    audio_bytes = BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)
                    
                    st.subheader("🎧 Listen to Translation")
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    # Download options
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download Lesson (Text)",
                            data=lesson,
                            file_name="english_lesson.md",
                            mime="text/markdown"
                        )
                    with col2:
                        st.download_button(
                            label="🔊 Download Audio",
                            data=audio_bytes,
                            file_name="pronunciation.mp3",
                            mime="audio/mp3"
                        )
        
        # Clean up
        os.unlink(temp_audio_path)
        st.session_state.audio_available = False
        
    except Exception as e:
        st.error(f"Error processing recording: {str(e)}")

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
