import streamlit as st
import yt_dlp
import os
import tempfile
import re
import requests

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

def download_douyin_via_api(url, tmpdir):
    # Danh sách các API dự phòng (thử lần lượt)
    api_endpoints = [
        f"https://tikwm.com/api/?url={url}&hd=1", # API 1: tikwm (ổn định)
        f"https://api.douyin.wtf/api/hybrid/video_data?url={url}&minimal=true", # API 2: douyin.wtf
        # Có thể thêm các API khác từ kết quả tìm kiếm nếu cần
    ]
    
    last_error = None
    for api_url in api_endpoints:
        try:
            st.info(f"🔄 Đang thử API: {api_url.split('/')[2]}...")
            res = requests.get(api_url, timeout=15).json()
            
            video_url = None
            title = "video_douyin"
            
            # Xử lý response của tikwm.com
            if "tikwm.com" in api_url:
                if res.get("code") == 0 and res.get("data"):
                    video_url = res["data"].get("hdplay") or res["data"].get("play")
                    title = res["data"].get("title", "video_douyin")
            # Xử lý response của douyin.wtf
            elif "douyin.wtf" in api_url:
                if res.get("code") == 200:
                    data = res.get("data", {})
                    video_data = data.get("video_data", {})
                    video_url = video_data.get("nwm_video_url_HQ") or video_data.get("nwm_video_url")
                    title = data.get("desc", "video_douyin")
            
            if video_url:
                title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
                file_path = os.path.join(tmpdir, f"{title}.mp4")
                with requests.get(video_url, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                st.success(f"✅ Tải thành công qua API {api_url.split('/')[2]}!")
                return file_path, f"{title}.mp4"
            else:
                last_error = f"API {api_url.split('/')[2]} không trả về link video."
                st.warning(last_error)
                
        except Exception as e:
            last_error = f"Lỗi khi gọi {api_url.split('/')[2]}: {e}"
            st.warning(last_error)
            continue # Thử API tiếp theo
            
    raise Exception(f"Tất cả API đều thất bại. Lỗi cuối: {last_error}")

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
                    # 1. Xử lý Douyin/TikTok
                    if "douyin.com" in final_url or "tiktok.com" in final_url:
                        st.info("⚡ Đang dùng API chuyên dụng tải Douyin/TikTok...")
                        file_path, filename = download_douyin_via_api(final_url, tmpdir)
                        with open(file_path, "rb") as f: file_data = f.read()
                        st.download_button("💾 Lưu Video", file_data, file_name=filename, mime="video/mp4")
                    
                    # 2. Xử lý YouTube, Bilibili, v.v.
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
                            st.success("✅ Tải thành công!")
                            st.download_button("💾 Lưu File", file_data, file_name=os.path.basename(filename))
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                st.info("Mẹo: Nếu vẫn lỗi Douyin, hãy thử dùng link rút gọn `v.douyin.com/...` thay vì link `modal_id`.")