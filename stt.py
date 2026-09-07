"""
Speech-to-Text Module
User ki voice (Urdu/Sindhi) ko text mein convert karta hai.

Supported Providers:
  - Local Whisper (FREE, runs Whisper model on your machine - no API key)
  - OpenAI Whisper (best for Urdu, decent for Sindhi)
  - Google Cloud Speech (good for Urdu)
  - Azure Speech (good for Urdu + Sindhi)
  - Alibaba DashScope (SenseVoice / Paraformer - multilingual)
"""
import io
import os
import tempfile
from pathlib import Path
from typing import Optional

from openai import OpenAI

from config import Config


class SpeechToText:
    """Handles converting audio input to text in Urdu or Sindhi."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = config.stt_provider
        self._openai_client: Optional[OpenAI] = None

    @property
    def openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=self.config.openai_api_key)
        return self._openai_client

    # ── Public API ─────────────────────────────────────────────────────

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ur",
        file_extension: str = "wav",
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes (from microphone or uploaded file)
            language: ISO 639-1 code ("ur" for Urdu, "sd" for Sindhi)
            file_extension: Audio format (wav, mp3, webm, ogg, m4a)

        Returns:
            dict with keys: text, language, confidence
        """
        if self.provider == "local":
            return await self._transcribe_local(audio_data, language, file_extension)
        elif self.provider == "openai":
            return await self._transcribe_openai(audio_data, language, file_extension)
        elif self.provider == "google":
            return await self._transcribe_google(audio_data, language)
        elif self.provider == "azure":
            return await self._transcribe_azure(audio_data, language)
        elif self.provider == "dashscope":
            return await self._transcribe_dashscope(audio_data, language, file_extension)
        else:
            raise ValueError(f"Unknown STT provider: {self.provider}")

    # ── Local Whisper (FREE - no API key) ───────────────────────────

    async def _transcribe_local(
        self,
        audio_data: bytes,
        language: str,
        file_extension: str,
    ) -> dict:
        """
        Use faster-whisper to transcribe locally. 100% FREE, no API key.
        Downloads the Whisper model on first use (~150MB for 'base' model).

        Models:
          - tiny:   fastest, least accurate (~75MB)
          - base:   good balance (~150MB)
          - small:  more accurate (~500MB)
          - medium: best for Urdu/Sindhi (~1.5GB)
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "Install faster-whisper: pip install faster-whisper"
            )

        import asyncio

        # Use 'base' model by default (good balance of speed + accuracy)
        model_size = getattr(self.config, "local_whisper_model", "base")

        # Write audio to temp file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}", delete=False
        ) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            # Load model and transcribe (runs in thread to not block async)
            def _transcribe():
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                lang_map = {"ur": "ur", "sd": "sd", "en": "en"}
                whisper_lang = lang_map.get(language, "ur")

                segments, info = model.transcribe(
                    temp_path,
                    language=whisper_lang,
                    beam_size=5,
                    vad_filter=True,
                )
                text = " ".join(seg.text for seg in segments)
                confidence = info.avg_logprob if hasattr(info, "avg_logprob") else 0.0
                return text.strip(), confidence

            text, confidence = await asyncio.to_thread(_transcribe)

            return {
                "text": text,
                "language": language,
                "confidence": confidence,
            }
        finally:
            os.unlink(temp_path)

    # ── OpenAI Whisper ────────────────────────────────────────────────

    async def _transcribe_openai(
        self,
        audio_data: bytes,
        language: str,
        file_extension: str,
    ) -> dict:
        """
        Use OpenAI Whisper API for transcription.
        Whisper Urdu support is excellent.
        Whisper Sindhi support is basic (works better with clear speech).
        """
        # Whisper needs a file-like object with a name
        filename = f"audio.{file_extension}"
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename

        response = self.openai_client.audio.transcriptions.create(
            model=self.config.stt_model,
            file=audio_file,
            language=language,  # Helps Whisper focus on the right language
            response_format="verbose_json",
            prompt=self._get_language_prompt(language),
        )

        return {
            "text": response.text.strip(),
            "language": language,
            "confidence": getattr(response, "avg_logprob", 0.0),
        }

    def _get_language_prompt(self, language: str) -> str:
        """Provide context hints to Whisper for better accuracy."""
        prompts = {
            "ur": "یہ ایک طبی مشاورت ہے۔ مریض اپنے علامات بیان کر رہا ہے۔",
            "sd": "هي هڪ طبي مشاورت آهي. مريض پنهنجا علامتون بيان ڪري رهيو آهي.",
            "en": "This is a medical consultation. The patient is describing their symptoms.",
        }
        return prompts.get(language, prompts["ur"])

    # ── Google Cloud Speech ────────────────────────────────────────────

    async def _transcribe_google(self, audio_data: bytes, language: str) -> dict:
        """
        Use Google Cloud Speech-to-Text.
        Supports Urdu ("ur-PK") but limited Sindhi support.
        """
        try:
            from google.cloud import speech_v1p1beta1 as speech
        except ImportError:
            raise ImportError(
                "Install google-cloud-speech: pip install google-cloud-speech"
            )

        client = speech.SpeechClient()

        # Map our language codes to Google BCP-47 tags
        lang_map = {"ur": "ur-PK", "sd": "sd-PK", "en": "en-US"}
        google_lang = lang_map.get(language, "ur-PK")

        audio = speech.RecognitionAudio(content=audio_data)
        config_recognition = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.config.sample_rate,
            language_code=google_lang,
            enable_automatic_punctuation=True,
        )

        response = client.recognize(config=config_recognition, audio=audio)

        text = " ".join(result.alternatives[0].transcript for result in response.results)
        confidence = (
            response.results[0].alternatives[0].confidence if response.results else 0.0
        )

        return {
            "text": text.strip(),
            "language": language,
            "confidence": confidence,
        }

    # ── Azure Speech ──────────────────────────────────────────────────

    async def _transcribe_azure(self, audio_data: bytes, language: str) -> dict:
        """
        Use Azure Speech Services.
        Best coverage for both Urdu ("ur-PK") and Sindhi ("sd-PK").
        """
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            raise ImportError(
                "Install azure-cognitiveservices-speech: "
                "pip install azure-cognitiveservices-speech"
            )

        lang_map = {"ur": "ur-PK", "sd": "sd-PK", "en": "en-US"}
        azure_lang = lang_map.get(language, "ur-PK")

        speech_config = speechsdk.SpeechConfig(
            subscription=self.config.azure_speech_key,
            region=self.config.azure_speech_region,
        )
        speech_config.speech_recognition_language = azure_lang

        # Write audio to temp file for Azure
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, audio_config=audio_config
            )
            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    "text": result.text.strip(),
                    "language": language,
                    "confidence": 0.9,
                }
            else:
                return {"text": "", "language": language, "confidence": 0.0}
        finally:
            os.unlink(temp_path)

    # ── Alibaba DashScope (SenseVoice / Paraformer) ──────────────────

    async def _transcribe_dashscope(
        self,
        audio_data: bytes,
        language: str,
        file_extension: str,
    ) -> dict:
        """
        Use Alibaba Cloud DashScope speech recognition.
        Models:
          - sensevoice-v1: Multilingual, supports 50+ languages
          - paraformer-v2: High accuracy, mainly Chinese + English
          - paraformer-realtime-v2: Real-time streaming

        Note: SenseVoice has broad multilingual support.
        Urdu/Sindhi accuracy may vary - test with clear speech.
        """
        try:
            import dashscope
            from dashscope.audio.asr import Transcription
        except ImportError:
            raise ImportError(
                "Install dashscope SDK: pip install dashscope"
            )

        dashscope.api_key = self.config.dashscope_api_key

        # Write audio to temp file (DashScope needs file path or URL)
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}", delete=False
        ) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            # Use Transcription API for non-real-time recognition
            task = Transcription.async_call(
                model=self.config.qwen_stt_model,
                file_urls=[temp_path],  # Local file path
                language_hints=[language],  # Language hint
            )

            # Wait for result
            result = Transcription.wait(task.output.task_id)

            if result.status_code == 200:
                # Extract text from results
                text = ""
                for res in result.output.get("results", []):
                    text += res.get("text", "")

                return {
                    "text": text.strip(),
                    "language": language,
                    "confidence": 0.8,
                }
            else:
                return {"text": "", "language": language, "confidence": 0.0}

        finally:
            os.unlink(temp_path)
