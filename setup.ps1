# Voice Medical Agent - Windows Setup Script
# Yeh script poora environment set up karti hai
# Run in PowerShell: .\setup.ps1

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Voice Medical Agent - Setup" -ForegroundColor Cyan
Write-Host "  طبي مشاورت ایجنٹ - سیٹ اپ" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[Step 1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found! Install Python 3.10+ from https://python.org" -ForegroundColor Red
    Write-Host "  Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
Write-Host ""
Write-Host "[Step 2/5] Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  OK: Virtual environment created (venv/)" -ForegroundColor Green
} else {
    Write-Host "  SKIP: venv/ already exists" -ForegroundColor DarkYellow
}

# Step 3: Activate and install dependencies
Write-Host ""
Write-Host "[Step 3/5] Installing Python dependencies..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install --upgrade pip -q
pip install -r requirements.txt
Write-Host "  OK: All dependencies installed" -ForegroundColor Green

# Step 4: Check Ollama
Write-Host ""
Write-Host "[Step 4/5] Checking Ollama (local Qwen)..." -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "  OK: $ollamaVersion" -ForegroundColor Green
    
    # Check if Qwen model exists
    Write-Host "  Checking for Qwen3 model..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    if ($models -match "qwen3") {
        Write-Host "  OK: Qwen3 model found" -ForegroundColor Green
    } else {
        Write-Host "  Qwen3 model not found. Downloading qwen3:8b (~5GB)..." -ForegroundColor Yellow
        Write-Host "  This may take 10-30 minutes depending on your internet..." -ForegroundColor Yellow
        ollama pull qwen3:8b
        Write-Host "  OK: Qwen3:8b downloaded" -ForegroundColor Green
    }
} catch {
    Write-Host "  WARNING: Ollama not found!" -ForegroundColor DarkYellow
    Write-Host "  For FREE local Qwen, install Ollama from: https://ollama.com" -ForegroundColor Yellow
    Write-Host "  Then run: ollama pull qwen3:8b" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Or use DashScope/OpenAI instead (edit .env file)" -ForegroundColor Yellow
}

# Step 5: Check .env
Write-Host ""
Write-Host "[Step 5/5] Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "  Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  OK: .env created - edit it with your API keys" -ForegroundColor Green
} else {
    Write-Host "  OK: .env exists" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To start the server:" -ForegroundColor White
Write-Host "    .\run.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Or manually:" -ForegroundColor White
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "    python server.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Then open: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "  IMPORTANT:" -ForegroundColor Yellow
Write-Host "    1. Edit .env and add your OpenAI API key (for Whisper STT)" -ForegroundColor White
Write-Host "    2. Make sure Ollama is running (for free Qwen LLM)" -ForegroundColor White
Write-Host "    3. Allow microphone access in your browser" -ForegroundColor White
Write-Host ""
