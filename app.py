import streamlit as st
import yt_dlp
import os
import tempfile
import re
import requests

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** với kiến trúc định tuyến thông minh.")

def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0].strip('.,;()[]"\'') if urls else text.strip()

def get_douyin_video_id(url):
    match = re.search(r'(?:modal_id=|/video/)(\d+)', url)
    return match.group(1) if match else None

def download_douyin_via_aweme(video_id, tmpdir):
    # Thêm User-Agent giả lập điện thoại để API trả về file thật
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.douyin.com/'
    }
    api_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
    st.info(f"⚡ Đang gọi API Douyin (aweme)...")
    
    try:
        response = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        response.raise_for_status()
        
        # KIỂM TRA DUNG LƯỢNG FILE (Nếu < 100KB thì chắc chắn là file lỗi/HTML)
        if len(response.content) < 100000:
            raise Exception("File tải về quá nhỏ hoặc bị chặn (0 KB).")
            
        file_path = os.path.join(tmpdir, f"{video_id}.mp4")
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        st.success("✅ Đã tải video qua API aweme!")
        return file_path, f"{video_id}.mp4"
    except Exception as e:
        st.warning(f"⚠️ API aweme thất bại: {e}. Chuyển sang dùng yt-dlp + Cookie...")
        return None, None

raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
audio_only = (loai_tai == "Chỉ Audio (MP3)")

st.markdown("---")
uploaded_cookie = st.file_uploader("Tải lên file cookies.txt (Rất quan trọng cho Douyin/YouTube)", type=["txt"])

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_url(raw_input)
        st.info(f"🔗 Đã nhận diện: {final_url}")
        
        with st.spinner("⏳ Đang xử lý..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_data = None
                    filename = "video.mp4"
                    
                    # BƯỚC 1: THỬ API AWEME
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        video_id = get_douyin_video_id(final_url)
                        if video_id:
                            filepath, filename = download_douyin_via_aweme(video_id, tmpdir)
                            if filepath:
                                with open(filepath, "rb") as f: file_data = f.read()
                    
                    # BƯỚC 2: FALLBACK SANG YT-DLP (NẾU API LỖI)
                    if file_data is None:
                        st.info("⚙️ Đang dùng yt-dlp (với Cookie) để tải...")
                        ydl_opts = {
                            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                            'quiet': True, 'no_warnings': True,
                            'extractor_args': {'youtube': {'player_client': ['mweb', 'tv', 'android']}}
                        }
                        
                        if uploaded_cookie is not None:
                            cookie_path = os.path.join(tmpdir, "cookies.txt")
                            with open(cookie_path, "wb") as f: f.write(uploaded_cookie.getbuffer())
                            ydl_opts['cookiefile'] = cookie_path
                            st.info("🍪 Đã nạp cookies.txt")

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
                st.info("Mẹo: Hãy chắc chắn bạn đã tải file cookies.txt lên và thử lại.")