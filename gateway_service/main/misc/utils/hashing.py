import hashlib


def calculate_image_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()
