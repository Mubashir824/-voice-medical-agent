"""Quick benchmark: measure LLM response time with /no_think fix."""
import logging
import time

logging.basicConfig(level=logging.INFO)

from config import Config
from doctor_agent import DoctorAgent
from medical_knowledge import MedicalKnowledgeBase

config = Config()
kb = MedicalKnowledgeBase()
kb.load()

doctor = DoctorAgent(config, language="en", knowledge_base=kb)

# Verify /no_think is in the system prompt
sys_msg = doctor.conversation_history[0]["content"]
print(f"/no_think in system prompt: {'/no_think' in sys_msg}")
print()

# Test 1: with medical context (real scenario)
print("Testing: 'I have fever and headache'...")
start = time.perf_counter()
response = asyncio_run = None

import asyncio

async def main():
    start = time.perf_counter()
    response = await doctor.get_response("I have fever and headache since yesterday")
    elapsed = time.perf_counter() - start
    print(f"Response time: {elapsed:.2f}s")
    print(f"Response: {response[:200]}")

asyncio.run(main())
