# Use an official Python runtime as a parent image
FROM python:3.10-slim

WORKDIR /dissertation
COPY . /dissertation

COPY setup.py ./
COPY requirements.txt ./

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e .

# Expose port 8006 for the FastAPI application
EXPOSE 8006

# Command to run the FastAPI app
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8006", "--reload"]
