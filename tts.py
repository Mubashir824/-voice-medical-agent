"""
Text-to-Speech Module
Doctor ki text response ko Urdu/Sindhi voice mein convert karta hai.

Supported Providers:
  - Edge TTS (FREE, no API key, Microsoft Edge voices - great Urdu/English)
  - OpenAI TTS (fast, decent quality, but limited Urdu/Sindhi support)
  - Google Cloud TTS (good Urdu support)
  - Azure Neural TTS (BEST for Urdu + Sindhi - recommended)
  - ElevenLabs (Premium quality, multilingual)
  - Alibaba DashScope / Qwen TTS (CosyVoice - multilingual)
"""
import io
import os
import tempfile
from typing import Optional

from openai import OpenAI

from config import Config


class TextToSpeech:
    """Handles converting text responses to speech in Urdu or Sindhi."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = config.tts_provider
        self._openai_client: Optional[OpenAI] = None

    @property
    def openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=self.config.openai_api_key)
        return self._openai_client

    # ── Public API ─────────────────────────────────────────────────────

    async def synthesize(
        self,
        text: str,
        language: str = "ur",
    ) -> dict:
        """
        Convert text to speech audio.

        Args:
            text: The text to convert to speech
            language: ISO 639-1 code ("ur" for Urdu, "sd" for Sindhi)

        Returns:
            dict with keys: audio_data (bytes), format (str), language (str)
        """
        # pyttsx3 and other engines crash (bare assert) on empty text.
        # Fail fast with a clear message instead of a cryptic traceback.
        if not text or not text.strip():
            raise ValueError("TTS received empty text - nothing to synthesize")

        if self.provider == "pyttsx3":
            return await self._synthesize_pyttsx3(text, language)
        elif self.provider == "edge":
            return await self._synthesize_edge(text, language)
        elif self.provider == "openai":
            return await self._synthesize_openai(text, language)
        elif self.provider == "google":
            return await self._synthesize_google(text, language)
        elif self.provider == "azure":
            return await self._synthesize_azure(text, language)
        elif self.provider == "elevenlabs":
            return await self._synthesize_elevenlabs(text, language)
        elif self.provider == "dashscope":
            return await self._synthesize_dashscope(text, language)
        else:
            raise ValueError(f"Unknown TTS provider: {self.provider}")

    # ── pyttsx3 TTS (OFFLINE - Windows SAPI5, 100% free, no network) ──

    async def _synthesize_pyttsx3(self, text: str, language: str) -> dict:
        """
        Use pyttsx3 for offline TTS via Windows SAPI5.
        100% FREE, no internet needed, works behind corporate firewalls.
        Voice quality is basic but functional.
        """
        import asyncio
        import os
        import tempfile

        def _do_tts():
            """Run pyttsx3 synchronously (called via asyncio.to_thread)."""
            import pyttsx3

            engine = pyttsx3.init()

            # Try to find a matching voice for the language
            voices = engine.getProperty("voices")
            lang_map = {
                "ur": ["urdu", "ur"],
                "sd": ["sindhi", "sd", "urdu", "ur"],
                "en": ["english", "en"],
            }
            keywords = lang_map.get(language, ["english"])

            selected_voice = None
            for voice in voices:
                for kw in keywords:
                    if kw in voice.name.lower() or kw in voice.id.lower():
                        selected_voice = voice.id
                        break
                if selected_voice:
                    break

            if selected_voice:
                engine.setProperty("voice", selected_voice)

            # Set speech rate (slightly slower for clarity)
            engine.setProperty("rate", 140)

            # Save to temp WAV file
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as f:
                temp_path = f.name

            engine.save_to_file(text, temp_path)
            engine.runAndWait()

            # Read the WAV file
            with open(temp_path, "rb") as f:
                audio_data = f.read()

            os.unlink(temp_path)

            return audio_data

        audio_data = await asyncio.to_thread(_do_tts)

        if not audio_data:
            raise RuntimeError("pyttsx3 returned empty audio")

        return {
            "audio_data": audio_data,
            "format": "wav",
            "language": language,
        }

    # ── Edge TTS (FREE - Microsoft Edge voices) ─────────────────────

    async def _synthesize_edge(self, text: str, language: str) -> dict:
        """
        Use Microsoft Edge TTS (100% FREE, no API key needed).
        High quality neural voices for Urdu, English, and many languages.

        Voices:
          - Urdu:   ur-PK-UzmaNeural (female), ur-PK-AsadNeural (male)
          - Sindhi: sd-PK-ShaziaNeural (female) - fallback to Urdu if unavailable
          - English: en-US-JennyNeural (female), en-US-GuyNeural (male)
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError(
                "Install edge-tts: pip install edge-tts"
            )

        # Map languages to Edge TTS voice names
        voice_map = {
            "ur": "ur-PK-UzmaNeural",      # Urdu female
            "sd": "ur-PK-UzmaNeural",       # Sindhi fallback to Urdu
            "en": "en-US-JennyNeural",      # English female
        }
        voice = voice_map.get(language, voice_map["ur"])

        # Collect all audio chunks into bytes
        # Use a custom connector with SSL verification disabled
        # to handle corporate proxy/firewall SSL interception
        import ssl
        import aiohttp

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        communicate = edge_tts.Communicate(text, voice, connector=connector)

        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        audio_data = b"".join(audio_chunks)

        if not audio_data:
            raise RuntimeError("Edge TTS returned empty audio")

        return {
            "audio_data": audio_data,
            "format": "mp3",
            "language": language,
        }

    # ── OpenAI TTS ────────────────────────────────────────────────────

    async def _synthesize_openai(self, text: str, language: str) -> dict:
        """
        Use OpenAI TTS API.
        Note: OpenAI TTS works best for English. For Urdu/Sindhi,
        it may not pronounce correctly. Use Azure for best results.
        """
        response = self.openai_client.audio.speech.create(
            model=self.config.tts_model,
            voice=self.config.tts_voice,
            input=text,
            response_format="mp3",
        )

        audio_data = response.content

        return {
            "audio_data": audio_data,
            "format": "mp3",
            "language": language,
        }

    # ── Google Cloud TTS ──────────────────────────────────────────────

    async def _synthesize_google(self, text: str, language: str) -> dict:
        """
        Use Google Cloud Text-to-Speech.
        Supports Urdu voices (ur-PK-Wavenet-A/B).
        """
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise ImportError(
                "Install google-cloud-texttospeech: "
                "pip install google-cloud-texttospeech"
            )

        client = texttospeech.TextToSpeechClient()

        # Map languages to Google TTS voice configs
        voice_configs = {
            "ur": {
                "language_code": "ur-PK",
                "name": "ur-PK-Wavenet-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE,
            },
            "sd": {
                # Google doesn't support Sindhi natively, fallback to Urdu
                "language_code": "ur-PK",
                "name": "ur-PK-Wavenet-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE,
            },
            "en": {
                "language_code": "en-US",
                "name": "en-US-Neural2-C",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE,
            },
        }

        voice_config = voice_configs.get(language, voice_configs["ur"])

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(**voice_config)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,  # Slightly slower for clarity
            pitch=0.0,
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return {
            "audio_data": response.audio_content,
            "format": "mp3",
            "language": language,
        }

    # ── Azure Neural TTS (RECOMMENDED for Urdu + Sindhi) ──────────────

    async def _synthesize_azure(self, text: str, language: str) -> dict:
        """
        Use Azure Neural Text-to-Speech.
        BEST option for both Urdu and Sindhi:
          - Urdu: ur-PK-UzmaNeural (female), ur-PK-AsadNeural (male)
          - Sindhi: sd-PK-ShaziaNeural (female), sd-PK-ZainNeural (male)
        """
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            raise ImportError(
                "Install azure-cognitiveservices-speech: "
                "pip install azure-cognitiveservices-speech"
            )

        # Azure Neural voices for Urdu and Sindhi
        voice_configs = {
            "ur": {
                "lang": "ur-PK",
                "voice": "ur-PK-UzmaNeural",  # Female Urdu voice
            },
            "sd": {
                "lang": "sd-PK",
                "voice": "sd-PK-ShaziaNeural",  # Female Sindhi voice
            },
            "en": {
                "lang": "en-US",
                "voice": "en-US-JennyNeural",
            },
        }

        voice_config = voice_configs.get(language, voice_configs["ur"])

        speech_config = speechsdk.SpeechConfig(
            subscription=self.config.azure_speech_key,
            region=self.config.azure_speech_region,
        )
        speech_config.speech_synthesis_voice_name = voice_config["voice"]

        # Output to memory stream
        stream = speechsdk.audio.PushAudioOutputStream(
            _AudioOutputCallback()
        )
        audio_config = speechsdk.audio.AudioOutputConfig(stream=stream)

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data = result.audio_data
        else:
            raise RuntimeError(
                f"Azure TTS failed: {result.reason}"
            )

        return {
            "audio_data": audio_data,
            "format": "wav",
            "language": language,
        }

    # ── ElevenLabs (Premium Quality) ──────────────────────────────────

    async def _synthesize_elevenlabs(self, text: str, language: str) -> dict:
        """
        Use ElevenLabs TTS API.
        Premium quality, good multilingual support.
        """
        import httpx

        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - good for multilingual

        headers = {
            "xi-api-key": self.config.elevenlabs_api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Best for non-English
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()

        return {
            "audio_data": response.content,
            "format": "mp3",
            "language": language,
        }

    # ── Alibaba DashScope TTS (Qwen TTS / CosyVoice) ─────────────────

    async def _synthesize_dashscope(self, text: str, language: str) -> dict:
        """
        Use Alibaba Cloud DashScope TTS (Qwen TTS / CosyVoice).

        Models available on DashScope:
          - cosyvoice-v2: Latest CosyVoice, multilingual
          - qwen-tts: Qwen3-TTS (10 languages, Urdu/Sindhi may vary)

        Note: Qwen3-TTS officially supports 10 languages:
        Chinese, English, Japanese, Korean, German, French,
        Russian, Portuguese, Spanish, Italian.
        Urdu/Sindhi support is experimental - test thoroughly.

        For best Urdu/Sindhi TTS, Azure Neural is still recommended.
        """
        try:
            import dashscope
            from dashscope.audio.tts_v2 import SpeechSynthesizer
        except ImportError:
            raise ImportError(
                "Install dashscope SDK: pip install dashscope"
            )

        dashscope.api_key = self.config.dashscope_api_key

        synthesizer = SpeechSynthesizer(
            model=self.config.qwen_tts_model,
            voice=self.config.qwen_tts_voice,
        )

        audio_data = synthesizer.call(text)

        if audio_data:
            return {
                "audio_data": audio_data,
                "format": "mp3",
                "language": language,
            }
        else:
            raise RuntimeError("DashScope TTS returned empty audio")


# Only define the callback class if Azure SDK is installed.
# This avoids a NameError at module load time when azure is not available.
try:
    import azure.cognitiveservices.speech as speechsdk

    class _AudioOutputCallback(speechsdk.audio.PushAudioOutputStreamCallback):
        """Helper class for Azure TTS audio output to memory."""

        def __init__(self):
            super().__init__()
            self._buffer = io.BytesIO()

        def write(self, audio_buffer: memoryview) -> int:
            self._buffer.write(audio_buffer)
            return len(audio_buffer)

        def close(self):
            self._buffer.seek(0)

except ImportError:
    # Azure SDK not installed - _AudioOutputCallback won't be needed
    # unless the user configures TTS_PROVIDER=azure
    _AudioOutputCallback = None  # type: ignore
