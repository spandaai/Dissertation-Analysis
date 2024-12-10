@echo off
setlocal enabledelayedexpansion

REM Enable error handling
set ERRORLEVEL=0

REM Load environment variables from the .env file
for /f "tokens=1,2 delims==" %%a in ('type .env') do (
    set %%a=%%b
)

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

REM Iterate over models in the .env file and pull them
for %%A in (
    OLLAMA_MODEL_FOR_ANALYSIS
    OLLAMA_MODEL_FOR_EXTRACTION
    OLLAMA_MODEL_FOR_SUMMARY
    OLLAMA_MODEL_FOR_IMAGE
    OLLAMA_MODEL_FOR_SCORING
) do (
    set MODEL=!%%A!
    echo Pulling model: !MODEL!
    docker exec -it ollama ollama pull !MODEL!
)

echo All models pulled successfully. Server is running.

REM Kill the server process
taskkill /PID %SERVER_PID% /F >nul 2>&1

endlocal
