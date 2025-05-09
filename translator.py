import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import tempfile
import os
from pydub import AudioSegment
from io import BytesIO

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
    st.info("Upload a WAV audio file or record using the button below")

# Audio input options
st.title("🎤 English Teaching Translator")
st.markdown("### 1. Provide Your Audio Input")

# Option 1: File uploader
audio_file = st.file_uploader(
    "Upload audio file (WAV format)",
    type=["wav"],
    accept_multiple_files=False,
    key="audio_uploader"
)

# Option 2: Record audio (using alternative method)
st.markdown("---")
st.markdown("### Or record using your microphone:")
st.warning("Note: Direct microphone recording requires HTTPS. For local testing, use file upload.")

# Process audio when provided
if audio_file:
    try:
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_file.read())
            temp_audio_path = tmp.name

        # Display audio player
        st.audio(audio_file, format="audio/wav")

        # Process with Gemini when API key is available
        if api_key:
            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-pro-latest")

            # Recognize speech
            with st.spinner("Processing your audio..."):
                with sr.AudioFile(temp_audio_path) as source:
                    audio_data = r.record(source)
                    native_text = r.recognize_google(
                        audio_data,
                        language=LANGUAGE_OPTIONS[native_lang]
                    )

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
                - 3 simple sentences
                - 2 complex sentences
                - 1 dialogue example
                
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
                    translation = lesson.split("### 1. English Translation")[1].split("### 2. Pronunciation Guide")[0].strip()
                    
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

    except sr.UnknownValueError:
        st.error("🔇 Could not understand audio. Please speak more clearly.")
    except sr.RequestError as e:
        st.error(f"🌐 Speech service error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
elif not api_key:
    st.warning("🔑 Please enter your Gemini API key in the sidebar")
