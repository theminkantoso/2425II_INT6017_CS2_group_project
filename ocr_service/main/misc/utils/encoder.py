import base64


def encode_text(input_text: str) -> str:
    return base64.b64encode(input_text.encode("utf-8")).decode("utf-8")
