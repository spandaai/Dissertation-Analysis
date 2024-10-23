# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the contents of the backend directory into the container
COPY backend/ /app/backend/
COPY setup.py ./
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e .

# Expose port 8006 for the FastAPI application
EXPOSE 8006

# Command to run the FastAPI app
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8006", "--reload"]
