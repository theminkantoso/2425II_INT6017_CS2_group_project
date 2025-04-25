from google.cloud import storage
from pathlib import Path
from typing import Optional
from datetime import timedelta
import os

class GCSService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
        self.bucket = self.storage_client.bucket(self.bucket_name)

    async def get_presigned_url(self, file_bytes: bytes, destination_blob_name: str, content_type: Optional[str] = None) -> str:
        """
        Create a presigned url for uploading a file to Google Cloud Storage.
        
        Args:
            file_bytes: The file content in bytes
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
            content_type="application/octet-stream"
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