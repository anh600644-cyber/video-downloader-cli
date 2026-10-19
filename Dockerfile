FROM python:3.10-slim

# Cài đặt FFmpeg (ghép video), Node.js (vượt rào YouTube) và các thư viện build cho f2
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0