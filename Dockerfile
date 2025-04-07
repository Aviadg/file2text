FROM python:3.11-slim

# Install system dependencies including Tesseract OCR and poppler-utils (for pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libreoffice \
    libgl1 \
    libglib2.0-0 \
    curl \
    wget \
    git \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Environment variables for Docling
ENV GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no"
ENV HF_HOME=/tmp/
ENV TORCH_HOME=/tmp/
ENV OMP_NUM_THREADS=4

WORKDIR /app

# Copy requirements file and install dependencies
COPY app/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Download Docling models
RUN docling-tools models download

# Create uploads directory
RUN mkdir -p /app/uploads

# Copy application code
COPY app /app/

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]