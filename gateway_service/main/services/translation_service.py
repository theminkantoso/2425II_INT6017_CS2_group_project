from googletrans import Translator

translator = Translator()


async def translate(text):
    try:
        result = await translator.translate(text, src="en", dest="vi")
        return result.text
    except Exception as e:
        raise e
