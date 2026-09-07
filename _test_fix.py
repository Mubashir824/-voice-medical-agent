import asyncio
import base64
from config import Config
from tts import TextToSpeech


async def test():
    config = Config()
    tts = TextToSpeech(config)

    # This is exactly what start_session() does
    greeting = "Hello! I'm your medical consultation assistant."
    result = await tts.synthesize(greeting, "en")

    audio = result["audio_data"]
    print(f"Audio type: {type(audio)}")
    print(f"Audio bytes: {len(audio)}")
    print(f"Format: {result['format']}")

    # This is the line that crashed before
    encoded = base64.b64encode(audio).decode()
    print(f"Base64 encoded length: {len(encoded)}")
    print("SUCCESS - no more coroutine error!")


asyncio.run(test())
