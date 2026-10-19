import streamlit as st
import yt_dlp
import os
import tempfile
import re
import subprocess
import requests

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")

def extract_and_normalize_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    if not urls: return text.strip()
    url = urls[0].strip('.,;()[]"\'')
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match: return f"https://www.douyin.com/video/{match.group(1)}"
    return url

def get_douyin_video_id(url):
    match = re.search(r'(?:modal_id=|/video/)(\d+)', url)
    return match.group(1) if match else None

# --- Phương án 1: Sử dụng agent-video-downloader (avd) ---
def download_with_avd(url, tmpdir):
    st.info("⚡ Đang dùng avd (Phương án chính)...")
    env = os.environ.copy()
    env["AVD_DOWNLOAD_DIR"] = tmpdir
    try:
        result = subprocess.run(["avd", "download", url], capture_output=True, text=True, timeout=120, env=env)
        if result.returncode != 0:
            raise Exception(f"avd thất bại: {result.stderr}")
        
        for f in os.listdir(tmpdir):
            if f.endswith(('.mp4', '.mkv', '.webm')):
                return os.path.join(tmpdir, f), f
        raise Exception("avd không tạo ra file video.")
    except Exception as e:
        st.warning(f"⚠️ avd thất bại: {e}")
        return None, None

# --- Phương án 2: Gọi API aweme trực tiếp (Fallback) ---
def download_with_aweme(video_id, tmpdir):
    st.info("🔧 Đang thử API aweme (Phương án dự phòng)...")
    api_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://www.douyin.com/'
    }
    try:
        response = requests.get(api_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        
        # Kiểm tra dung lượng file (nếu quá nhỏ là file lỗi)
        if int(response.headers.get('content-length', 0)) < 100000:
            raise Exception("File trả về quá nhỏ hoặc bị chặn.")
            
        file_path = os.path.join(tmpdir, f"{video_id}.mp4")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        st.success("✅ Tải thành công qua API aweme!")
        return file_path, f"{video_id}.mp4"
    except Exception as e:
        st.warning(f"⚠️ API aweme thất bại: {e}")
        return None, None

# --- Giao diện ---
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
audio_only = (loai_tai == "Chỉ Audio (MP3)")

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_and_normalize_url(raw_input)
        st.info(f"🔗 Đã nhận diện: {final_url}")
        
        with st.spinner("⏳ Đang xử lý..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_data = None
                    filename = "video.mp4"
                    
                    if "douyin.com" in final_url:
                        video_id = get_douyin_video_id(final_url)
                        if not video_id:
                            raise Exception("Không thể trích xuất ID video.")
                        
                        # Thử avd trước
                        filepath, filename = download_with_avd(final_url, tmpdir)
                        if filepath:
                            with open(filepath, "rb") as f: file_data = f.read()
                        else:
                            # Nếu avd thất bại, thử API aweme
                            filepath, filename = download_with_aweme(video_id, tmpdir)
                            if filepath:
                                with open(filepath, "rb") as f: file_data = f.read()
                    
                    # Các nền tảng khác dùng yt-dlp
                    if file_data is None:
                        st.info("⚙️ Đang dùng yt-dlp...")
                        ydl_opts = {
                            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                            'quiet': True, 'no_warnings': True,
                            'extractor_args': {'youtube': {'player_client': ['mweb', 'tv', 'android']}}
                        }
                        if audio_only:
                            ydl_opts['format'] = 'bestaudio/best'
                            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
                        else:
                            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                            
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(final_url, download=True)
                            filename = ydl.prepare_filename(info)
                            if audio_only: filename = os.path.splitext(filename)[0] + '.mp3'
                            with open(filename, "rb") as f: file_data = f.read()
                            st.success("✅ Tải thành công qua yt-dlp!")
                    
                    if file_data:
                        mime = "audio/mp3" if audio_only else "video/mp4"
                        st.download_button("💾 Lưu File", file_data, file_name=os.path.basename(filename), mime=mime)
                        
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")