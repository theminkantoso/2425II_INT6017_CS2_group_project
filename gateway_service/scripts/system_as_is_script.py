import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main.services import ocr_service, pdf_service, translation_service


async def run_system_as_is():
    import os

    text = await ocr_service.image_to_text(
        image_path=os.path.join(os.getcwd(), "scripts", "sample.png")
    )
    translated_text = await translation_service.translate(text)
    await pdf_service.text_to_pdf(
        text=translated_text,
        output_filename=os.path.join(os.getcwd(), "scripts", "output.pdf"),
    )


if __name__ == "__main__":
    asyncio.run(run_system_as_is())
