#!/bin/bash

set -e  # Exit immediately on error
set -o pipefail  # Capture errors in pipes
set -o nounset  # Treat unset variables as errors

# Load environment variables from .env file
echo "========================================="
echo "Loading environment variables from .env"
echo "========================================="

if [ ! -f .env ]; then
  echo ".env file not found. Exiting..."
  exit 1
fi

while IFS='=' read -r key value; do
  # Skip empty lines and comments
  if [[ -n "$key" && "$key" != \#* && -n "$value" ]]; then
    export "$key=$value"
    echo "Loaded $key=$value"
  fi
done < .env

# Check if curl is installed
echo "========================================="
echo "Checking for curl installation..."
echo "========================================="

if ! command -v curl &>/dev/null; then
  echo "curl not found, installing..."
  sudo apt-get update && sudo apt-get install -y curl
else
  echo "curl is already installed."
fi

# Start the Ollama server
echo "========================================="
echo "Starting Ollama server..."
echo "========================================="
ollama serve > ollama.log 2>&1 &
SERVER_PID=$!

# Wait for the server to be ready
echo "Waiting for the server to be ready..."
until curl -s -f http://localhost:11434 > /dev/null 2>&1; do
  echo "Waiting for the server to start..."
  sleep 2
done

echo "Server is ready. Starting to pull models..."

# Pull models based on environment variables
echo "========================================="
echo "Pulling models listed in .env file"
echo "========================================="

MODEL_VARS=("OLLAMA_MODEL_FOR_ANALYSIS" "OLLAMA_MODEL_FOR_EXTRACTION" "OLLAMA_MODEL_FOR_SUMMARY" "OLLAMA_MODEL_FOR_IMAGE" "OLLAMA_MODEL_FOR_SCORING")

for MODEL_VAR in "${MODEL_VARS[@]}"; do
  MODEL=${!MODEL_VAR:-}
  if [ -n "$MODEL" ]; then
    echo "Pulling model: $MODEL"
    docker exec -it ollama-platform ollama pull "$MODEL"
    if [ $? -ne 0 ]; then
      echo "Failed to pull model: $MODEL"
      kill -9 $SERVER_PID
      exit 1
    fi
  else
    echo "Environment variable $MODEL_VAR is not defined. Skipping..."
  fi
done

echo "========================================="
echo "All models pulled successfully. Server is running."
echo "========================================="