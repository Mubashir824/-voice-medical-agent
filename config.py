"""
Configuration for Voice Medical Agent
Yahan saari API keys aur settings manage hoti hain.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use system env vars


@dataclass
class Config:
    """Main configuration class for the voice medical agent."""

    # ── Language Settings ──────────────────────────────────────────────
    # Supported languages: "ur" (Urdu), "sd" (Sindhi), "auto" (auto-detect)
    default_language: str = "ur"

    # ── OpenAI Settings (Whisper STT + GPT + TTS) ────────────────────
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    stt_model: str = "whisper-1"          # Whisper for speech-to-text
    llm_model: str = "gpt-4o"             # GPT-4o for doctor reasoning
    tts_model: str = "tts-1-hd"          # High quality TTS
    tts_voice: str = "nova"               # Voice persona (alloy, echo, fable, onyx, nova, shimmer)

    # ── Google Cloud Settings (Alternative STT/TTS for Sindhi) ────────
    google_credentials_path: str = field(
        default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    )

    # ── Azure Settings (Best for Urdu/Sindhi TTS) ────────────────────
    azure_speech_key: str = field(default_factory=lambda: os.getenv("AZURE_SPEECH_KEY", ""))
    azure_speech_region: str = field(default_factory=lambda: os.getenv("AZURE_SPEECH_REGION", "eastus"))

    # ── Alibaba Cloud / DashScope Settings (Qwen Models) ───────────
    dashscope_api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    dashscope_base_url: str = field(
        default_factory=lambda: os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
    )
    # Qwen LLM models: qwen-max, qwen-plus, qwen-turbo, qwen3-235b-a22b
    qwen_llm_model: str = "qwen-max"
    # Qwen TTS: cosyvoice-v2 (Qwen3-TTS on DashScope)
    qwen_tts_model: str = "cosyvoice-v2"
    qwen_tts_voice: str = "longxiaochun"  # Voice name for Qwen TTS
    # Qwen STT: sensevoice-v1, paraformer-v2, paraformer-realtime-v2
    qwen_stt_model: str = "sensevoice-v1"

    # ── Ollama Settings (LOCAL Qwen - 100% FREE Forever!) ───────────
    # Download: https://ollama.com  |  Models: https://ollama.com/library/qwen3
    # No API key needed! Runs on your own machine.
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434/v1"
        )
    )
    # Local Qwen models (download via: ollama pull qwen3:8b)
    # Small (CPU):  qwen3:0.6b, qwen3:1.7b, qwen3:4b
    # Medium (8GB): qwen3:8b, qwen2.5:7b
    # Large (16GB): qwen3:14b, qwen3:32b
    # Huge (48GB+): qwen3:235b-a22b (MoE)
    ollama_llm_model: str = "qwen3:8b"

    # ── ElevenLabs Settings (Premium Multilingual TTS) ────────────────
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))

    # ── STT Provider: "local" (FREE), "openai", "google", "azure", "dashscope" ──
    stt_provider: str = field(default_factory=lambda: os.getenv("STT_PROVIDER", "openai"))

    # ── TTS Provider: "pyttsx3" (FREE offline), "edge" (FREE), "openai", "azure", "dashscope" ──
    tts_provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "openai"))

    # ── LLM Provider: "openai", "dashscope", "ollama" ───────────────
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama"))

    # ── Local Whisper STT Settings (FREE - no API key) ──────────────
    # faster-whisper models: tiny, base, small, medium, large-v3
    # tiny (~75MB) | base (~150MB) | small (~500MB) | medium (~1.5GB)
    local_whisper_model: str = field(
        default_factory=lambda: os.getenv("LOCAL_WHISPER_MODEL", "base")
    )

    # ── Audio Settings ────────────────────────────────────────────────
    sample_rate: int = 16000
    audio_format: str = "wav"

    # ── Server Settings ───────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Language display names ────────────────────────────────────────
    language_names: dict = field(default_factory=lambda: {
        "ur": "اردو (Urdu)",
        "sd": "سنڌي (Sindhi)",
        "en": "English",
    })

    def validate(self):
        """Validate that required API keys are set."""
        errors = []
        if self.stt_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required for OpenAI STT")
        if self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required for OpenAI LLM")
        if self.tts_provider == "azure" and not self.azure_speech_key:
            errors.append("AZURE_SPEECH_KEY is required for Azure TTS")
        if self.tts_provider == "elevenlabs" and not self.elevenlabs_api_key:
            errors.append("ELEVENLABS_API_KEY is required for ElevenLabs TTS")
        if self.stt_provider == "dashscope" and not self.dashscope_api_key:
            errors.append("DASHSCOPE_API_KEY is required for Alibaba DashScope STT")
        if self.llm_provider == "dashscope" and not self.dashscope_api_key:
            errors.append("DASHSCOPE_API_KEY is required for Alibaba Qwen LLM")
        if self.llm_provider == "ollama":
            # Ollama is free - just check if running
            pass  # No key needed
        if self.stt_provider == "local":
            # Local Whisper is free - no key needed
            pass
        if self.tts_provider == "pyttsx3":
            # pyttsx3 is offline - no key needed
            pass
        if self.tts_provider == "edge":
            # Edge TTS is free - no key needed
            pass
        if self.tts_provider == "dashscope" and not self.dashscope_api_key:
            errors.append("DASHSCOPE_API_KEY is required for Alibaba Qwen TTS")
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
