import streamlit as st
import yt_dlp
import os
import tempfile
import re

# Cấu hình giao diện Web
st.set_page_config(page_title="Video Downloader", page_icon="📥", layout="centered")

st.title("📥 Đa Nền Tảng Video Downloader")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** và hơn 1000 trang khác.")

# Hàm tự động lọc link từ đoạn văn bản
def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else text

# Dùng text_area thay vì text_input để khung nhập rộng rãi, tự xuống dòng
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản copy từ App):", 
                         placeholder="Dán link hoặc đoạn chia sẻ vào đây...", 
                         height=100)

loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])

# Thêm tùy chọn Cookie (Rất cần cho Douyin/Bilibili)
st.markdown("---")
st.markdown("### 🍪 Tùy chọn nâng cao (Dành cho Douyin/Bilibili)")
uploaded_cookie = st.file_uploader("Tải lên file cookies.txt (nếu video bị lỗi chặn)", type=["txt"])

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video trước khi bấm tải!")
    else:
        # Tự động lọc lấy link thực sự
        url = extract_url(raw_input).strip()
        
        with st.spinner(f"⏳ Đang xử lý video... Vui lòng đợi..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                    }

                    if uploaded_cookie is not None:
                        cookie_path = os.path.join(tmpdir, "cookies.txt")
                        with open(cookie_path, "wb") as f:
                            f.write(uploaded_cookie.getbuffer())
                        ydl_opts['cookiefile'] = cookie_path

                    if loai_tai == "Video (MP4)":
                        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    else:
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)
                        
                        if loai_tai == "Chỉ Audio (MP3)":
                            filename = os.path.splitext(filename)[0] + '.mp3'

                        with open(filename, "rb") as f:
                            file_data = f.read()
                            
                        st.success("✅ Tải thành công! Bấm nút bên dưới để lưu về máy.")
                        
                        mime_type = "video/mp4" if loai_tai == "Video (MP4)" else "audio/mp3"
                        st.download_button(
                            label="💾 Lưu file về máy",
                            data=file_data,
                            file_name=os.path.basename(filename),
                            mime=mime_type
                        )
            except Exception as e:
                # Rút gọn thông báo lỗi để không hiện đoạn văn dài ngoằng
                error_msg = str(e)
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                st.error(f"❌ Có lỗi xảy ra: {error_msg}\n\n*Gợi ý: Hãy kiểm tra lại link, hoặc tải file cookies.txt lên nếu bị chặn.*")