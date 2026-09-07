"""
Voice Medical Agent - Main Orchestrator
Yeh file STT → Doctor Agent → TTS ka poora flow manage karti hai.
"""
import asyncio
import logging
import time
from typing import Optional

from config import Config
from stt import SpeechToText
from doctor_agent import DoctorAgent
from medical_knowledge import MedicalKnowledgeBase
from tts import TextToSpeech

logger = logging.getLogger(__name__)


class VoiceMedicalAgent:
    """
    Main agent that orchestrates the full voice pipeline:

    User Voice → [STT] → Patient Text → [Doctor Agent] → Doctor Text → [TTS] → Doctor Voice

    Supports: Urdu (ur), Sindhi (sd), English (en)
    """

    def __init__(
        self,
        config: Config,
        language: str = "ur",
        knowledge_base: MedicalKnowledgeBase | None = None,
    ):
        self.config = config
        self.stt = SpeechToText(config)
        self.doctor = DoctorAgent(
            config, language=language, knowledge_base=knowledge_base
        )
        self.tts = TextToSpeech(config)
        self.language = language
        self.is_active = False
        self.session_id: Optional[str] = None

    async def start_session(self, session_id: str) -> dict:
        """
        Start a new consultation session.
        Returns greeting audio + text.
        """
        self.session_id = session_id
        self.is_active = True
        self.doctor.reset_conversation()

        # Get greeting
        greeting_text = await self.doctor.get_greeting()

        # Convert greeting to speech
        tts_result = await self.tts.synthesize(greeting_text, self.language)

        logger.info(f"Session started: {session_id} | Language: {self.language}")

        return {
            "session_id": session_id,
            "greeting_text": greeting_text,
            "greeting_audio": tts_result["audio_data"],
            "audio_format": tts_result["format"],
            "language": self.language,
        }

    async def process_voice_input(
        self,
        audio_data: bytes,
        file_extension: str = "wav",
    ) -> dict:
        """
        Process user's voice input and return doctor's response.

        Full pipeline:
        1. STT: Convert voice to text
        2. LLM: Get doctor's response
        3. TTS: Convert response to voice

        Args:
            audio_data: Raw audio bytes from user's microphone
            file_extension: Audio file format

        Returns:
            dict with patient_text, doctor_text, doctor_audio, audio_format
        """
        if not self.is_active:
            raise RuntimeError("Session not started. Call start_session() first.")

        pipeline_start = time.perf_counter()

        # Step 1: Speech-to-Text
        logger.info("Step 1: Transcribing user audio...")
        stt_start = time.perf_counter()
        stt_result = await self.stt.transcribe(
            audio_data, self.language, file_extension
        )
        stt_time = time.perf_counter() - stt_start
        patient_text = stt_result["text"]
        logger.info("⏱ STT took %.2fs", stt_time)

        if not patient_text.strip():
            # If transcription is empty, ask user to repeat
            sorry_text = {
                "ur": "معذرت، میں آپ کی بات سمجھ نہیں سکا۔ براہ کرم دوبارہ بولیں۔",
                "sd": "معاف ڪجو، مان توهان جي ڳالهه سمجهي نه سگهيس. مهرباني ڪري ٻيهر ڳالهايو.",
                "en": "Sorry, I couldn't understand. Please speak again.",
            }
            text = sorry_text.get(self.language, sorry_text["ur"])
            tts_result = await self.tts.synthesize(text, self.language)
            return {
                "patient_text": "",
                "doctor_text": text,
                "doctor_audio": tts_result["audio_data"],
                "audio_format": tts_result["format"],
                "status": "retry",
            }

        logger.info(f"Patient said: {patient_text}")

        # Step 2: Doctor Agent Response (medical context search + LLM)
        logger.info("Step 2: Getting doctor response...")
        llm_start = time.perf_counter()
        doctor_text = await self.doctor.get_response(patient_text)
        llm_time = time.perf_counter() - llm_start
        logger.info("⏱ LLM (context search + generation) took %.2fs", llm_time)
        logger.info(f"Doctor said: {doctor_text}")

        # Step 3: Text-to-Speech
        logger.info("Step 3: Synthesizing doctor's speech...")
        tts_start = time.perf_counter()
        tts_result = await self.tts.synthesize(doctor_text, self.language)
        tts_time = time.perf_counter() - tts_start
        logger.info("⏱ TTS took %.2fs", tts_time)

        total_time = time.perf_counter() - pipeline_start
        logger.info(
            "⏱ TOTAL PIPELINE: %.2fs (STT %.2fs | LLM %.2fs | TTS %.2fs)",
            total_time,
            stt_time,
            llm_time,
            tts_time,
        )

        return {
            "patient_text": patient_text,
            "doctor_text": doctor_text,
            "doctor_audio": tts_result["audio_data"],
            "audio_format": tts_result["format"],
            "stt_confidence": stt_result["confidence"],
            "status": "success",
        }

    async def end_session(self) -> dict:
        """End the current consultation session."""
        farewell_text = {
            "ur": "اپنا خیال رکھیں۔ اگر علامات بڑھیں تو فوری ڈاکٹر سے ملیں۔ اللہ حافظ!",
            "sd": "پنهنجو خيال رکو. جيڪڏهن علامتون وڌن ته فوري ڊاڪٽر سان ملو. الله حافظ!",
            "en": "Take care of yourself. If symptoms worsen, please see a doctor immediately. Goodbye!",
        }
        text = farewell_text.get(self.language, farewell_text["ur"])
        tts_result = await self.tts.synthesize(text, self.language)

        self.is_active = False
        summary = self.doctor.get_conversation_summary()

        return {
            "farewell_text": text,
            "farewell_audio": tts_result["audio_data"],
            "audio_format": tts_result["format"],
            "conversation_summary": summary,
        }

    def switch_language(self, language: str):
        """Switch the language for the current session."""
        self.language = language
        self.doctor.set_language(language)
        logger.info(f"Language switched to: {language}")
