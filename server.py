"""
FastAPI Web Server for Voice Medical Agent
Browser se voice call karne ke liye endpoints provide karta hai.
"""
import base64
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from config import Config
from agent import VoiceMedicalAgent
from medical_knowledge import MedicalKnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# ── Global state ──────────────────────────────────────────────────────
config = Config()
agents: dict[str, VoiceMedicalAgent] = {}  # session_id -> agent

# Medical knowledge base - loaded once at startup, shared by all sessions
# This provides real medical data as context to the LLM
knowledge_base = MedicalKnowledgeBase()


# ── FastAPI App ───────────────────────────────────────────────────────
app = FastAPI(
    title="Voice Medical Agent",
    description="Urdu/Sindhi voice-based medical consultation agent",
    version="1.0.0",
)

# CORS (browser mic access needs this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load the medical knowledge base when the server starts."""
    logger.info("Loading medical knowledge base...")
    knowledge_base.load()
    stats = knowledge_base.get_stats()
    logger.info(
        "Medical knowledge base ready: %d chunks indexed from %s",
        stats["total_chunks"],
        stats["data_dir"],
    )


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the web interface."""
    html_path = STATIC_DIR / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/api/session/start")
async def start_session(language: str = Form("ur")):
    """
    Start a new consultation session.
    Returns session_id and greeting audio (base64 encoded).
    """
    session_id = str(uuid.uuid4())
    agent = VoiceMedicalAgent(
        config, language=language, knowledge_base=knowledge_base
    )
    agents[session_id] = agent

    result = await agent.start_session(session_id)

    return {
        "session_id": session_id,
        "greeting_text": result["greeting_text"],
        "greeting_audio": base64.b64encode(result["greeting_audio"]).decode(),
        "audio_format": result["audio_format"],
        "language": language,
    }


@app.post("/api/session/{session_id}/speak")
async def process_speech(
    session_id: str,
    audio: UploadFile = File(...),
):
    """
    Process user's voice input.
    Accepts audio file, returns doctor's text + voice response.
    """
    agent = agents.get(session_id)
    if not agent:
        raise HTTPException(404, "Session not found")

    audio_data = await audio.read()

    # Detect file extension from content type
    content_type = audio.content_type or "audio/wav"
    ext_map = {
        "audio/wav": "wav",
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mp3": "mp3",
        "audio/mpeg": "mp3",
        "audio/mp4": "m4a",
    }
    file_ext = ext_map.get(content_type, "wav")

    result = await agent.process_voice_input(audio_data, file_ext)

    return {
        "patient_text": result["patient_text"],
        "doctor_text": result["doctor_text"],
        "doctor_audio": base64.b64encode(result["doctor_audio"]).decode(),
        "audio_format": result["audio_format"],
        "status": result["status"],
    }


@app.post("/api/session/{session_id}/switch-language")
async def switch_language(session_id: str, language: str = Form(...)):
    """Switch language mid-session."""
    agent = agents.get(session_id)
    if not agent:
        raise HTTPException(404, "Session not found")

    agent.switch_language(language)
    return {"status": "ok", "language": language}


@app.post("/api/session/{session_id}/end")
async def end_session(session_id: str):
    """End consultation session."""
    agent = agents.get(session_id)
    if not agent:
        raise HTTPException(404, "Session not found")

    result = await agent.end_session()
    del agents[session_id]

    return {
        "farewell_text": result["farewell_text"],
        "farewell_audio": base64.b64encode(result["farewell_audio"]).decode(),
        "audio_format": result["audio_format"],
        "conversation_summary": result["conversation_summary"],
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "active_sessions": len(agents),
        "llm_provider": config.llm_provider,
        "stt_provider": config.stt_provider,
        "tts_provider": config.tts_provider,
        "medical_knowledge": knowledge_base.get_stats(),
    }


# ── Main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print()
    print("=" * 55)
    print("  Voice Medical Agent - طبي مشاورت")
    print("=" * 55)
    print(f"  LLM Provider:  {config.llm_provider}")
    print(f"  STT Provider:  {config.stt_provider}")
    print(f"  TTS Provider:  {config.tts_provider}")
    print(f"  Server:        http://localhost:{config.port}")
    print("=" * 55)
    print()

    # Load medical knowledge base before starting the server
    print("  Loading medical knowledge base...")
    knowledge_base.load()
    kb_stats = knowledge_base.get_stats()
    print(f"  Medical Chunks: {kb_stats['total_chunks']} indexed")
    print("=" * 55)
    print()

    config.validate()
    uvicorn.run(app, host="127.0.0.1", port=config.port)
