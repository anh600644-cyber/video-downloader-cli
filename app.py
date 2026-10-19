import streamlit as st
import yt_dlp
import os
import tempfile
import re
import asyncio
from agent_video_downloader import download as avd_download

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** với kiến trúc định tuyến thông minh.")

# Hàm trích xuất link từ văn bản
def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0].strip('.,;()[]"\'') if urls else text.strip()

# Hàm tải Douyin/TikTok bằng avd (không cần cookie)
async def download_douyin_avd(url, tmpdir):
    st.info("⚡ Đang dùng API chuyên dụng (avd) để vượt rào...")
    try:
        # avd sẽ tự động xử lý và tải file về thư mục tmpdir
        result = await avd_download(url, output_dir=tmpdir)
        
        # Tìm file đã tải (thường là .mp4)
        for f in os.listdir(tmpdir):
            if f.endswith(('.mp4', '.mkv', '.webm')):
                return os.path.join(tmpdir, f), f
        raise Exception("Không tìm thấy file video sau khi tải.")
    except Exception as e:
        raise Exception(f"Lỗi avd: {e}")

# Giao diện
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
audio_only = (loai_tai == "Chỉ Audio (MP3)")

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_url(raw_input)
        st.info(f"🔗 Đã nhận diện: {final_url}")
        
        with st.spinner("⏳ Đang xử lý..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    # NHÁNH 1: DOUYIN/TIKTOK -> DÙNG AVD (Không cần cookie)
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        filepath, filename = asyncio.run(download_douyin_avd(final_url, tmpdir))
                        with open(filepath, "rb") as f: file_data = f.read()
                        st.success("✅ Tải thành công qua avd!")
                        st.download_button("💾 Lưu Video", file_data, file_name=filename, mime="video/mp4")
                    
                    # NHÁNH 2: CÁC NỀN TẢNG KHÁC -> DÙNG YT-DLP
                    else:
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
                            st.download_button("💾 Lưu File", file_data, file_name=os.path.basename(filename))
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                st.info("Mẹo: Nếu vẫn lỗi, hãy thử lại sau hoặc kiểm tra xem video có bị giới hạn vùng không.")