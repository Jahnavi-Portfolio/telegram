#Requires -Version 5.1
<#
.SYNOPSIS
    Starts the Telegram AI Assistant for local development without Docker.
.DESCRIPTION
    This script automates the following steps:
    1. Checks for required software (Python 3.10+, pip).
    2. Creates a Python virtual environment (.venv) if it doesn't exist.
    3. Installs dependencies from requirements.txt.
    4. Checks for a local Redis server and provides guidance if not found.
    5. Starts the RQ worker process in a new terminal window.
    6. Starts the Uvicorn web server for the main bot application.
    It assumes you have a .env file configured and ngrok running separately.
.NOTES
    - Run this script from the root of the project directory.
    - Requires PowerShell 5.1 or newer.
    - You must run `ngrok http 8000` in a separate terminal and update your .env file's WEBHOOK_URL before running this script.
#>

# --- Configuration ---
$pythonExecutable = "python"
$venvDir = ".venv"
$requirementsFile = "requirements.txt"
$redisPort = 6379

# --- Helper Functions ---
function Write-Host-Color($message, $color) {
    Write-Host $message -ForegroundColor $color
}

# --- Script Body ---
Clear-Host
Write-Host-Color "=================================================" -Cyan
Write-Host-Color "  Telegram AI Assistant - Local Development   " -Cyan
Write-Host-Color "=================================================" -Cyan
Write-Host ""

# 1. Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host-Color "[ERROR] .env file not found. Please copy .env.example to .env and fill in your credentials." -Red
    exit 1
}
Write-Host-Color "[OK] .env file found." -Green

# Import environment variables from .env to use in this script
try {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^(?!#)([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value)
        }
    }
}
catch {
    Write-Host-Color "[ERROR] Failed to parse .env file." -Red
    exit 1
}


# 2. Check for Python
Write-Host "Checking for Python..."
try {
    $pythonVersion = (& $pythonExecutable --version)
    Write-Host-Color "[OK] Found Python: $pythonVersion" -Green
}
catch {
    Write-Host-Color "[ERROR] Python is not installed or not in your PATH. Please install Python 3.10+." -Red
    exit 1
}

# 3. Setup Virtual Environment and Install Dependencies
if (-not (Test-Path "$venvDir/Scripts/activate")) {
    Write-Host-Color "Virtual environment not found. Creating one..." -Yellow
    try {
        & $pythonExecutable -m venv $venvDir
        Write-Host-Color "[OK] Virtual environment created at '$venvDir'." -Green
    }
    catch {
        Write-Host-Color "[ERROR] Failed to create virtual environment." -Red
        exit 1
    }
}
else {
    Write-Host-Color "[OK] Virtual environment found." -Green
}

# Activate virtual environment for this script session
$activateScript = Join-Path $pwd.Path "$venvDir/Scripts/Activate.ps1"
try {
    . $activateScript
}
catch {
    Write-Host-Color "[ERROR] Failed to activate virtual environment. You may need to run 'Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process' first." -Red
    exit 1
}


Write-Host "Installing/checking dependencies from $requirementsFile..."
try {
    pip install -r $requirementsFile | Out-Null
    Write-Host-Color "[OK] Dependencies are up to date." -Green
}
catch {
    Write-Host-Color "[ERROR] Failed to install dependencies." -Red
    exit 1
}

# 4. Check for Redis
Write-Host "Checking for local Redis server on port $redisPort..."
try {
    $redisTest = Test-NetConnection -ComputerName localhost -Port $redisPort -WarningAction SilentlyContinue
    if ($redisTest.TcpTestSucceeded) {
        Write-Host-Color "[OK] Redis server is running on port $redisPort." -Green
    }
    else {
        throw "Redis connection failed."
    }
}
catch {
    Write-Host-Color "[WARNING] Local Redis server not found on port $redisPort." -Yellow
    Write-Host-Color "Please ensure Redis is running. You can start it easily with Docker:" -Yellow
    Write-Host-Color "  docker run -d -p 6379:6379 redis" -Yellow
    # Optionally exit here, or let the worker fail. We'll let it continue.
}

# 5. Start RQ Worker
Write-Host-Color "Starting RQ Worker process in a new window..." -Cyan
$redisUrl = $env:REDIS_URL
if (-not $redisUrl) {
    Write-Host-Color "[ERROR] REDIS_URL not found in .env file." -Red
    exit 1
}
$workerCommand = "rq worker -u `"$redisUrl`" default"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$($pwd.Path)'; . $activateScript; $workerCommand"


# 6. Start Web Server
Write-Host-Color "Starting FastAPI web server..." -Cyan
Write-Host "You can access the bot logs in this window."
Write-Host "Make sure ngrok is running and your WEBHOOK_URL in .env is correct."
Write-Host "Press CTRL+C to stop the server."
Write-Host ""

try {
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}
catch {
    Write-Host-Color "[ERROR] Failed to start Uvicorn server." -Red
}
