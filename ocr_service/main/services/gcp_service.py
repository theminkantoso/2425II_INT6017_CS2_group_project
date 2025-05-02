import aiohttp

from main.misc.exceptions import BadRequest


async def download_image_from_gcs_to_memory(public_url: str) -> bytes:
    """
    Downloads an image file from a public Google Cloud Storage URL into memory.
    Only proceeds if the file is an image based on Content-Type.

    :param public_url: Public GCS file URL
    :return: Image content as bytes
    :raises: Exception if file is not an image
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(public_url) as response:
            if response.status != 200:
                raise BadRequest(
                    error_message=f"Failed to download file: HTTP {response.status}"
                )

            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                raise BadRequest(
                    error_message=f"File is not an image (Content-Type: {content_type})"
                )

            return await response.read()
