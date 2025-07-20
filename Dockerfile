# File: Dockerfile

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional: if running locally with Mongo client tools)
# RUN apt-get update && apt-get install -y build-essential curl

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables (adjust as needed)
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true

# Default command: CLI dispatcher
CMD ["python", "main.py"]
