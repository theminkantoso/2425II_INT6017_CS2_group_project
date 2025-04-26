import asyncio

from googletrans import Translator

translator = Translator()


async def translate(text):
    retries = 3
    delay = 1  # Initial delay in seconds

    for attempt in range(retries):
        try:
            result = await translator.translate(text, src="en", dest="vi")
            return result.text
        except Exception as e:
            if attempt < retries - 1:  # Check if retries are remaining
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise e
