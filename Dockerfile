# Sử dụng image chính thức của Playwright, đã có sẵn các thư viện hệ thống cần thiết
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# BƯỚC QUAN TRỌNG NHẤT: Cài đặt trình duyệt Chromium cho Playwright
# Lệnh này sẽ tải và cài đặt trình duyệt, đảm bảo nó tương thích với HĐH trong container
RUN playwright install chromium

# Copy toàn bộ code còn lại
COPY . .

# Lệnh khởi chạy Streamlit
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0