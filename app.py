import streamlit as st
import yt_dlp
import os
import tempfile
import re
import requests

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** với kiến trúc định tuyến thông minh.")

# Hàm trích xuất link từ văn bản
def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0].strip('.,;()[]"\'') if urls else text.strip()

# Hàm lấy ID video từ link Douyin
def get_douyin_video_id(url):
    # Xử lý link dạng modal_id hoặc /video/
    match = re.search(r'(?:modal_id=|/video/)(\d+)', url)
    return match.group(1) if match else None

# Hàm tải Douyin qua API aweme (không cần cookie)
def download_douyin_via_aweme(video_id, tmpdir):
    api_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
    st.info(f"⚡ Đang gọi API Douyin (aweme) cho video ID: {video_id}...")
    
    try:
        # Gửi request để lấy link video
        response = requests.get(api_url, allow_redirects=True, timeout=15)
        response.raise_for_status()
        
        # API này thường trả về file trực tiếp, không cần lấy link từ JSON
        file_path = os.path.join(tmpdir, f"{video_id}.mp4")
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        st.success("✅ Đã tải video qua API aweme!")
        return file_path, f"{video_id}.mp4"
    except Exception as e:
        raise Exception(f"Lỗi API aweme: {e}")

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
                    # NHÁNH 1: DOUYIN/TIKTOK -> DÙNG API AWEME
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        video_id = get_douyin_video_id(final_url)
                        if not video_id:
                            raise Exception("Không thể trích xuất ID video từ link Douyin này.")
                        
                        filepath, filename = download_douyin_via_aweme(video_id, tmpdir)
                        with open(filepath, "rb") as f: file_data = f.read()
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
                st.info("Mẹo: Nếu là YouTube, hãy thử tải file cookies.txt lên. Nếu là Douyin, hãy kiểm tra lại link video.")