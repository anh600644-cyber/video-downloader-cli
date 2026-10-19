import streamlit as st
import yt_dlp
import os
import tempfile
import re
import subprocess

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")
st.markdown("Tích hợp **jiji262/douyin-downloader** cho Douyin, **yt-dlp** cho các nền tảng khác.")

def extract_and_normalize_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    if not urls: return text.strip()
    url = urls[0].strip('.,;()[]"\'')
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match: return f"https://www.douyin.com/video/{match.group(1)}"
    return url

# --- HÀM GỌI CÔNG CỤ DOUYIN-DOWNLOADER ---
def download_douyin_with_tool(url, tmpdir):
    st.info("⚡ Đang dùng công cụ chuyên dụng jiji262/douyin-downloader...")
    
    # Đường dẫn đến thư mục chứa tool đã được clone trong Dockerfile
    tool_dir = "/app/douyin_tool"
    
    # Tùy thuộc vào cách tool hoạt động, nó thường có file run.py hoặc main.py
    # Ở đây ta giả định tool hỗ trợ nhận URL và thư mục đầu ra
    # (Bạn có thể cần điều chỉnh lệnh này nếu tool yêu cầu tham số khác)
    command = [
        "python", f"{tool_dir}/run.py",  # Hoặc main.py tùy cấu trúc dự án
        "-u", url,
        "-o", tmpdir
    ]
    
    try:
        # Chạy tool ngầm và chờ nó tải xong
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            # Nếu lỗi, in ra log để dễ debug
            st.error(f"Log lỗi từ tool: {result.stderr}")
            raise Exception(f"Tool tải Douyin thất bại (Mã lỗi: {result.returncode})")
        
        # Tìm file đã tải trong thư mục tạm
        downloaded_file = None
        for f in os.listdir(tmpdir):
            if f.endswith(('.mp4', '.mkv', '.webm')):
                downloaded_file = os.path.join(tmpdir, f)
                break
                
        if not downloaded_file:
            raise Exception("Không tìm thấy file video sau khi tool chạy xong.")
            
        st.success("✅ Đã tải video Douyin thành công bằng tool chuyên dụng!")
        return downloaded_file, os.path.basename(downloaded_file)
        
    except subprocess.TimeoutExpired:
        raise Exception("Quá trình tải Douyin mất quá nhiều thời gian (Timeout 180s).")
    except Exception as e:
        raise Exception(f"Lỗi khi chạy tool: {e}")

# --- Giao diện ---
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
audio_only = (loai_tai == "Chỉ Audio (MP3)")

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_and_normalize_url(raw_input)
        st.info(f"🔗 Đã nhận diện và chuẩn hóa: {final_url}")
        
        with st.spinner("⏳ Đang xử lý... Vui lòng đợi (Douyin có thể mất 1-2 phút)..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_data = None
                    filename = "video.mp4"
                    
                    # NHÁNH 1: DOUYIN/TIKTOK -> DÙNG TOOL VỪA TẢI VỀ
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        filepath, filename = download_douyin_with_tool(final_url, tmpdir)
                        with open(filepath, "rb") as f: file_data = f.read()
                    
                    # NHÁNH 2: CÁC NỀN TẢNG KHÁC -> DÙNG YT-DLP
                    else:
                        st.info("⚙️ Đang dùng yt-dlp xử lý...")
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
                    
                    # HIỂN THỊ NÚT TẢI
                    if file_data:
                        mime = "audio/mp3" if audio_only else "video/mp4"
                        st.download_button("💾 Lưu File Về Máy", file_data, file_name=os.path.basename(filename), mime=mime)
                        
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                st.info("Mẹo: Nếu tool báo lỗi, hãy thử copy link video dạng ngắn (v.douyin.com...) và dán vào.")