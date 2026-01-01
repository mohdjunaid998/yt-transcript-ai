import streamlit as st
import os, re, whisper, yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# Page Setup
st.set_page_config(page_title="Pro YT Transcriber", page_icon="🎯", layout="wide")

# Custom ChatGPT Dark UI
st.markdown("""
    <style>
    .main { background-color: #0b0d11; color: white; }
    .stTextInput > div > div > input { border-radius: 8px; border: 1px solid #444; background: #1f212a; color: white; }
    .stButton > button { background-color: #10a37f; color: white; width: 100%; border-radius: 8px; border: none; height: 3em; }
    .transcript-box { padding: 20px; border-radius: 10px; background: #2d2f39; border-left: 5px solid #10a37f; }
    </style>
    """, unsafe_allow_html=True)

def extract_video_id(url):
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_transcript_via_api(video_id, include_timestamps):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Priority 1: Manually created (English/Hindi)
        # Priority 2: Auto-generated (English/Hindi)
        # Priority 3: Translation to English
        try:
            t = transcript_list.find_transcript(['en', 'hi', 'en-GB', 'en-US'])
        except:
            t = transcript_list.find_generated_transcript(['en', 'hi']).translate('en')
            
        data = t.fetch()
        
        if include_timestamps:
            return "\n".join([f"[{int(i['start']//60):02d}:{int(i['start']%60):02d}] {i['text']}" for i in data])
        else:
            return " ".join([i['text'] for i in data])
    except Exception as e:
        return None

def transcribe_whisper(url):
    # NOTE: If this fails, the server IP is blocked by YT.
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Using 'base' for better accuracy than 'tiny'
        model = whisper.load_model("base")
        result = model.transcribe("temp_audio.mp3")
        
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        return result['text']
    except Exception as e:
        return f"ERROR: YouTube blocked the audio download. Error: {str(e)}"

# --- UI SECTION ---
st.title("🚀 Pro YouTube Transcript AI")
st.write("Extract transcripts manually or using AI (Whisper)")

col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input("", placeholder="Paste YouTube Link (Shorts, Mobile, or Web)...")
with col2:
    st.write("###")
    process_btn = st.button("Extract")

# Options
c1, c2 = st.columns(2)
with c1:
    use_ts = st.checkbox("Show Timestamps", value=True)
with c2:
    st.info("💡 Hint: If manual fails, AI will automatically start.")

if process_btn and url_input:
    v_id = extract_video_id(url_input)
    if not v_id:
        st.error("❌ Invalid YouTube URL")
    else:
        with st.status("🔍 Analyzing Video...", expanded=True) as status:
            # 1. TRY MANUAL API FIRST
            st.write("Checking official transcripts...")
            final_text = get_transcript_via_api(v_id, use_ts)
            
            # 2. IF MANUAL FAILS, USE WHISPER
            if not final_text:
                st.write("Manual not found. Booting up Whisper AI...")
                final_text = transcribe_whisper(url_input)
            
            status.update(label="Process Complete!", state="complete")

        if "ERROR:" in final_text:
            st.error(final_text)
            st.warning("⚠️ Tips: Streamlit Cloud IPs are often blocked by YT. To fix this, upload a 'cookies.txt' to your GitHub repo.")
        else:
            st.subheader("📜 Transcript Results")
            st.text_area("Final Output", final_text, height=500)
            st.download_button("📥 Download Transcript", final_text, file_name=f"transcript_{v_id}.txt")
