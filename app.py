import streamlit as st
import os, re, whisper, yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# Page Config
st.set_page_config(page_title="YT Transcript AI", page_icon="🚀", layout="centered")

# ChatGPT Style CSS
st.markdown("""
    <style>
    .stTextInput > div > div > input { border-radius: 10px; }
    .stTextArea > div > div > textarea { background-color: #f7f7f8; color: #333; border-radius: 10px; }
    .stButton > button { border-radius: 10px; background-color: #10a37f; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

def extract_video_id(url):
    # Sabhi tarah ke links ke liye regex (Shorts, Mobile, Desktop)
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_manual_transcript(video_id, with_timestamps=False):
    try:
        # Pehle manual transcript check karo
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            # Try English or Hindi
            t = transcript_list.find_transcript(['en', 'hi'])
        except:
            # Agar nahi hai toh koi bhi available utha lo aur English mein translate karo
            t = transcript_list.find_transcript(transcript_list._manually_created_transcripts.keys() or transcript_list._generated_transcripts.keys()).translate('en')
        
        data = t.fetch()
        if with_timestamps:
            return "\n".join([f"[{int(i['start']//60)}:{int(i['start']%60):02d}] {i['text']}" for i in data])
        return " ".join([i['text'] for i in data])
    except Exception as e:
        return None

def transcribe_whisper(url):
    # Download settings
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 'tiny' model is best for free hosting
        model = whisper.load_model("tiny")
        result = model.transcribe("temp_audio.mp3", task="transcribe")
        
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        return result['text']
    except Exception as e:
        return f"Whisper Error: {str(e)}"

# UI
st.title("🎬 YT Transcript AI")
st.write("Enter any YouTube URL to get the full transcript.")

url_input = st.text_input("Paste Link Here (Normal, Shorts, or Mobile)", placeholder="https://...")
ts_check = st.checkbox("Include Timestamps (Only for manual transcripts)")

if st.button("Generate Transcript →"):
    if url_input:
        v_id = extract_video_id(url_input)
        if v_id:
            with st.spinner("Processing... Please wait"):
                # 1. Try Manual
                res = get_manual_transcript(v_id, ts_check)
                
                # 2. Try Whisper if Manual Fails
                if not res:
                    st.info("Manual transcript unavailable. Running AI Transcription (Whisper)...")
                    res = transcribe_whisper(url_input)
                
                if res:
                    st.subheader("Transcript Output:")
                    st.text_area(label="Copy from here:", value=res, height=400)
                    st.success("Done!")
                else:
                    st.error("Could not extract transcript. Please check the URL.")
        else:
            st.error("Invalid YouTube URL. Please copy-paste again.")
