import hashlib
import os
import uuid
from abc import ABC, abstractmethod

from app.core.config import settings


class FileStorage(ABC):
    @abstractmethod
    def save(self, filename: str, data: bytes) -> str:
        """Persist bytes, return a retrievable URL/key."""

    @abstractmethod
    def read(self, key: str) -> bytes: ...


class LocalFileStorage(FileStorage):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def save(self, filename: str, data: bytes) -> str:
        key = f"{uuid.uuid4().hex}_{filename}"
        with open(self._path(key), "wb") as f:
            f.write(data)
        return f"{settings.PUBLIC_FILE_BASE_URL}/{key}"

    def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()


class S3FileStorage(FileStorage):
    """S3-compatible storage (AWS S3, MinIO, R2...). Used in prod."""

    def __init__(self):
        import boto3

        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )

    def save(self, filename: str, data: bytes) -> str:
        key = f"invoices/{uuid.uuid4().hex}_{filename}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"{settings.PUBLIC_FILE_BASE_URL}/{key}"

    def read(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()


def get_storage() -> FileStorage:
    if settings.STORAGE_BACKEND == "s3":
        return S3FileStorage()
    return LocalFileStorage(settings.LOCAL_STORAGE_DIR)


def compute_file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
