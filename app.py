import streamlit as st
import yt_dlp
import os
import tempfile
import re
import asyncio
from f2.apps.douyin.handler import DouyinHandler

st.set_page_config(page_title="Video Downloader", page_icon="📥", layout="centered")
st.title("📥 Đa Nền Tảng Video Downloader")

def extract_and_normalize_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    if not urls: return text.strip()
    url = urls[0].strip('.,;()[]"\'')
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match: return f"https://www.douyin.com/video/{match.group(1)}"
    return url

async def download_douyin_with_f2(url, tmpdir):
    """Sử dụng thư viện f2 để tải video Douyin."""
    # f2 yêu cầu aweme_id hoặc link video
    handler = DouyinHandler(kwargs={}) 
    
    try:
        # Lấy thông tin video
        video_info = await handler.fetch_one_video(url)
        
        # Lấy link tải không watermark chất lượng cao nhất
        # Cấu trúc của f2 có thể thay đổi, nhưng thường là video.play_addr.url_list
        video_url = video_info.video.play_addr.url_list[0]
        title = re.sub(r'[\\/*?:"<>|]', "", video_info.desc)[:50]
        
        file_path = os.path.join(tmpdir, f"{title}.mp4")
        
        # Tải file bằng requests (f2 có thể cung cấp hàm tải, nhưng dùng requests cho đơn giản)
        import requests
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                
        return file_path, f"{title}.mp4"
    except Exception as e:
        raise Exception(f"Lỗi khi dùng f2: {e}")

# --- Giao diện ---
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
st.markdown("---")
uploaded_cookie = st.file_uploader("Tải lên file cookies.txt (Dự phòng cho YouTube/Bilibili)", type=["txt"])

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_and_normalize_url(raw_input)
        st.info(f"🔗 Đã nhận diện: {final_url}")
        
        with st.spinner("⏳ Đang xử lý..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    # 1. Xử lý Douyin/TikTok bằng f2
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        st.info("⚡ Đang dùng thư viện f2 để tải Douyin/TikTok...")
                        file_path, filename = asyncio.run(download_douyin_with_f2(final_url, tmpdir))
                        with open(file_path, "rb") as f: file_data = f.read()
                        st.download_button("💾 Lưu Video", file_data, file_name=filename, mime="video/mp4")
                    
                    # 2. Xử lý YouTube, Bilibili, v.v. bằng yt-dlp
                    else:
                        st.info("⚙️ Đang dùng yt-dlp xử lý...")
                        ydl_opts = {
                            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                            'quiet': True, 'no_warnings': True,
                            'extractor_args': {'youtube': {'player_client': ['mweb', 'tv', 'android']}}
                        }
                        if uploaded_cookie is not None:
                            cookie_path = os.path.join(tmpdir, "cookies.txt")
                            with open(cookie_path, "wb") as f: f.write(uploaded_cookie.getbuffer())
                            ydl_opts['cookiefile'] = cookie_path

                        if loai_tai == "Video (MP4)":
                            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                        else:
                            ydl_opts['format'] = 'bestaudio/best'
                            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]

                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(final_url, download=True)
                            filename = ydl.prepare_filename(info)
                            if loai_tai == "Chỉ Audio (MP3)": filename = os.path.splitext(filename)[0] + '.mp3'
                            with open(filename, "rb") as f: file_data = f.read()
                            st.download_button("💾 Lưu File", file_data, file_name=os.path.basename(filename))
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                st.info("Mẹo: Nếu vẫn lỗi, hãy thử dùng link rút gọn v.douyin.com hoặc kiểm tra lại file cookies.txt.")