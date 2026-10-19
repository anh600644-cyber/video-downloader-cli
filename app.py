import streamlit as st
import yt_dlp
import os
import tempfile
import re
import requests
import time

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")
st.markdown("Hệ thống tự động định tuyến: **Siêu tốc cho Douyin/TikTok**, **Mạnh mẽ cho YouTube/Bilibili**.")

# --- CẤU HÌNH MEDIA-PARSER ---
# Nếu bạn tự host Media-Parser, hãy điền link vào đây (VD: http://localhost:8051/api/v1/parse)
# Nếu để trống, code sẽ tự động dùng phương án dự phòng yt-dlp.
MEDIA_PARSER_API_URL = os.getenv("MEDIA_PARSER_API_URL", "")

# --- CÁC HÀM XỬ LÝ ---
def extract_and_normalize_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    if not urls: return text.strip()
    url = urls[0].strip('.,;()[]"\'')
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match: return f"https://www.douyin.com/video/{match.group(1)}"
    return url

def download_file(url, filepath):
    """Tải file từ link trực tiếp với thanh tiến trình."""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_length = int(r.headers.get('content-length', 0))
        with open(filepath, 'wb') as f:
            if total_length == 0:
                f.write(r.content)
            else:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    return filepath

def parse_with_media_parser(url):
    """Gọi API Media-Parser (nếu có cấu hình)."""
    if not MEDIA_PARSER_API_URL:
        return None
        
    try:
        response = requests.get(MEDIA_PARSER_API_URL, params={"url": url}, timeout=15)
        data = response.json()
        if data.get("retcode") == 200 and data.get("succ"):
            return data["data"]
    except Exception as e:
        st.warning(f"⚠️ Media-Parser không phản hồi ({e}). Chuyển sang dự phòng...")
    return None

def process_with_ytdlp(url, tmpdir, audio_only, cookie_path=None):
    """Xử lý tải bằng yt-dlp (Dự phòng)."""
    ydl_opts = {
        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
        'quiet': True, 
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['mweb', 'tv', 'android']}}
    }
    
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    if audio_only:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if audio_only:
            filename = os.path.splitext(filename)[0] + '.mp3'
        return filename

# --- GIAO DIỆN ---
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
audio_only = (loai_tai == "Chỉ Audio (MP3)")

st.markdown("---")
uploaded_cookie = st.file_uploader("Tải lên file cookies.txt (Dự phòng cho YouTube/Bilibili)", type=["txt"])

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_and_normalize_url(raw_input)
        st.info(f"🔗 Đã nhận diện: {final_url}")
        
        with st.spinner("⏳ Hệ thống đang phân tích và tải video..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_data = None
                    filename = "video.mp4"
                    mime_type = "video/mp4" if not audio_only else "audio/mp3"

                    # BƯỚC 1: THỬ DÙNG MEDIA-PARSER (Nếu được cấu hình và là link Douyin/TikTok)
                    mp_data = None
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        if MEDIA_PARSER_API_URL:
                            st.info("⚡ Đang dùng Media-Parser (Tốc độ cao)...")
                            mp_data = parse_with_media_parser(final_url)
                    
                    if mp_data:
                        # Nếu Media-Parser thành công
                        download_url = mp_data.get("audio_url") if audio_only else mp_data.get("video_url")
                        title = re.sub(r'[\\/*?:"<>|]', "", mp_data.get("title", "video"))[:50]
                        
                        if download_url:
                            ext = ".mp3" if audio_only else ".mp4"
                            filename = title + ext
                            filepath = os.path.join(tmpdir, filename)
                            st.info("📥 Đang tải file từ link trực tiếp...")
                            download_file(download_url, filepath)
                            
                            with open(filepath, "rb") as f:
                                file_data = f.read()
                            st.success("✅ Tải thành công qua Media-Parser!")
                    
                    # BƯỚC 2: DỰ PHÒNG BẰNG YT-DLP
                    if file_data is None:
                        st.info("⚙️ Đang dùng hệ thống dự phòng (yt-dlp)...")
                        
                        cookie_path = None
                        if uploaded_cookie is not None:
                            cookie_path = os.path.join(tmpdir, "cookies.txt")
                            with open(cookie_path, "wb") as f: f.write(uploaded_cookie.getbuffer())
                            st.info("🍪 Đã nạp cookies.txt")

                        filepath = process_with_ytdlp(final_url, tmpdir, audio_only, cookie_path)
                        filename = os.path.basename(filepath)
                        with open(filepath, "rb") as f:
                            file_data = f.read()
                        st.success("✅ Tải thành công qua yt-dlp!")

                    # HIỂN THỊ NÚT TẢI XUỐNG
                    if file_data:
                        st.download_button(
                            label="💾 Lưu File Về Máy",
                            data=file_data,
                            file_name=filename,
                            mime=mime_type
                        )
                        
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                st.info("Mẹo: Nếu là YouTube, hãy thử tải file cookies.txt lên. Nếu là Douyin, link có thể đã bị xóa hoặc cần đăng nhập.")