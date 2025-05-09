import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import tempfile
import os
from io import BytesIO
import numpy as np
import soundfile as sf
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration, AudioProcessorBase
import av
import queue

# Initialize speech recognizer
r = sr.Recognizer()

# Enhanced WebRTC Configuration with fallback
RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
        {"urls": ["stun:stun2.l.google.com:19302"]},
        # Add your TURN server credentials here if available
        # {
        #     "urls": "turn:your.turn.server:3478",
        #     "username": "your_username",
        #     "credential": "your_password"
        # }
    ]
})

# Configure Streamlit page
st.set_page_config(
    page_title="🎤 English Teaching Translator",
    page_icon="🎤",
    layout="wide"
)

# Language options
LANGUAGE_OPTIONS = {
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Chinese": "zh-CN",
    "Japanese": "ja-JP",
    "Sindhi": "sd-PK",
    "Urdu": "ur-PK"
}

class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = queue.Queue()
    
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.audio_frames.put(frame.to_ndarray())
        return frame

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
    st.info("Choose an audio input method below")

# Audio Input Section
st.title("🎤 English Teaching Translator")
st.header("1. Provide Your Audio Input")

# Option 1: File Uploader (always available)
uploaded_file = st.file_uploader(
    "Upload audio file (WAV format)",
    type=["wav"],
    help="Maximum 10MB, WAV format only",
    key="audio_uploader"
)

# Option 2: Microphone Recording with better handling
st.markdown("---")
st.markdown("### Or try microphone recording:")

audio_frames = []
saved_audio_path = None

def process_audio_frames(frames):
    """Convert audio frames to WAV file"""
    if frames:
        audio_array = np.concatenate(frames)
        temp_path = "recording.wav"
        sf.write(temp_path, audio_array, 44100)
        return temp_path
    return None

if 'recording' not in st.session_state:
    st.session_state.recording = False

if st.button("Start Recording" if not st.session_state.recording else "Stop Recording"):
    st.session_state.recording = not st.session_state.recording
    if st.session_state.recording:
        st.warning("Recording... Speak now. Click again to stop.")
        audio_frames = []
        webrtc_ctx = webrtc_streamer(
            key="mic_recorder",
            mode=WebRtcMode.SENDONLY,
            audio_processor_factory=AudioRecorder,
            media_stream_constraints={
                "audio": {
                    "sampleRate": 44100,
                    "channelCount": 1,
                    "echoCancellation": True,
                    "noiseSuppression": True
                }
            },
            rtc_configuration=RTC_CONFIGURATION,
            async_processing=True
        )
        
        if webrtc_ctx and webrtc_ctx.audio_processor:
            while st.session_state.recording:
                try:
                    frame = webrtc_ctx.audio_processor.audio_frames.get(timeout=1)
                    audio_frames.append(frame)
                except queue.Empty:
                    continue
            
            saved_audio_path = process_audio_frames(audio_frames)
            if saved_audio_path:
                uploaded_file = saved_audio_path
                st.success("✅ Recording saved!")
                st.audio(saved_audio_path, format="audio/wav")

# Process audio when provided
if uploaded_file:
    try:
        # Handle both uploaded files and recorded audio
        if isinstance(uploaded_file, str):  # Recorded audio
            temp_audio_path = uploaded_file
        else:  # Uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_file.read())
                temp_audio_path = tmp.name

        # Display audio player
        st.audio(temp_audio_path, format="audio/wav")

        # Process with Gemini when API key is available
        if api_key:
            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-pro-latest")

            # Recognize speech
            with st.spinner("🔍 Processing your audio..."):
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
        if not isinstance(uploaded_file, str):
            os.unlink(temp_audio_path)
        elif os.path.exists(uploaded_file) and uploaded_file != "recording.wav":
            os.unlink(uploaded_file)

    except sr.UnknownValueError:
        st.error("🔇 Could not understand audio. Please speak more clearly.")
    except sr.RequestError as e:
        st.error(f"🌐 Speech service error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
elif not api_key:
    st.warning("🔑 Please enter your Gemini API key in the sidebar")
else:
    st.info("👆 Please upload an audio file or record using your microphone")

# Connection troubleshooting
if not st.session_state.get('recording', False):
    st.warning("""
    **If microphone recording fails:**
    1. Try using Chrome/Firefox
    2. Ensure microphone permissions are granted
    3. Try the file upload option instead
    4. Refresh the page if issues persist
    """)
