# Use a base image with Python 3.10
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the setup files
COPY setup.py ./
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e .

# Copy the application code
COPY ./backend/src ./backend/src

# Expose the desired port (change as needed)
EXPOSE 8006

# Command to run the application
CMD ["uvicorn", "backend.src.main:main", "--host", "0.0.0.0", "--port", "8006"]
