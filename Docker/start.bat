@echo off

REM Set the working directory to the directory of the script
cd /d "%~dp0"

REM Prompt the user to choose deployment type
echo =========================================
echo Choose the docker deployment type:
echo 1. Build Backend from Source
echo 2. Use Latest Stable Backend Image
echo =========================================
set /p deploy_type="Enter your choice (1 or 2): "

REM Determine the docker-compose file based on inputs
if "%deploy_type%"=="1" (
    set compose_file=docker-compose-build.yml
    echo Building from Source
) else if "%deploy_type%"=="2" (
    set compose_file=docker-compose-image.yml
    echo Stable Image - CPU mode selected. Using %compose_file%
) else (
    echo Invalid deployment type choice. Exiting.
    exit /b 1
)

REM Verify that the selected compose file exists
if not exist "%compose_file%" (
    echo Error: %compose_file% not found.
    exit /b 1
)

echo =========================================
echo Checking for .env file...
echo =========================================
if not exist ".env" (
    echo .env file not found. Creating a default .env file...
    > .env echo # Hugging Face Token
    >> .env echo HF_TOKEN=entertokenhere
    >> .env echo.
    >> .env echo # VLLM Services
    >> .env echo # VLLM_URL_FOR_ANALYSIS=http://vllmnemotrontext:8001/v1/chat/completions
    >> .env echo # VLLM_URL_FOR_SUMMARY=http://vllmnemotrontext:8001/v1/chat/completions
    >> .env echo # VLLM_URL_FOR_IMAGE=http://vllmqwenvision:8002/v1/chat/completions
    >> .env echo # VLLM_URL_FOR_SCORING=http://vllmnemotrontext:8001/v1/chat/completions
    >> .env echo # VLLM_URL_FOR_EXTRACTION=http://vllmnemotrontext:8001/v1/chat/completions
    >> .env echo.
    >> .env echo # VLLM Models
    >> .env echo # VLLM_MODEL_FOR_ANALYSIS=AMead10/Llama-3.2-3B-Instruct-AWQ
    >> .env echo # VLLM_MODEL_FOR_EXTRACTION=AMead10/Llama-3.2-3B-Instruct-AWQ
    >> .env echo # VLLM_MODEL_FOR_SUMMARY=AMead10/Llama-3.2-3B-Instruct-AWQ
    >> .env echo # VLLM_MODEL_FOR_IMAGE=Qwen/Qwen2-VL-2B-Instruct-AWQ
    >> .env echo # VLLM_MODEL_FOR_SCORING=AMead10/Llama-3.2-3B-Instruct-AWQ
    >> .env echo.
    >> .env echo #############OLLAMA PARAMS###################
    >> .env echo OLLAMA_URL=http://ollama:11434
    >> .env echo OLLAMA_MODEL_FOR_ANALYSIS=qwen2.5:7b
    >> .env echo OLLAMA_MODEL_FOR_EXTRACTION=qwen2.5:7b
    >> .env echo OLLAMA_MODEL_FOR_SUMMARY=qwen2.5:7b
    >> .env echo OLLAMA_MODEL_FOR_IMAGE=llava-phi3
    >> .env echo OLLAMA_MODEL_FOR_SCORING=qwen2.5:7b
    >> .env echo.
    >> .env echo # React App Configuration
    >> .env echo REACT_APP_API_URL=http://localhost:8007
    >> .env echo.
    >> .env echo # Kafka Configuration
    >> .env echo KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    >> .env echo KAFKA_TOPIC=dissertation_analysis_queue
    >> .env echo MAX_CONCURRENT_USERS=2
    >> .env echo.
    >> .env echo # Redis Configuration
    >> .env echo REDIS_URL=redis://redis:6379
    >> .env echo.
    >> .env echo # Database Configuration
    >> .env echo SQLALCHEMY_DATABASE_URL=mysql+pymysql://root:Spanda%%40123@mysql:3306/feedbackDb
    echo Default .env file created successfully.
) else (
    echo .env file already exists. Proceeding with the script...
)

echo =========================================
echo Step 1: Creating Docker network 'app_network'
echo =========================================
docker network create app_network 2>nul
if errorlevel 1 (
    echo Network 'app_network' already exists or could not be created.
) else (
    echo Network 'app_network' created successfully.
)

echo =========================================
echo Step 2: Running Docker Compose with %compose_file%
echo =========================================
docker compose -f "%compose_file%" up -d
if errorlevel 1 (
    echo Docker Compose failed to start. Exiting script.
    exit /b 1
) else (
    echo Docker Compose started successfully.
)

echo =========================================
echo Waiting for 30 seconds before running entrypoint.bat...
echo =========================================
choice /n /t 30 /d y >nul

echo =========================================
echo Step 3: Running entrypoint.bat
echo =========================================
if exist "entrypoint.bat" (
    call entrypoint.bat
    if errorlevel 1 (
        echo entrypoint.bat encountered an error.
        exit /b 1
    ) else (
        echo entrypoint.bat ran successfully.
    )
) else (
    echo entrypoint.bat not found in the current directory.
    exit /b 1
)

echo =========================================
echo All steps completed successfully!
echo Please visit http://localhost:4000/ to use the application.
echo =========================================
exit /b 0
