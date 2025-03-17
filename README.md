# File2Text

<p align="center">
  <img src="https://via.placeholder.com/150x150?text=file2text" alt="file2text Logo">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Compatible-2496ED.svg?style=flat&logo=docker" alt="Docker"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.103.1-009688.svg?style=flat&logo=fastapi" alt="FastAPI"></a>
  <a href="https://n8n.io/"><img src="https://img.shields.io/badge/n8n-Integration-FF6D00.svg?style=flat" alt="n8n"></a>
</p>

**file2text** is a powerful, containerized REST API service for extracting text from various document formats, optimized for integration with LLMs, n8n workflows, and other automation tools.

## 🚀 Features

- **Multi-format Support**: Extract text from PDFs, DOC/DOCX, and various image formats
- **Smart OCR Processing**: Automatically uses OCR for scanned documents and images
- **Multiple Input Methods**: Upload files directly or send base64-encoded data
- **Batch Processing**: Process multiple files in a single request
- **LLM-Ready Output**: Clean, structured JSON responses ready for LLM processing
- **n8n Integration**: Seamless integration with n8n workflows
- **Docker Containerized**: Easy deployment in any environment
- **Multilingual Support**: Configurable for multiple languages including English and Hebrew

## 🔧 Technologies

- **FastAPI**: High-performance Python web framework
- **Tesseract OCR**: Optical Character Recognition for images and scanned PDFs
- **PyPDF2 & pdf2image**: PDF processing and conversion
- **python-docx**: Microsoft Word document processing
- **Docker & Docker Compose**: Containerization and orchestration

## 📋 Requirements

- Docker & Docker Compose
- 2GB+ RAM recommended for optimal OCR performance
- Sufficient disk space for temporary file processing

## 🔍 How It Works

file2text utilizes a combination of direct text extraction and OCR technologies to process your documents:

1. **PDFs**: First attempts direct text extraction, falls back to OCR for scanned documents
2. **DOC/DOCX**: Extracts text from Microsoft Word documents (including legacy .doc via LibreOffice)
3. **Images**: Uses Tesseract OCR with image pre-processing for optimal text recognition
4. **All extracted text** is returned in clean, structured JSON format

## 📦 Installation & Setup

### Quick Start with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/file2text.git
   cd file2text
   ```

2. Start the service:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at http://localhost:8000

### Build from Source

1. Clone the repository
2. Customize the Dockerfile or docker-compose.yml if needed
3. Build and start the service:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## 📚 API Documentation

Once the service is running, access the interactive API documentation at http://localhost:8000/docs

### Endpoints

- `GET /` - Service status check
- `POST /extract-text/` - Extract text from uploaded file
- `POST /batch-extract/` - Process multiple uploaded files
- `POST /extract-text-base64/` - Extract text from base64-encoded file

### Example: Extract Text from a PDF

```bash
curl -X POST \
  http://localhost:8000/extract-text/ \
  -H "accept: application/json" \
  -F "file=@/path/to/your/document.pdf"
```

### Response Format

```json
{
  "filename": "document.pdf",
  "text": "This is the extracted text content from the PDF file...",
  "file_type": "pdf"
}
```

## 🔌 Integrating with n8n

file2text is optimized for use with n8n workflows. Here's how to connect:

1. In n8n, add an HTTP Request node
2. Configure it to send a POST request to `http://yourhostip:8000/extract-text-base64/`
3. Set the body to JSON with this structure:
   ```json
   {
     "filename": "{{$node[\"Read Binary File\"].binary.data.fileName}}",
     "content_type": "{{$node[\"Read Binary File\"].binary.data.mimeType}}",
     "base64_data": "{{$binary.data.toString('base64')}}"
   }
   ```

### n8n Docker Network Configuration

If running both n8n and file2text in Docker containers, use one of these approaches:

1. Use the host's IP address in the HTTP Request URL:
   ```
   http://YOUR_HOST_IP:8000/extract-text-base64/
   ```

2. Create a shared Docker network:
   ```bash
   docker network create shared-network
   ```
   
   Then update both docker-compose files to use this network and reference the service by name:
   ```
   http://text-extraction-api:8000/extract-text-base64/
   ```

## 📂 Project Structure

```
file2text/
│
├── docker-compose.yml          # Main docker-compose configuration
├── Dockerfile                  # Docker image configuration
│
├── app/                        # Main application directory
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI main application file
│   │
│   └── extractors/             # Package for text extraction modules
│       ├── __init__.py         # Package initialization
│       ├── pdf_extractor.py    # PDF extraction module
│       ├── doc_extractor.py    # DOC/DOCX extraction module
│       └── image_extractor.py  # Image extraction module
│
└── uploads/                    # Directory for temporary file uploads
```

## 🚩 Language Support 

By default, file2text is configured for English language documents. For additional languages:

1. Update the Dockerfile to include additional Tesseract language packs
2. Pass the language parameter in your API requests

### Adding Hebrew Support

```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-heb \  # Hebrew language pack
    # other dependencies...
```

Then in your API requests, specify:
```json
{
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "base64_data": "...",
  "language": "heb"  # For Hebrew only
  // Or "language": "eng+heb" for mixed content
}
```

## 🔒 Security Considerations

- The service processes files temporarily and automatically removes them after extraction
- Consider implementing authentication if deploying in a production environment
- Set appropriate file size limits in your production configuration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/file2text](https://github.com/yourusername/file2text)

---

Made with ❤️ by [Your Name]