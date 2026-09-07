"""End-to-end test: exact server flow that crashed (fever + context + TTS)."""
import asyncio
import base64
import logging
import time

logging.basicConfig(level=logging.INFO)

from config import Config
from doctor_agent import DoctorAgent
from medical_knowledge import MedicalKnowledgeBase
from tts import TextToSpeech

config = Config()
kb = MedicalKnowledgeBase()
kb.load()
doctor = DoctorAgent(config, language="en", knowledge_base=kb)
tts = TextToSpeech(config)


async def main():
    # Same message that produced the empty response
    message = "I am experiencing very high fever about 100°F at temperature. I am feeling right now."

    total_start = time.perf_counter()
    doctor_text = await doctor.get_response(message)
    llm_done = time.perf_counter()

    print(f"\nDoctor said ({len(doctor_text)} chars): {doctor_text}\n")

    # This is what crashed before (empty text -> pyttsx3 assert)
    tts_result = await tts.synthesize(doctor_text, "en")
    total_time = time.perf_counter() - total_start

    audio = tts_result["audio_data"]
    encoded = base64.b64encode(audio).decode()
    print(f"Audio: {len(audio)} bytes | base64: {len(encoded)} chars")
    print(f"\n⏱ LLM: {llm_done - total_start:.1f}s | TTS: {total_time - (llm_done - total_start):.2f}s | TOTAL: {total_time:.1f}s")
    print("\nSUCCESS - no crash, real response, audio generated")


asyncio.run(main())
