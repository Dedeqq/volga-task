"""S3 storage client for managing audio files."""

import boto3
from botocore.exceptions import ClientError
from app.config import settings
from typing import Optional
import os


class S3Client:
    """Handle S3 operations for audio storage."""

    def __init__(self):
        """Initialize S3 client."""
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
        )
        self.bucket = settings.S3_BUCKET

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a file to S3.

        Args:
            local_path: Local file path
            s3_key: S3 object key (path)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.upload_file(local_path, self.bucket, s3_key)
            return True
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            return False

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3.

        Args:
            s3_key: S3 object key (path)
            local_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.download_file(self.bucket, s3_key, local_path)
            return True
        except ClientError as e:
            print(f"Error downloading file from S3: {e}")
            return False

    def get_file_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for a file.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL or None if error
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False
