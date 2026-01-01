import streamlit as st
import os, re, whisper, yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# Page Setup (ChatGPT Dark Theme)
st.set_page_config(page_title="Ultimate YT Transcriber", layout="wide")

st.markdown("""
    <style>
    .stTextArea textarea { font-size: 1.1rem !important; line-height: 1.6 !important; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #10a37f; color: white; }
    </style>
    """, unsafe_allow_html=True)

def extract_video_id(url):
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def fetch_api_transcript(video_id):
    """Bina download kiye YouTube se transcript nikalne ka tareeka"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 1. Pehle Manual English/Hindi dhundo
        try:
            t = transcript_list.find_transcript(['en', 'hi'])
        except:
            # 2. Agar nahi mili toh pehli available transcript uthao aur usey English mein translate karo
            t = transcript_list.find_transcript(transcript_list._manually_created_transcripts.keys() or transcript_list._generated_transcripts.keys())
            if t.language_code != 'en':
                t = t.translate('en')
        
        data = t.fetch()
        return " ".join([i['text'] for i in data])
    except Exception as e:
        return None

def transcribe_whisper(url):
    """Ye tabhi chalega jab API fail ho jayegi (Isme block ka khatra hai)"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}],
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        model = whisper.load_model("tiny")
        result = model.transcribe("audio.mp3")
        if os.path.exists("audio.mp3"): os.remove("audio.mp3")
        return result['text']
    except Exception as e:
        return f"ERROR: YouTube Blocked Audio Access. Try a video with subtitles."

# --- UI ---
st.title("🎬 YT Transcript Pro AI")
st.write("Extract text from any video - Powered by AI")

url = st.text_input("Paste YouTube Link:", placeholder="https://youtube.com/...")

if st.button("Extract Transcript ✨"):
    if url:
        v_id = extract_video_id(url)
        if v_id:
            with st.status("Working on it...") as status:
                st.write("Searching YouTube Database (No-Download Mode)...")
                final_output = fetch_api_transcript(v_id)
                
                if not final_output:
                    st.write("Manual transcript not found. Attempting AI Whisper...")
                    final_output = transcribe_whisper(url)
                
                status.update(label="Complete!", state="complete")
            
            st.subheader("Final Result:")
            st.text_area("", value=final_output, height=450)
            st.download_button("Download Text", final_output, file_name="transcript.txt")
        else:
            st.error("Invalid URL!")
