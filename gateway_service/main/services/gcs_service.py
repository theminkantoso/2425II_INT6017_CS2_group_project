import aiohttp
from google.cloud import storage
from typing import Optional
from datetime import timedelta

from main import config
from main.misc.exceptions import BadRequest


class GCSService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket_name = config.GCS_BUCKET_NAME
        self.bucket = self.storage_client.bucket(self.bucket_name)

    async def get_presigned_url(
        self, destination_blob_name: str, content_type: Optional[str] = None
    ) -> str:
        """
        Create a presigned url for uploading a file to Google Cloud Storage.

        Args:
            destination_blob_name: The name of the file in GCS (including path)
            content_type: The content type of the file (e.g., 'image/jpeg')

        Returns:
            The presigned url for uploading a file to Google Cloud Storage
        """
        blob = self.bucket.blob(destination_blob_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type,
        )

        # Return the public URL
        return url

    async def delete_file(self, blob_name: str) -> None:
        """Delete a file from Google Cloud Storage."""
        blob = self.bucket.blob(blob_name)
        blob.delete()

    def get_file_url(self, blob_name: str) -> str:
        """Get the public URL for a file."""
        blob = self.bucket.blob(blob_name)
        return blob.public_url


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

            # content_type = response.headers.get("Content-Type", "")
            # if not content_type.startswith("image/"):
            #     raise BadRequest(
            #         error_message=f"File is not an image (Content-Type: {content_type})"
            #     )

            return await response.read()
