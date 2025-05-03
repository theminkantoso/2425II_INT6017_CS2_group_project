import asyncio
import io

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


async def text_to_pdf(text, output_filename="output.pdf"):
    """
    Asynchronously converts text to a PDF file with proper Unicode support for Vietnamese.

    Args:
        text (str): The text to be saved in the PDF.
        output_filename (str, optional): The name of the output PDF file. Defaults to "output.pdf".

    Returns:
        str: Path to the saved PDF file.
    """

    # Define a coroutine that does the actual PDF creation work
    async def create_pdf():
        # This is a CPU-bound task, so we'll run it in a thread pool
        return await asyncio.to_thread(_create_pdf_sync, text, output_filename)

    # Actual PDF creation function that will run in a thread pool
    def _create_pdf_sync(text, filename):
        # Register DejaVu Sans font which has good Unicode support
        font_path = os.path.join(os.getcwd(), "main", "commons", "Roboto-Regular.ttf")

        # Register the font if the file exists
        pdfmetrics.registerFont(TTFont("Roboto-Regular", font_path))
        font_name = "Roboto-Regular"

        # Set up the document with letter page size
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        # Use default style for paragraphs with Unicode font
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontName = "Roboto-Regular"  # Use the registered Unicode font

        # Split the text into paragraphs and add them to the story
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            p = Paragraph(para.replace("\n", "<br/>"), style)
            story.append(p)
            story.append(Spacer(1, 12))  # Add some space between paragraphs

        # Build the PDF
        doc.build(story)
        return filename

    # Execute the coroutine and return the result
    result = await create_pdf()
    return result


async def text_to_pdf_in_memory(text: str) -> io.BytesIO:
    """
    Asynchronously generates a PDF file in memory from the given text.

    Args:
        text (str): The text to be saved in the PDF.

    Returns:
        io.BytesIO: In-memory PDF file.
    """

    def _create_pdf_bytes():
        buffer = io.BytesIO()

        # Register Unicode-supporting font (Roboto or DejaVu)
        font_path = os.path.join(os.getcwd(), "main", "commons", "Roboto-Regular.ttf")
        pdfmetrics.registerFont(TTFont("Roboto-Regular", font_path))

        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontName = "Roboto-Regular"

        story = []
        for para in text.split("\n\n"):
            story.append(Paragraph(para.replace("\n", "<br/>"), style))
            story.append(Spacer(1, 12))

        doc.build(story)
        buffer.seek(0)  # rewind to the beginning
        return buffer

    return await asyncio.to_thread(_create_pdf_bytes)
