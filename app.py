import streamlit as st
import yt_dlp
import os
import tempfile

# Cấu hình giao diện Web
st.set_page_config(page_title="Video Downloader", page_icon="📥", layout="centered")

st.title("📥 Đa Nền Tảng Video Downloader")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** và hơn 1000 trang khác.")

# Form nhập liệu
url = st.text_input("🔗 Nhập URL video vào đây:", placeholder="https://www.youtube.com/watch?v=...")
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not url:
        st.warning("Vui lòng nhập URL video trước khi bấm tải!")
    else:
        with st.spinner("⏳ Đang xử lý video... Vui lòng đợi (có thể mất 1-2 phút)..."):
            try:
                # Tạo thư mục tạm để chứa file sau khi tải
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                    }

                    # Cấu hình cho từng loại
                    if loai_tai == "Video (MP4)":
                        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    else:
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]

                    # Thực hiện tải
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)
                        
                        # Nếu tải MP3 thì tên file sẽ thay đổi đuôi
                        if loai_tai == "Chỉ Audio (MP3)":
                            filename = os.path.splitext(filename)[0] + '.mp3'

                        # Đọc file để hiển thị nút tải về
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
                st.error(f"❌ Có lỗi xảy ra: {e}")