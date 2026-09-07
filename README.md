<<<<<<< HEAD
# 🏥 Voice Medical Agent - صوتی طبی مشاورت
### Urdu + Sindhi Voice-Based Doctor Consultation Agent

AI-powered voice agent jo doctor ki tarah behave karta hai. User apni **awaaz mein symptoms** batata hai aur agent **Urdu ya Sindhi** mein guidance deta hai - bilkul jaise ek real doctor karta hai.

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 🗣️ Voice Input | Urdu + Sindhi mein bol kar symptoms batao |
| 🩺 Doctor Brain | GPT-4o powered medical guidance (symptom analysis, follow-up questions) |
| 🔊 Voice Output | Doctor ka jawab Urdu/Sindhi voice mein suno |
| 🌐 Multi-Language | Urdu (اردو), Sindhi (سنڌي), English support |
| 💬 Conversation Memory | Puri baat yaad rakhta hai context ke saath |
| 🖥️ Web Interface | Browser se call karo, koi app install nahi |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    USER (Browser/Mobile)                       │
│   🎤 Speak Symptoms  ←──→  🔊 Listen to Doctor Response       │
└────────────────┬─────────────────────────────────┬────────────┘
                 │ Audio (WebM/WAV)                │ Audio (MP3/WAV)
                 ▼                                 │
┌─────────────────────────────┐                    │
│  1. SPEECH-TO-TEXT (STT)    │                    │
│  ┌─────────────────────────┐ │                    │
│  │ OpenAI Whisper (ur/sd)  │ │                    │
│  │ Google Cloud (ur)       │ │                    │
│  │ Azure Speech (ur+sd)    │ │                    │
│  └─────────────────────────┘ │                    │
│  Output: Patient Text        │                    │
└────────────────┬────────────┘                    │
                 │ "مجھے سر درد ہے"                 │
                 ▼                                 │
┌─────────────────────────────┐                    │
│  2. DOCTOR AGENT (LLM)      │                    │
│  ┌─────────────────────────┐ │                    │
│  │ GPT-4o + Medical Prompt │ │                    │
│  │ Urdu/Sindhi System Msg  │ │                    │
│  │ Conversation History    │ │                    │
│  └─────────────────────────┘ │                    │
│  Output: Doctor Text         │                    │
└────────────────┬────────────┘                    │
                 │ "سر درد کی کئی وجوہات..."        │
                 ▼                                 │
┌─────────────────────────────┐                    │
│  3. TEXT-TO-SPEECH (TTS)    │                    │
│  ┌─────────────────────────┐ │                    │
│  │ OpenAI TTS (basic)      │ │                    │
│  │ Azure Neural (BEST ⭐)  │ │                    │
│  │ Google Cloud (good)     │ │                    │
│  │ ElevenLabs (premium)    │ │                    │
│  └─────────────────────────┘ │                    │
│  Output: Doctor Audio        │────────────────────┘
└─────────────────────────────┘
```

---

## 🚀 Quick Start

### Step 1: Clone & Install
```bash
# Dependencies install
pip install -r requirements.txt
```

### Step 2: Set API Keys
```bash
# .env.example ko copy karke .env banao
copy .env.example .env

# Ab .env mein apni OpenAI API key dalo
# OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Run Server
```bash
python server.py
```

### Step 4: Open Browser
```
http://localhost:8000
```

1. Language select karo (Urdu / Sindhi / English)
2. 📞 Call button dabao
3. 🎤 Mic button dabao aur symptoms bolo
4. Doctor ka jawab suno!

---

## 🌍 Language Support Guide

### Urdu (اردو) - Best Support ✅
| Component | Provider | Quality |
|-----------|----------|---------|
| STT | OpenAI Whisper | ⭐⭐⭐⭐⭐ Excellent |
| STT | Google Cloud | ⭐⭐⭐⭐ Very Good |
| STT | Azure Speech | ⭐⭐⭐⭐ Very Good |
| LLM | GPT-4o | ⭐⭐⭐⭐⭐ Excellent (native Urdu) |
| TTS | Azure Neural (UzmaNeural) | ⭐⭐⭐⭐⭐ **RECOMMENDED** |
| TTS | Google Cloud (ur-PK) | ⭐⭐⭐⭐ Good |
| TTS | OpenAI TTS | ⭐⭐ Basic (English accent) |

### Sindhi (سنڌي) - Limited Support ⚠️
| Component | Provider | Quality |
|-----------|----------|---------|
| STT | OpenAI Whisper | ⭐⭐⭐ Decent (clear speech needed) |
| STT | Azure Speech | ⭐⭐⭐⭐ Best for Sindhi |
| LLM | GPT-4o | ⭐⭐⭐⭐ Good (via Sindhi system prompt) |
| TTS | Azure Neural (ShaziaNeural) | ⭐⭐⭐⭐⭐ **RECOMMENDED** |
| TTS | ElevenLabs | ⭐⭐⭐⭐ Good (multilingual v2) |

> **Sindhi ke liye RECOMMENDED setup:** Azure Speech STT + GPT-4o + Azure Neural TTS

---

## 🔧 Configuration for Sindhi

`config.py` mein yeh changes karo:

```python
# config.py mein
default_language = "sd"        # Sindhi default
stt_provider = "azure"         # Azure for better Sindhi STT
tts_provider = "azure"         # Azure Neural TTS has Sindhi voices
```

Ya environment variables set karo:
```env
# .env file mein
AZURE_SPEECH_KEY=your-azure-key
AZURE_SPEECH_REGION=eastus
```

---

## 📁 Project Structure

```
voice-medical-agent/
├── config.py            # Saari settings aur API keys
├── stt.py               # Speech-to-Text (Whisper, Google, Azure)
├── doctor_agent.py      # LLM Doctor brain (Urdu/Sindhi prompts)
├── tts.py               # Text-to-Speech (OpenAI, Azure, Google, ElevenLabs)
├── agent.py             # Main orchestrator (STT → LLM → TTS pipeline)
├── server.py            # FastAPI web server
├── static/
│   └── index.html       # Web UI (voice recording + chat)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

---

## 🎙️ Recommended Setup by Budget

### 💰 Budget Setup (OpenAI Only)
- **Cost:** ~$0.05 per consultation
- **STT:** OpenAI Whisper
- **LLM:** GPT-4o-mini (cheaper)
- **TTS:** OpenAI TTS
- **Best for:** Urdu only, quick prototype

### ⭐ Recommended Setup (OpenAI + Azure)
- **Cost:** ~$0.08 per consultation
- **STT:** OpenAI Whisper or Azure
- **LLM:** GPT-4o
- **TTS:** Azure Neural (Uzma/Shazia)
- **Best for:** Urdu + Sindhi, good quality

### 🏆 Premium Setup (OpenAI + Azure + ElevenLabs)
- **Cost:** ~$0.15 per consultation
- **STT:** Azure Speech
- **LLM:** GPT-4o
- **TTS:** ElevenLabs multilingual v2
- **Best for:** Production, best voice quality

---

## 📱 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/session/start` | New session (params: `language=ur`) |
| `POST` | `/api/session/{id}/speak` | Send audio, get doctor response |
| `POST` | `/api/session/{id}/switch-language` | Change language mid-call |
| `POST` | `/api/session/{id}/end` | End consultation |
| `GET`  | `/api/health` | Health check |

---

## ⚠️ Medical Disclaimer

> This agent provides **preliminary medical guidance only**. It is NOT a replacement for a real doctor.
> Always consult a qualified healthcare professional for proper diagnosis and treatment.
> In emergencies, call your local emergency number immediately.

---

## 🔮 Future Enhancements

- [ ] Twilio/phone integration (real phone call support)
- [ ] WebRTC for real-time streaming voice
- [ ] WhatsApp voice note integration
- [ ] Pashto + Punjabi language support
- [ ] Medical history database per user
- [ ] Appointment booking with real doctors
- [ ] Prescription generation
=======
# voice-medical-agent
this is Voice medical agent
>>>>>>> fab60290a06906921c81a3b03a68402847f7286b
