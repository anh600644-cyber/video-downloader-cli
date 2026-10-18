import streamlit as st
import yt_dlp
import os
import tempfile
import re
import asyncio
from playwright.async_api import async_playwright

# ... (Giữ nguyên phần cấu hình giao diện và hàm extract_url) ...

# Hàm chuyên biệt để lấy link video Douyin bằng Playwright
async def get_douyin_direct_url(video_url):
    async with async_playwright() as p:
        # Khởi chạy trình duyệt headless
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Biến để lưu trữ link video bắt được
        video_link = None
        
        # Hàm xử lý khi có response từ API
        async def handle_response(response):
            nonlocal video_link
            # Tìm API chi tiết video của Douyin
            if "/aweme/v1/web/aweme/detail/" in response.url:
                try:
                    json_data = await response.json()
                    # Trích xuất link playAddr
                    video_link = json_data["aweme_detail"]["video"]["play_addr"]["url_list"][0]
                except Exception:
                    pass
        
        # Đăng ký hàm xử lý response
        page.on("response", handle_response)
        
        try:
            # Mở trang video
            await page.goto(video_url, wait_until="networkidle", timeout=30000)
            # Đợi thêm một chút để API kịp trả về
            await asyncio.sleep(2)
        except Exception as e:
            st.error(f"Lỗi khi mở trang Douyin: {e}")
        finally:
            await browser.close()
        
        return video_link

# ... (Phần giao diện Streamlit) ...

if st.button("🚀 Bắt đầu tải", type="primary"):
    if not raw_input:
        st.warning("Vui lòng nhập link video trước khi bấm tải!")
    else:
        url = extract_url(raw_input).strip()
        
        with st.spinner("⏳ Đang xử lý video..."):
            try:
                final_download_url = url # Mặc định dùng link gốc
                
                # Nếu là link Douyin, dùng Playwright để lấy link trực tiếp
                if "douyin.com" in url:
                    st.info("Đã phát hiện link Douyin, đang dùng trình duyệt ảo để vượt rào...")
                    direct_url = asyncio.run(get_douyin_direct_url(url))
                    if direct_url:
                        final_download_url = direct_url
                        st.success("Đã lấy được link video trực tiếp!")
                    else:
                        st.warning("Không thể lấy link trực tiếp, sẽ thử tải bằng cách thông thường.")

                # Tiến hành tải với yt-dlp (dùng link gốc hoặc link đã trích xuất)
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    }
                    
                    # Nếu là link trực tiếp, có thể cần thêm header Referer
                    if "douyin.com" in url:
                        ydl_opts['http_headers'] = {'Referer': 'https://www.douyin.com/'}

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(final_download_url, download=True)
                        filename = ydl.prepare_filename(info)
                        
                        with open(filename, "rb") as f:
                            file_data = f.read()
                            
                        st.success("✅ Tải thành công! Bấm nút bên dưới để lưu về máy.")
                        st.download_button(
                            label="💾 Lưu file về máy",
                            data=file_data,
                            file_name=os.path.basename(filename),
                            mime="video/mp4"
                        )
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra: {e}")