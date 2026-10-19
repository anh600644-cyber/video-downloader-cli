FROM python:3.10-slim

# Cài đặt các thư viện hệ thống, FFmpeg, Node.js và Git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. TẢI DỰ ÁN DOUYIN-DOWNLOADER VỀ MÁY CHỦ
RUN git clone https://github.com/jiji262/douyin-downloader.git /app/douyin_tool

# 2. Cài đặt thư viện cho dự án đó
RUN pip install --no-cache-dir -r /app/douyin_tool/requirements.txt

# 3. Cài đặt trình duyệt ảo (Playwright) cho dự án đó dùng để vượt rào
RUN playwright install chromium
# Cài đặt các thư viện phụ thuộc của Playwright cho Linux
RUN playwright install-deps

# 4. Cài đặt thư viện cho app của bạn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code của bạn vào
COPY . .

# Chạy web Streamlit
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0