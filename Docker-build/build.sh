#!/bin/bash

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes
set -o nounset  # Treat unset variables as errors

# Set working directory to the directory of the script
cd "$(dirname "$0")"

echo "========================================="
echo "Checking for .env file..."
echo "========================================="
if [ ! -f .env ]; then
  echo ".env file not found. Creating a default .env file..."
  cat <<EOL > .env
# Hugging Face Token
HF_TOKEN=<your_hf_token>

# VLLM Services
# VLLM_URL_FOR_ANALYSIS=http://vllmnemotrontext:8001/v1/chat/completions
# VLLM_URL_FOR_SUMMARY=http://vllmnemotrontext:8001/v1/chat/completions
# VLLM_URL_FOR_IMAGE=http://vllmqwenvision:8002/v1/chat/completions
# VLLM_URL_FOR_SCORING=http://vllmnemotrontext:8001/v1/chat/completions
# VLLM_URL_FOR_EXTRACTION=http://vllmnemotrontext:8001/v1/chat/completions

# VLLM Models
# VLLM_MODEL_FOR_ANALYSIS=AMead10/Llama-3.2-3B-Instruct-AWQ
# VLLM_MODEL_FOR_EXTRACTION=AMead10/Llama-3.2-3B-Instruct-AWQ
# VLLM_MODEL_FOR_SUMMARY=AMead10/Llama-3.2-3B-Instruct-AWQ
# VLLM_MODEL_FOR_IMAGE=Qwen/Qwen2-VL-2B-Instruct-AWQ
# VLLM_MODEL_FOR_SCORING=AMead10/Llama-3.2-3B-Instruct-AWQ

#############OLLAMA PARAMS###################
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL_FOR_ANALYSIS=qwen2.5:7b
OLLAMA_MODEL_FOR_EXTRACTION=qwen2.5:7b
OLLAMA_MODEL_FOR_SUMMARY=qwen2.5:7b
OLLAMA_MODEL_FOR_IMAGE=llava-phi3
OLLAMA_MODEL_FOR_SCORING=qwen2.5:7b

# React App Configuration
REACT_APP_API_URL=http://localhost:8007

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=dissertation_analysis_queue
MAX_CONCURRENT_USERS=2

# Redis Configuration
REDIS_URL=redis://redis:6379

# Database Configuration
SQLALCHEMY_DATABASE_URL=mysql+pymysql://root:Spanda%40123@mysql:3306/feedbackDb
EOL
  echo "Default .env file created successfully."
else
  echo ".env file already exists. Proceeding with the script..."
fi

echo "========================================="
echo "Step 1: Creating Docker network 'app_network'"
echo "========================================="
docker network create app_network || echo "Network 'app_network' already exists or could not be created."

echo "========================================="
echo "Step 2: Running Docker Compose"
echo "========================================="
docker-compose up -d
if [ $? -ne 0 ]; then
  echo "Docker Compose failed to start. Exiting script."
  exit 1
else
  echo "Docker Compose started successfully."
fi

echo "========================================="
echo "Waiting for 30 seconds before running entrypoint.sh..."
echo "========================================="
sleep 30

echo "========================================="
echo "Step 3: Running entrypoint.sh"
echo "========================================="
if [ -f entrypoint.sh ]; then
  bash entrypoint.sh
  if [ $? -ne 0 ]; then
    echo "entrypoint.sh encountered an error."
    exit 1
  else
    echo "entrypoint.sh ran successfully."
  fi
else
  echo "entrypoint.sh not found in the current directory."
  exit 1
fi

echo "========================================="
echo "All steps completed successfully."
echo "========================================="
