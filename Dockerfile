# Dùng Python bản rút gọn
FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết cho Playwright
RUN apt-get update && apt-get install -y \
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

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# LỆNH QUAN TRỌNG NHẤT: Tải trình duyệt Chromium cho Playwright
RUN playwright install chromium

# Copy code
COPY . .

# Chạy web
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0