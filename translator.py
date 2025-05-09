import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

# Configure Streamlit
st.set_page_config(
    page_title="🎤 English Teaching Translator",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize recognizer
r = sr.Recognizer()

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
    st.info("""
        **Recording Instructions:**
        1. Click the microphone button
        2. Allow browser microphone access
        3. Speak clearly for 5 seconds
        4. Click stop when finished
    """)

# Main app interface
st.title("🎤 English Teaching Translator")
st.markdown("""
    <style>
    .big-font { font-size:18px !important; }
    </style>
    <p class="big-font">Speak in your native language and get a complete English lesson!</p>
""", unsafe_allow_html=True)

# Audio recording
audio_bytes = None
with st.expander("🎤 Record Audio (5 seconds)", expanded=True):
    audio_bytes = st.audio(
        "Click to record",
        format="audio/wav",
        start_label="🎤 Start Recording",
        stop_label="⏹ Stop Recording",
        sample_rate=16000,
        key="audio_recorder"
    )

# Processing logic
if api_key and audio_bytes:
    try:
        # Configure Gemini
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

        # Process audio
        with st.spinner("🔄 Processing your audio..."):
            with sr.AudioFile(audio_file) as source:
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
            
            # Audio translation
            if "### 1. English Translation" in lesson:
                translation = lesson.split("### 1. English Translation")[1].split("### 2. Pronunciation Guide")[0].strip()
                
                with st.spinner("🔊 Generating audio pronunciation..."):
                    tts = gTTS(translation, lang='en', slow=True)
                    tts.save("translation.mp3")
                    
                    st.subheader("🎧 Listen to Translation")
                    st.audio("translation.mp3", format="audio/mp3")
                    
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

    except sr.UnknownValueError:
        st.error("🔇 Could not understand audio. Please speak more clearly.")
    except sr.RequestError:
        st.error("🌐 Speech service error. Please check your internet connection.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
elif api_key and not audio_bytes:
    st.warning("🎤 Please record your voice to get started")
elif not api_key:
    st.warning("🔑 Please enter your Gemini API key in the sidebar")
