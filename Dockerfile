FROM python:3.10-slim

# 1. Cài đặt các gói hệ thống cần thiết (bao gồm cả các thư viện cho Playwright)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Clone dự án douyin-downloader
RUN git clone https://github.com/jiji262/douyin-downloader.git /app/douyin_tool

# 3. Cài đặt requirements của dự án douyin-downloader
RUN pip install --no-cache-dir -r /app/douyin_tool/requirements.txt

# 4. CÀI ĐẶT TƯỜNG MINH PLAYWRIGHT (Bước còn thiếu)
RUN pip install playwright

# 5. Cài đặt trình duyệt Chromium cho Playwright
RUN python -m playwright install chromium

# 6. Cài đặt requirements của ứng dụng chính
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy code ứng dụng
COPY . .

# 8. Chạy Streamlit
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0