@echo off
:: Set the working directory to the directory of the script
cd /d "%~dp0"

:: Prompt the user to choose deployment type
echo =========================================
echo Choose the docker deployment type:
echo 1. Build Backend from Source
echo 2. Use Latest Stable Backend Image
echo =========================================
set /p deploy_type="Enter your choice (1 or 2): "

:: Prompt the user to choose CPU or GPU mode
echo =========================================
echo Choose the hardware mode:
echo 1. CPU
echo 2. GPU
echo =========================================
set /p mode="Enter your choice (1 or 2): "

:: Determine the docker-compose file based on inputs
if "%deploy_type%"=="1" (
    if "%mode%"=="1" (
        set "compose_file=docker-compose-build-cpu.yml"
        echo Build from Source - CPU mode selected.
    ) else if "%mode%"=="2" (
        set "compose_file=docker-compose-build-gpu.yml"
        echo Build from Source - GPU mode selected.
    ) else (
        echo Invalid hardware mode choice. Exiting.
        exit /b 1
    )
) else if "%deploy_type%"=="2" (
    if "%mode%"=="1" (
        set "compose_file=docker-compose-image-cpu.yml"
        echo Stable Image - CPU mode selected. Using %compose_file%
    ) else if "%mode%"=="2" (
        set "compose_file=docker-compose-image-gpu.yml"
        echo Stable Image - GPU mode selected. Using %compose_file%
    ) else (
        echo Invalid hardware mode choice. Exiting.
        exit /b 1
    )
) else (
    echo Invalid deployment type choice. Exiting.
    exit /b 1
)

:: Verify that the selected compose file exists
if not exist "%compose_file%" (
    echo Error: %compose_file% not found.
    exit /b 1
)

echo =========================================
echo Checking for .env file...
echo =========================================
if not exist ".env" (
    echo .env file not found. Creating a default .env file...
    (
        echo # Hugging Face Token
        echo HF_TOKEN=entertokenhere
        echo.
        echo # VLLM Services
        echo # VLLM_URL_FOR_ANALYSIS=http://vllmnemotrontext:8001/v1/chat/completions
        echo # VLLM_URL_FOR_SUMMARY=http://vllmnemotrontext:8001/v1/chat/completions
        echo # VLLM_URL_FOR_IMAGE=http://vllmqwenvision:8002/v1/chat/completions
        echo # VLLM_URL_FOR_SCORING=http://vllmnemotrontext:8001/v1/chat/completions
        echo # VLLM_URL_FOR_EXTRACTION=http://vllmnemotrontext:8001/v1/chat/completions
        echo.
        echo # VLLM Models
        echo # VLLM_MODEL_FOR_ANALYSIS=AMead10/Llama-3.2-3B-Instruct-AWQ
        echo # VLLM_MODEL_FOR_EXTRACTION=AMead10/Llama-3.2-3B-Instruct-AWQ
        echo # VLLM_MODEL_FOR_SUMMARY=AMead10/Llama-3.2-3B-Instruct-AWQ
        echo # VLLM_MODEL_FOR_IMAGE=Qwen/Qwen2-VL-2B-Instruct-AWQ
        echo # VLLM_MODEL_FOR_SCORING=AMead10/Llama-3.2-3B-Instruct-AWQ
        echo.
        echo #############OLLAMA PARAMS###################
        echo OLLAMA_URL=http://ollama:11434
        echo OLLAMA_MODEL_FOR_ANALYSIS=qwen2.5:7b
        echo OLLAMA_MODEL_FOR_EXTRACTION=qwen2.5:7b
        echo OLLAMA_MODEL_FOR_SUMMARY=qwen2.5:7b
        echo OLLAMA_MODEL_FOR_IMAGE=llava-phi3
        echo OLLAMA_MODEL_FOR_SCORING=qwen2.5:7b
        echo.
        echo # React App Configuration
        echo REACT_APP_API_URL=http://localhost:8007
        echo.
        echo # Kafka Configuration
        echo KAFKA_BOOTSTRAP_SERVERS=kafka:9092
        echo KAFKA_TOPIC=dissertation_analysis_queue
        echo MAX_CONCURRENT_USERS=2
        echo.
        echo # Redis Configuration
        echo REDIS_URL=redis://redis:6379
        echo.
        echo # Database Configuration
        echo SQLALCHEMY_DATABASE_URL=mysql+pymysql://root:Spanda%40123@mysql:3306/feedbackDb
    ) > .env
    echo Default .env file created successfully.
) ELSE (
    echo .env file already exists. Proceeding with the script...
)

echo =========================================
echo Step 1: Creating Docker network 'app_network'
echo =========================================
docker network create app_network 2>nul
if %errorlevel% neq 0 (
    echo Network 'app_network' already exists or could not be created.
) else (
    echo Network 'app_network' created successfully.
)

echo =========================================
echo Step 2: Running Docker Compose with %compose_file%
echo =========================================
docker compose -f "%compose_file%" up -d --build
if %errorlevel% neq 0 (
    echo Docker Compose failed to start. Exiting script.
    exit /b %errorlevel%
) else (
    echo Docker Compose started successfully.
)

echo =========================================
echo Waiting for 30 seconds before running entrypoint.bat...
echo =========================================
timeout /t 30 /nobreak >nul

echo =========================================
echo Step 3: Running entrypoint.bat
echo =========================================
if exist entrypoint.bat (
    call entrypoint.bat
    if %errorlevel% neq 0 (
        echo entrypoint.bat encountered an error.
        exit /b %errorlevel%
    ) else (
        echo entrypoint.bat ran successfully.
    )
) else (
    echo entrypoint.bat not found in the current directory.
    exit /b 1
)

echo =========================================
echo All steps completed successfully.
echo =========================================
echo All steps completed successfully! Please visit http://localhost:4000/ in order to use the application.
echo =========================================
exit /b 0