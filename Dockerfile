FROM python:3.10-slim

# Avoid interactive prompts during builds
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "web_app.py"]  # Or change to gunicorn if using Flask API
