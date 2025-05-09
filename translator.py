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
    st.info("Record audio using the button below, then click 'Save Recording'")

# Main app interface
st.title("🎤 English Teaching Translator")
st.markdown("### 1. Record Your Audio")

# Audio recording state
if 'audio_frames' not in st.session_state:
    st.session_state.audio_frames = []
if 'recording' not in st.session_state:
    st.session_state.recording = False

# Start/Stop recording buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🎤 Start Recording", disabled=st.session_state.recording):
        st.session_state.recording = True
        st.session_state.audio_frames = []
        st.experimental_rerun()

with col2:
    if st.button("⏹ Stop Recording", disabled=not st.session_state.recording):
        st.session_state.recording = False
        st.experimental_rerun()

# Status indicator
if st.session_state.recording:
    st.warning("Recording... Speak now. Click 'Stop Recording' when done.")
else:
    st.info("Click 'Start Recording' to begin")

# Save recording button (only shows after stopping)
if not st.session_state.recording and st.session_state.audio_frames:
    if st.button("💾 Save Recording"):
        try:
            # Convert frames to WAV
            audio_array = np.concatenate(st.session_state.audio_frames)
            temp_audio_path = "recording.wav"
            sf.write(temp_audio_path, audio_array, 44100)
            
            # Process with Gemini 2.5
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    "gemini-1.5-pro-latest",  # Updated to latest available
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 1,
                        "top_k": 32,
                        "max_output_tokens": 4096,
                    }
                )

                # Recognize speech
                with st.spinner("🔍 Processing your audio..."):
                    with sr.AudioFile(temp_audio_path) as source:
                        audio_data = r.record(source)
                        native_text = r.recognize_google(
                            audio_data,
                            language=LANGUAGE_OPTIONS[native_lang]
                        )

                    # Generate lesson with Gemini 2.5
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
            st.session_state.audio_frames = []
            
        except Exception as e:
            st.error(f"Error processing recording: {str(e)}")

# Audio processing fallback (file upload)
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

# JavaScript for basic audio recording (fallback)
audio_js = """
<script>
const record = () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];
        
        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });
        
        mediaRecorder.start();
        
        setTimeout(() => {
            mediaRecorder.stop();
            const audioBlob = new Blob(audioChunks);
            const audioUrl = URL.createObjectURL(audioBlob);
            // Send to Streamlit
            window.parent.postMessage({audioUrl: audioUrl}, "*");
        }, 5000); // Record for 5 seconds
    });
}
</script>
"""

# Add the JavaScript
st.components.v1.html(audio_js, height=0)
