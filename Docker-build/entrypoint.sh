#!/bin/bash
set -e

# Install curl if not already installed
if ! command -v curl &> /dev/null; then
    echo "curl not found, installing..."
    apt-get update && apt-get install -y curl

else
    echo "curl is already installed."
fi

echo "Starting Ollama server..."
ollama serve >ollama.log 2>&1 &
server_pid=$!

echo "Streaming Ollama server logs..."

tail -f ollama.log &
tail_pid=$!

echo "Waiting for the server to be ready..."
echo "Waiting for the server to be ready..."
until curl -s -f http://localhost:11434 >/dev/null 2>&1; do
    echo "Waiting for the server to start..."
    sleep 2
done

echo "Server is ready. Starting to pull models..."

echo "Pulling llama3.2:3b-instruct-q2_K..."
ollama pull llama3.2:3b-instruct-q2_K

echo "Pulling llava-phi3..."
ollama pull llava-phi3

echo "All models pulled successfully. Server is running."

kill $tail_pid

wait $server_pid
