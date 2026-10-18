import streamlit as st
import yt_dlp
import os
import tempfile
import re
import asyncio
from playwright.async_api import async_playwright

# Cấu hình giao diện Web
st.set_page_config(page_title="Video Downloader", page_icon="📥", layout="centered")

st.title("📥 Đa Nền Tảng Video Downloader")
st.markdown("Hỗ trợ **YouTube, Bilibili, TikTok, Douyin** và hơn 1000 trang khác.")

# Hàm tự động lọc link từ đoạn văn bản (Bắt trọn mọi loại link)
def extract_url(text):
    # Tìm chuỗi bắt đầu bằng http/https và kéo dài đến khi gặp dấu cách hoặc xuống dòng
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else text

# GIAO DIỆN NHẬP LIỆU
raw_input = st.text_area("🔗 Nhập URL (hoặc dán cả đoạn văn bản copy từ App):", 
                         placeholder="Dán link hoặc đoạn chia sẻ vào đây...", 
                         height=100)

loai_tai = st.radio("Chọn định dạng tải:", ["Video (MP4)", "Chỉ Audio (MP3)"])

st.markdown("---")
st.markdown("### 🍪 Tùy chọn nâng cao (Dành cho Douyin/Bilibili)")
uploaded_cookie = st.file_uploader("Tải lên file cookies.txt (nếu video bị lỗi chặn)", type=["txt"])


# Hàm chuyên biệt để lấy link video Douyin bằng Playwright
async def get_douyin_direct_url(video_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Giả lập User-Agent của Chrome để không bị Douyin chặn
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        video_link = None
        
        # Hàm hứng các gói tin API trả về từ Douyin
        async def handle_response(response):
            nonlocal video_link
            if "/aweme/v1/web/aweme/detail/" in response.url:
                try:
                    json_data = await response.json()
                    if "aweme_detail" in json_data and json_data["aweme_detail"]:
                        video_link = json_data["aweme_detail"]["video"]["play_addr"]["url_list"][0]
                except Exception:
                    pass
        
        page.on("response", handle_response)
        
        try:
            # Mở trang web (không cần đợi load hết mọi thứ, chỉ cần load DOM)
            await page.goto(video_url, wait_until="domcontentloaded", timeout=20000)
            # Đợi tối đa 5 giây để API kịp gọi
            for _ in range(10):
                if video_link:
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            pass # Bỏ qua lỗi timeout nếu đã lấy được link
        finally:
            await browser.close()
        
        return video_link


# NÚT BẤM VÀ XỬ LÝ TẢI
if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video trước khi bấm tải!")
    else:
        # Tự động bóc tách link từ đoạn văn bản
        url = extract_url(raw_input).strip()
        st.info(f"🔗 Đã nhận diện link: {url}")
        
        with st.spinner("⏳ Đang xử lý video..."):
            try:
                final_download_url = url
                
                # Nếu là link Douyin, dùng Playwright để vượt rào
                if "douyin.com" in url:
                    st.info("Đã phát hiện link Douyin, đang dùng trình duyệt ảo để vượt rào...")
                    direct_url = asyncio.run(get_douyin_direct_url(url))
                    if direct_url:
                        final_download_url = direct_url
                        st.success("Đã lấy được link video trực tiếp!")
                    else:
                        st.warning("Không thể lấy link trực tiếp từ API, sẽ thử tải bằng cách thông thường...")

                # Tiến hành tải bằng yt-dlp
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                    }

                    # Nếu có upload cookie
                    if uploaded_cookie is not None:
                        cookie_path = os.path.join(tmpdir, "cookies.txt")
                        with open(cookie_path, "wb") as f:
                            f.write(uploaded_cookie.getbuffer())
                        ydl_opts['cookiefile'] = cookie_path

                    # Cấu hình format
                    if loai_tai == "Video (MP4)":
                        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    else:
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]

                    # Thêm Referer cho Douyin để tránh lỗi 403
                    if "douyin.com" in url:
                        ydl_opts['http_headers'] = {'Referer': 'https://www.douyin.com/'}

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(final_download_url, download=True)
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
                st.error(f"❌ Có lỗi xảy ra: {e}\n\n*Gợi ý: Nếu là video Douyin bị chặn, hãy xuất file cookies.txt từ trình duyệt và upload lên đây.*")