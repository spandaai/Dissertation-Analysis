@echo off
setlocal enabledelayedexpansion

REM Enable error handling
set ERRORLEVEL=0

REM Check if curl is installed
where curl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo curl not found, installing...
    powershell -Command "Start-Process -Verb RunAs powershell -ArgumentList 'Install-Package -Name curl -Force'"
) else (
    echo curl is already installed.
)

echo Starting Ollama server...
start /B ollama serve > ollama.log 2>&1
set SERVER_PID=%!

echo Waiting for the server to be ready...
:wait_server
curl -s -f http://localhost:11434 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Waiting for the server to start...
    timeout /t 2 >nul
    goto wait_server
)

echo Server is ready. Starting to pull models...

echo Pulling text model...
docker exec -it ollama ollama pull qwen2.5:7b

echo Pulling vision model...
docker exec -it ollama ollama pull llava-phi3

echo All models pulled successfully. Server is running.

REM Kill the tail process
taskkill /PID %TAIL_PID% /F >nul 2>&1

REM Wait for server process to end
taskkill /PID %SERVER_PID% /F >nul 2>&1

endlocal
