import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os
from io import BytesIO
import base64
from pydub import AudioSegment
import time

# Configure Streamlit page
st.set_page_config(
    page_title="🎤 English Teaching Translator",
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

# Audio recording component
def audio_recorder_component():
    """Custom audio recorder using browser's MediaRecorder API"""
    recorder_js = """
    <script>
    async function recordAudio() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];
        
        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });
        
        // Start recording
        mediaRecorder.start();
        document.getElementById("status").textContent = "Recording...";
        document.getElementById("stopBtn").disabled = false;
        
        // Return promise that resolves with audio blob
        return new Promise(resolve => {
            document.getElementById("stopBtn").onclick = () => {
                mediaRecorder.stop();
                stream.getTracks().forEach(track => track.stop());
                document.getElementById("status").textContent = "Processing...";
            };
            
            mediaRecorder.addEventListener("stop", () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    window.parent.postMessage({
                        type: 'audioRecording',
                        data: base64data
                    }, '*');
                };
            });
        });
    }
    </script>
    <div>
        <button onclick="recordAudio()" id="startBtn">🎤 Start Recording</button>
        <button disabled id="stopBtn">⏹ Stop</button>
        <span id="status">Ready to record</span>
    </div>
    """
    st.components.v1.html(recorder_js, height=100)

# Main app interface
st.title("🎤 English Teaching Translator")

# Audio input options
input_method = st.radio(
    "Choose input method:",
    ["Record Audio", "Upload Audio File"],
    horizontal=True
)

audio_data = None

if input_method == "Record Audio":
    st.markdown("### 1. Record Your Voice")
    audio_recorder_component()
    
    # Handle recorded audio from JavaScript
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    
    # JavaScript to Python communication
    js_code = """
    <script>
    window.addEventListener('message', (event) => {
        if (event.data.type === 'audioRecording') {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: event.data.data
            }, '*');
        }
    });
    </script>
    """
    result = st.components.v1.html(js_code, height=0)
    
    if result is not None:
        st.session_state.audio_data = result
        st.success("✅ Recording received!")

elif input_method == "Upload Audio File":
    st.markdown("### 1. Upload Audio File")
    uploaded_file = st.file_uploader(
        "Choose an audio file (WAV or MP3)",
        type=["wav", "mp3"]
    )
    if uploaded_file:
        audio_data = uploaded_file.read()

# Process audio when available
if (st.session_state.get('audio_data') or audio_data) and api_key:
    try:
        # Prepare audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            if audio_data:  # From file upload
                tmp.write(audio_data)
            else:  # From recording
                audio_bytes = base64.b64decode(st.session_state.audio_data)
                tmp.write(audio_bytes)
            temp_audio_path = tmp.name

        # Display audio player
        st.audio(temp_audio_path, format="audio/wav")

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
        if 'audio_data' in st.session_state:
            del st.session_state.audio_data

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
elif (st.session_state.get('audio_data') or audio_data) and not api_key:
    st.warning("🔑 Please enter your Gemini API key in the sidebar")
else:
    st.info("👆 Please record or upload audio to begin")

# Requirements note
st.markdown("---")
st.markdown("""
**Requirements:**
```python
google-generativeai>=0.3.0
gtts>=2.3.1
streamlit>=1.32.0
pydub>=0.25.1  # For MP3 support
