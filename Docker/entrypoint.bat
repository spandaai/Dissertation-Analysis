@echo off
setlocal enabledelayedexpansion

REM Enable error handling
set ERRORLEVEL=0

REM Load environment variables from the .env file
echo =========================================
echo Loading environment variables from .env
echo =========================================
for /f "tokens=1,2 delims==" %%a in ('type .env') do (
    set %%a=%%b
    echo Loaded %%a=%%b
)

REM Check if curl is installed
echo =========================================
echo Checking for curl installation...
echo =========================================
where curl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo curl not found, installing...
    powershell -Command "Start-Process -Verb RunAs powershell -ArgumentList 'Install-Package -Name curl -Force'"
) else (
    echo curl is already installed.
)

REM Start the Ollama server
echo =========================================
echo Starting Ollama server...
echo =========================================
start /B ollama serve > ollama.log 2>&1
set SERVER_PID=%!

REM Wait for the server to be ready
echo Waiting for the server to be ready...
:wait_server
curl -s -f http://localhost:11434 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Waiting for the server to start...
    timeout /t 2 >nul
    goto wait_server
)

echo Server is ready. Starting to pull models...

REM Pull models based on environment variables
echo =========================================
echo Pulling models listed in .env file
echo =========================================
for %%A in (
    OLLAMA_MODEL_FOR_ANALYSIS
    OLLAMA_MODEL_FOR_EXTRACTION
    OLLAMA_MODEL_FOR_SUMMARY
    OLLAMA_MODEL_FOR_IMAGE
    OLLAMA_MODEL_FOR_SCORING
) do (
    set MODEL=!%%A!
    if defined MODEL (
        echo Pulling model: !MODEL!
        docker exec -it ollama ollama pull !MODEL!
        if %ERRORLEVEL% NEQ 0 (
            echo Failed to pull model: !MODEL!
            exit /b 1
        )
    ) else (
        echo Environment variable %%A is not defined. Skipping...
    )
)

echo =========================================
echo All models pulled successfully. Server is running.
echo =========================================

REM Kill the server process
echo Shutting down Ollama server...
taskkill /PID %SERVER_PID% /F >nul 2>&1

endlocal
