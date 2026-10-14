# Base image
FROM python:3.11-slim

WORKDIR /app

# System dependencies (kuch Python packages ko C compiler chahiye hota hai)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Requirements pehle copy karo - Docker layer caching ke liye (dependencies
# baar baar rebuild nahi hongi jab tak requirements.txt na badle)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki poora project copy karo
COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
