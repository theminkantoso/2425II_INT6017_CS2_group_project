import pytesseract
from PIL import Image


async def image_to_text(image_path: str) -> str:
    """
    Convert an image to text using OCR.
    """

    # Load the image from the specified path
    image = Image.open(image_path)

    # Use pytesseract to do OCR on the image
    text = pytesseract.image_to_string(image)

    return text
