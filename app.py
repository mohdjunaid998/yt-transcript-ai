import streamlit as st
import os, re, whisper, yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# Page Config (ChatGPT Style)
st.set_page_config(page_title="YT Transcript AI", page_icon="??", layout="centered")

# Custom CSS for ChatGPT-like feel
st.markdown("""
    <style>
    .stTextInput > div > div > input { border-radius: 20px; }
    .stButton > button { border-radius: 20px; width: 100%; background-color: #10a37f; color: white; }
    .transcript-box { background-color: #f7f7f8; padding: 20px; border-radius: 10px; border: 1px solid #d1d1e0; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic Functions ---

def extract_video_id(url):
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc:
        return parse_qs(parsed.query).get('v', [None])[0]
    if 'youtu.be' in parsed.netloc:
        return parsed.path.lstrip('/')
    return None

def get_manual_transcript(video_id, with_timestamps=False):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # Try finding manually created/supported transcripts
        try:
            t = transcript_list.find_manually_created_transcript(['en', 'hi'])
        except:
            t = transcript_list.find_generated_transcript(['en', 'hi'])
            
        data = t.fetch()
        if with_timestamps:
            return "\n".join([f"[{int(i['start']//60)}:{int(i['start']%60):02d}] {i['text']}" for i in data])
        return " ".join([i['text'] for i in data])
    except:
        return None

def transcribe_whisper(url, with_timestamps=False):
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    model = whisper.load_model("tiny") # Fast and light for web
    result = model.transcribe("temp_audio.mp3")
    os.remove("temp_audio.mp3")
    return result['text']

# --- UI Layout ---

st.title("?? YT Transcript AI")
st.caption("ChatGPT-style YouTube Transcript Extractor")

url = st.text_input("Paste YouTube Link here...", placeholder="https://youtube.com/watch?v=...")
col1, col2 = st.columns([4, 1])
with col1:
    mode = st.checkbox("Include Timestamps?")
with col2:
    submit = st.button("Extract ?")

if submit and url:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("Invalid URL")
    else:
        with st.status("Extracting... please wait", expanded=True) as status:
            st.write("Checking YouTube Database...")
            transcript = get_manual_transcript(video_id, mode)
            
            if not transcript:
                st.write("Manual transcript not found. Initializing Whisper AI...")
                transcript = transcribe_whisper(url, mode)
            
            status.update(label="Transcript Ready!", state="complete")

        st.subheader("Final Transcript")
        # ChatGPT style text output with copy button
        st.text_area(label="Result", value=transcript, height=400)
        st.download_button("Download as Text", transcript, file_name="transcript.txt")