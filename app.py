import streamlit as st
import yt_dlp
import os
import tempfile
import re
import asyncio
import requests
from f2.apps.douyin.handler import DouyinHandler

st.set_page_config(page_title="Video Downloader Pro", page_icon="📥", layout="centered")
st.title("📥 Video Downloader Pro")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** với kiến trúc định tuyến thông minh.")

# Hàm trích xuất và chuẩn hóa link
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

# --- HÀM MỚI: Chuyển đổi file cookies.txt (Netscape) thành chuỗi cookie ---
def parse_netscape_cookie(cookie_text):
    cookies = []
    for line in cookie_text.splitlines():
        line = line.strip()
        # Bỏ qua dòng trống và dòng comment
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            name = parts[5]
            value = parts[6]
            cookies.append(f"{name}={value}")
    return "; ".join(cookies)

# Hàm tải video Douyin bằng f2
async def download_douyin_with_f2(aweme_id, tmpdir, cookie_string=None):
    st.info("⚡ Đang dùng thư viện f2 chuyên dụng để xử lý Douyin...")
    
    kwargs = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
            "Referer": "https://www.douyin.com/",
        },
        "proxies": {"http://": None, "https://": None},
    }
    
    # Gán chuỗi cookie đã được làm sạch vào cấu hình
    if cookie_string:
        kwargs["cookie"] = cookie_string

    try:
        handler = DouyinHandler(kwargs)
        video_info = await handler.fetch_one_video(aweme_id=aweme_id)
        
        # Trích xuất link video
        video_url = None
        if hasattr(video_info, 'video') and video_info.video:
            if hasattr(video_info.video, 'play_addr') and video_info.video.play_addr:
                video_url = video_info.video.play_addr.url_list[0]
            elif hasattr(video_info.video, 'bit_rate') and video_info.video.bit_rate:
                video_url = video_info.video.bit_rate[0].play_addr.url_list[0]
        
        if not video_url:
            raise Exception("Không thể trích xuất link video từ dữ liệu của f2.")

        title = getattr(video_info, 'desc', f"douyin_{aweme_id}")
        title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        
        file_path = os.path.join(tmpdir, f"{title}.mp4")
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
                    
        st.success("✅ Đã tải video Douyin thành công qua f2!")
        return file_path, f"{title}.mp4"
        
    except Exception as e:
        raise Exception(f"Lỗi f2: {e}")

# --- Giao diện ---
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản chia sẻ):", height=100)
loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])
audio_only = (loai_tai == "Chỉ Audio (MP3)")

st.markdown("---")
uploaded_cookie = st.file_uploader("Tải lên file cookies.txt (Rất quan trọng cho Douyin/YouTube)", type=["txt"])

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video!")
    else:
        final_url = extract_and_normalize_url(raw_input)
        st.info(f"🔗 Đã nhận diện và chuẩn hóa: {final_url}")
        
        with st.spinner("⏳ Đang xử lý..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_data = None
                    filename = "video.mp4"
                    
                    # Đọc và xử lý nội dung cookie nếu có
                    cookie_string = None
                    if uploaded_cookie is not None:
                        raw_cookie_text = uploaded_cookie.getvalue().decode("utf-8")
                        cookie_string = parse_netscape_cookie(raw_cookie_text)
                        st.info(f"🍪 Đã nạp và xử lý cookie (độ dài: {len(cookie_string)} ký tự)")

                    # NHÁNH 1: DOUYIN/TIKTOK -> DÙNG F2
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        video_id = get_douyin_video_id(final_url)
                        if not video_id:
                            raise Exception("Không thể trích xuất ID video từ link này.")
                        
                        filepath, filename = asyncio.run(download_douyin_with_f2(video_id, tmpdir, cookie_string))
                        with open(filepath, "rb") as f: file_data = f.read()
                    
                    # NHÁNH 2: CÁC NỀN TẢNG KHÁC -> DÙNG YT-DLP
                    else:
                        st.info("⚙️ Đang dùng yt-dlp xử lý...")
                        ydl_opts = {
                            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                            'quiet': True, 'no_warnings': True,
                            'extractor_args': {'youtube': {'player_client': ['mweb', 'tv', 'android']}}
                        }
                        
                        # Nếu có cookie, lưu ra file tạm để yt-dlp sử dụng
                        if uploaded_cookie is not None:
                            cookie_path = os.path.join(tmpdir, "cookies.txt")
                            with open(cookie_path, "wb") as f: f.write(uploaded_cookie.getbuffer())
                            ydl_opts['cookiefile'] = cookie_path

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
                st.info("Mẹo: Nếu lỗi f2 vẫn tiếp diễn, hãy thử dùng 'Get cookies.txt LOCALLY' để xuất lại cookie mới và đảm bảo bạn đã đăng nhập Douyin.")