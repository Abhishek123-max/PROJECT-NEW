"""StorageService

Lightweight storage service that uploads files to AWS S3.
This service intentionally keeps a small surface area: it requires S3 settings
to be present and uploads files to the configured bucket. It returns a public
URL (constructed from a configured CDN base URL or the S3 bucket URL).
"""

from typing import Optional
import asyncio
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile, HTTPException, status

from ...settings.base import get_settings

settings = get_settings()


class StorageService:
    """Minimal service for uploading files to AWS S3.

    Usage:
        await storage_service.upload_file(upload_file, destination_path)
    """

    def __init__(self) -> None:
        pass

    async def upload_file(self, file: UploadFile, bucket_name: Optional[str], destination_path: str) -> str:
        """Upload a file to S3 and return its public URL.

        Args:
            file: FastAPI `UploadFile` instance
            bucket_name: S3 bucket name (must be configured in settings)
            destination_path: object key inside the bucket

        Returns:
            Public URL for the uploaded object
        """
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and (bucket_name or settings.S3_BUCKET_NAME)):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AWS S3 is not configured in settings.")

        # Resolve bucket name precedence (argument first, then settings)
        bucket = bucket_name or settings.S3_BUCKET_NAME

        try:
            contents = await file.read()

            # Create a synchronous client (creation is cheap) and run network calls in threadpool
            client = boto3.client(
                's3',
                region_name=settings.AWS_S3_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            # Verify the bucket exists and is accessible (head_bucket will raise if missing)
            try:
                await asyncio.to_thread(client.head_bucket, Bucket=bucket)
            except ClientError as e:
                # Provide a clearer error for missing bucket
                err_code = None
                try:
                    err_code = e.response.get('Error', {}).get('Code')
                except Exception:
                    pass
                if err_code == 'NoSuchBucket':
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"S3 bucket '{bucket}' does not exist. Verify bucket name and AWS account.")
                raise

            # Upload the object
            await asyncio.to_thread(
                client.put_object,
                Bucket=bucket,
                Key=destination_path,
                Body=contents,
                ContentType=file.content_type,
            )

            if settings.S3_CDN_URL:
                public_url = f"{settings.S3_CDN_URL.rstrip('/')}/{destination_path}"
            else:
                public_url = f"https://{bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{destination_path}"
            return public_url
        except (BotoCoreError, ClientError) as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file: {str(e)}")


storage_service = StorageService()