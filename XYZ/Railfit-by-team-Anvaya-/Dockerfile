FROM python:3.9-slim

WORKDIR /app

# System dependencies for OCR/barcode
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY backend/ ./backend/
COPY ai_models/ ./ai_models/
COPY database/ ./database/

EXPOSE 5000

CMD ["python", "backend/app.py"]
