from fastapi import APIRouter
from main.services import translation_service

router: APIRouter = APIRouter()


@router.post("/api/translate")
async def translate_text(input_text: str):
    translated_text = await translation_service.translate(text=input_text)
