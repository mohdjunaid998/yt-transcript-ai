import streamlit as st
import os, re, whisper, yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ultimate YT Transcript AI", page_icon="🚀", layout="wide")

# --- UI STYLING (ChatGPT Style) ---
st.markdown("""
    <style>
    .main { background-color: #0b0d11; color: white; }
    .stTextInput > div > div > input { border-radius: 10px; border: 1px solid #444; background: #1f212a; color: white; }
    .stButton > button { background-color: #10a37f; color: white; border-radius: 10px; height: 3em; font-weight: bold; }
    .transcript-container { padding: 20px; border-radius: 15px; background-color: #1f212a; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---

def extract_video_id(url):
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_manual_transcript(v_id, use_ts):
    """YouTube API se direct transcript nikalna (Fast & Safe)"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
        # 1. Pehle English ya Hindi manual dhundo, nahi toh auto-generated
        try:
            t = transcript_list.find_transcript(['en', 'hi', 'en-GB', 'en-US'])
        except:
            # 2. Agar foreign language hai toh auto-translate to English
            t = transcript_list.find_transcript(transcript_list._manually_created_transcripts.keys() or transcript_list._generated_transcripts.keys())
            if t.language_code != 'en':
                t = t.translate('en')
        
        data = t.fetch()
        if use_ts:
            return "\n".join([f"[{int(i['start']//60):02d}:{int(i['start']%60):02d}] {i['text']}" for i in data])
        return " ".join([i['text'] for i in data])
    except:
        return None

def transcribe_whisper(url):
    """Whisper AI se audio transcript nikalna (With Cookie Support)"""
    cookie_file = "cookies.txt" if os.path.exists("cookies.txt") else None
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
        return f"❌ AI Error: YouTube block bypass failed. Please update cookies.txt or use a video with subtitles. Details: {str(e)}"

# --- APP UI ---
st.title("🎬 Ultimate YouTube Transcript AI")
st.write("Extract every word from any video using API & AI.")

# Input Layout
url_input = st.text_input("Paste YouTube Link (Normal, Shorts, or Mobile):")
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    use_timestamps = st.checkbox("Include Timestamps", value=True)
with col_opt2:
    st.info("💡 Pro Tip: If official subtitles exist, we use them first.")

if st.button("Generate Transcript ✨"):
    if not url_input:
        st.warning("Please enter a URL first!")
    else:
        v_id = extract_video_id(url_input)
        if not v_id:
            st.error("Invalid YouTube URL!")
        else:
            with st.status("🚀 Processing Video...", expanded=True) as status:
                # Step 1: Check YouTube Subtitles
                st.write("Searching YouTube Database...")
                final_text = get_manual_transcript(v_id, use_timestamps)
                
                # Step 2: Fallback to Whisper AI
                if not final_text:
                    st.write("Manual transcript unavailable. Initializing AI Whisper...")
                    final_text = transcribe_whisper(url_input)
                
                status.update(label="Transcript Ready!", state="complete")

            # Final Display
            st.subheader("📜 Transcript Result")
            if "❌" in final_text:
                st.error(final_text)
            else:
                st.text_area("Final Output", final_text, height=450)
                st.download_button("📥 Download Text", final_text, file_name=f"transcript_{v_id}.txt")
                st.success("Success! Copy or Download the text above.")
