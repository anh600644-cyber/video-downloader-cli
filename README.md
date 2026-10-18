# Video Downloader CLI (Bilibili · Douyin · TikTok · YouTube)

Công cụ dòng lệnh đa nền tảng giúp tải video từ **Bilibili**, **Douyin**, **TikTok**, **YouTube** và hơn 1000 trang khác, dựa trên sức mạnh của [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

---

## 📋 Yêu cầu hệ thống

| Thành phần | Bắt buộc | Ghi chú |
|---|---|---|
| **Python** | ≥ 3.8 | [Tải tại đây](https://www.python.org/downloads/) |
| **pip** | ≥ 20.0 | Thường đi kèm Python |
| **FFmpeg** | ✅ Bắt buộc | Cần để hợp nhất video/audio, chuyển đổi định dạng, nhúng phụ đề |

### Cài đặt FFmpeg

- **Windows:** Tải từ [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), giải nén và thêm thư mục `bin` vào `PATH`.
- **macOS:** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
- **Fedora:** `sudo dnf install ffmpeg`

Kiểm tra: `ffmpeg -version`

---

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/your-username/video-downloader-cli.git
cd video-downloader-cli