FROM python:3.10-slim

# Cài đặt FFmpeg, Node.js và Git (cần cho avd và yt-dlp)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chạy avd agent-setup để cài đặt các phụ thuộc cần thiết cho avd
RUN avd agent-setup || true

COPY . .

CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0