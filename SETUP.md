# Voice Medical Agent - Complete Setup Guide
## مکمل سیٹ اپ گائیڈ - Step by Step

---

## Folder Structure (فائلوں کی ترتیب)

```
voice-medical-agent/
│
├── .env                  ← Your API keys (EDIT THIS)
├── .env.example          ← Template file
├── .gitignore            ← Git ignore rules
│
├── config.py             ← All settings and provider configuration
├── stt.py                ← Speech-to-Text (Voice → Text)
├── doctor_agent.py       ← LLM Doctor Brain (Qwen/GPT-4)
├── tts.py                ← Text-to-Speech (Text → Voice)
├── agent.py              ← Main orchestrator (connects STT→LLM→TTS)
├── server.py             ← FastAPI web server
│
├── static/
│   └── index.html        ← Web UI (browser voice call interface)
│
├── requirements.txt      ← Python dependencies
├── setup.ps1             ← Windows PowerShell setup script
├── run.bat               ← Quick start (double-click to run)
│
├── SETUP.md              ← This guide
└── README.md             ← Project overview
```

---

## Prerequisites (پہلے سے چاہیے)

| Tool | Download Link | Purpose |
|------|--------------|---------|
| **Python 3.10+** | [python.org](https://python.org/downloads) | Programming language |
| **Ollama** | [ollama.com](https://ollama.com) | FREE local Qwen LLM |
| **Git** (optional) | [git-scm.com](https://git-scm.com) | Version control |

---

## Step-by-Step Setup

### Step 1: Install Python

1. Go to [python.org/downloads](https://python.org/downloads)
2. Download Python 3.10 or newer
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Verify:
```powershell
python --version
```

### Step 2: Install Ollama (FREE Local Qwen)

1. Go to [ollama.com](https://ollama.com)
2. Download and install Ollama for Windows
3. Open a new PowerShell terminal
4. Download the Qwen3 model:
```powershell
ollama pull qwen3:8b
```
This downloads ~5GB. Wait 10-30 minutes.

5. Verify it works:
```powershell
ollama run qwen3:8b "Assalam o Alaikum, Urdu mein jawab do"
```

### Step 3: Get OpenAI API Key (for Whisper STT + TTS)

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account or login
3. Go to API Keys section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-...`)
6. Add some credits ($5 minimum)

### Step 4: Run Setup Script

Open PowerShell in your project folder:
```powershell
cd "c:\Users\aysha.nazir\Documents\Qoder\2026-09-02\chat-1"
.\setup.ps1
```

**OR** do it manually:

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure API Keys

Open the `.env` file and add your OpenAI key:

```env
# .env file
LLM_PROVIDER=ollama           # FREE local Qwen (no key needed)
STT_PROVIDER=openai           # Whisper for voice input
TTS_PROVIDER=openai           # OpenAI for voice output

OPENAI_API_KEY=sk-your-actual-key-here    ← PUT YOUR KEY HERE
```

### Step 6: Start the Server

**Easy way (double-click):**
```
Double-click run.bat
```

**Or PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
python server.py
```

You should see:
```
================================================
  Voice Medical Agent - طبی مشاورت
================================================
  LLM Provider:  ollama
  STT Provider:  openai
  TTS Provider:  openai
  Server:        http://localhost:8000
================================================
```

### Step 7: Use It!

1. Open browser: **http://localhost:8000**
2. Select language: اردو / سنڌي / English
3. Click 📞 (call button)
4. Click 🎤 and speak your symptoms
5. Listen to the doctor's response!

---

## Configuration Options (سیٹنگز)

### Option A: 100% FREE Setup (Ollama + OpenAI Whisper)

```env
LLM_PROVIDER=ollama
STT_PROVIDER=openai        # Need OpenAI key for Whisper
TTS_PROVIDER=openai        # Need OpenAI key for TTS
OPENAI_API_KEY=sk-...
```
- LLM: FREE (local Qwen3:8b)
- STT: ~$0.006/min (Whisper)
- TTS: ~$0.015/1000 chars
- **Total: ~$0.02 per consultation**

### Option B: All Alibaba (DashScope)

```env
LLM_PROVIDER=dashscope
STT_PROVIDER=dashscope
TTS_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-key
```
- Use Alibaba for everything
- 1M free tokens per model for new users

### Option C: Best Quality (Mixed)

```env
LLM_PROVIDER=ollama           # FREE Qwen for brain
STT_PROVIDER=openai           # Whisper (best Urdu STT)
TTS_PROVIDER=azure            # Azure Neural (best Urdu/Sindhi voice)
OPENAI_API_KEY=sk-...
AZURE_SPEECH_KEY=your-key
```

### Option D: All OpenAI

```env
LLM_PROVIDER=openai
STT_PROVIDER=openai
TTS_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## Troubleshooting (مسائل کا حل)

### "ModuleNotFoundError: No module named 'fastapi'"
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "Connection refused" or "Ollama not running"
```powershell
# Make sure Ollama is running
ollama serve
# Or restart Ollama from system tray
```

### "OPENAI_API_KEY is required"
Edit `.env` file and add your actual OpenAI API key.

### "Microphone not working in browser"
- Browser must be `http://localhost` (not `http://0.0.0.0`)
- Allow microphone permission when browser asks
- Use Chrome or Edge (best mic support)

### Port 8000 already in use
Edit `.env`:
```env
# Not currently configurable via .env, edit config.py directly:
port = 8001
```

---

## Complete Flow Diagram

```
                    ┌─────────────┐
                    │   USER      │
                    │  (Browser)  │
                    └──────┬──────┘
                           │
              🎤 Speaks symptoms in Urdu/Sindhi
                           │
                           ▼
              ┌────────────────────────┐
              │  1. SPEECH-TO-TEXT     │
              │  ──────────────────    │
              │  OpenAI Whisper        │  ← stt.py
              │  "مجھے سر درد ہے"      │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  2. DOCTOR AGENT (LLM) │
              │  ──────────────────    │
              │  Qwen3:8b (Ollama)     │  ← doctor_agent.py
              │  or GPT-4o (OpenAI)    │
              │  or Qwen-Max (DashScope│
              │                        │
              │  Output:               │
              │  "سر درد کب سے ہے؟"    │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  3. TEXT-TO-SPEECH     │
              │  ──────────────────    │
              │  OpenAI TTS            │  ← tts.py
              │  or Azure Neural       │
              │  or Qwen TTS           │
              └────────────┬───────────┘
                           │
                    🔊 Doctor speaks
                           │
                           ▼
                    ┌─────────────┐
                    │   USER      │
                    │  (Listens)  │
                    └─────────────┘
```

---

## Quick Commands Reference

| Action | Command |
|--------|---------|
| Setup (first time) | `.\setup.ps1` |
| Start server | `.\run.bat` or `python server.py` |
| Download Qwen model | `ollama pull qwen3:8b` |
| Test Qwen locally | `ollama run qwen3:8b` |
| Check Ollama models | `ollama list` |
| Install new dependency | `pip install <package-name>` |
| Health check | Visit `http://localhost:8000/api/health` |
