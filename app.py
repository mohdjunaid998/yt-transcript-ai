import streamlit as st
import os, re, whisper, yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="YT Transcript AI", page_icon="🚀", layout="centered")

def extract_video_id(url):
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def transcribe_whisper(url):
    # Agar repo mein cookies.txt hai toh use use karein block se bachne ke liye
    cookie_file = "cookies.txt" if os.path.exists("cookies.txt") else None
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'no_warnings': True,
    }
    
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        model = whisper.load_model("tiny")
        result = model.transcribe("temp_audio.mp3")
        
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        return result['text']
    except Exception as e:
        return f"❌ Download Error: YouTube has blocked the server IP. Please upload 'cookies.txt' to GitHub or try a different video. Error details: {str(e)}"

# --- UI ---
st.title("🎬 YT Transcript AI")

url_input = st.text_input("Paste Link Here", placeholder="https://...")
mode = st.checkbox("Include Timestamps (Manual only)")

if st.button("Generate Transcript →"):
    if url_input:
        v_id = extract_video_id(url_input)
        if v_id:
            with st.spinner("Step 1: Checking YouTube Database..."):
                try:
                    # First try API
                    transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
                    t = transcript_list.find_transcript(['en', 'hi'])
                    data = t.fetch()
                    res = " ".join([i['text'] for i in data])
                    st.success("Found Manual Transcript!")
                    st.text_area("Result", res, height=400)
                except:
                    st.info("Manual transcript not found. Trying AI (Whisper)...")
                    res = transcribe_whisper(url_input)
                    if "❌" in res:
                        st.error(res)
                    else:
                        st.text_area("AI Result", res, height=400)
        else:
            st.error("Invalid URL")
