import pytesseract
from PIL import ImageFile


async def image_to_text(image: ImageFile.ImageFile) -> str:
    """
    Convert an image to text using OCR.
    """

    # Use pytesseract to do OCR on the image
    text = pytesseract.image_to_string(image)

    return text
