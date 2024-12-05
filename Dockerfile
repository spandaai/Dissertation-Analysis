# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /dissertation

# Copy project files
COPY . /dissertation

# Install system dependencies (poppler-utils for PDF processing and libpq-dev for psycopg2)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -e .

# Expose port 8006 for the FastAPI application
EXPOSE 8006

# Command to run the FastAPI app
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8006", "--reload"]
