"""Object storage for generated audio: local disk (dev/test) or any S3-compatible service (MinIO, AWS)."""

import asyncio
from pathlib import Path
from typing import Protocol

from app.core.config import settings


class Storage(Protocol):
    async def get(self, key: str) -> bytes | None: ...

    async def put(self, key: str, data: bytes, content_type: str) -> None: ...


class LocalStorage:
    def __init__(self, base: str):
        self.base = Path(base)

    def _path(self, key: str) -> Path:
        path = (self.base / key).resolve()
        if self.base.resolve() not in path.parents:
            raise ValueError("invalid storage key")
        return path

    async def get(self, key: str) -> bytes | None:
        path = self._path(key)
        return await asyncio.to_thread(path.read_bytes) if path.exists() else None

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(write)


class S3Storage:
    def __init__(self) -> None:
        import boto3

        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self._bucket_ready = False

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        existing = {b["Name"] for b in self.client.list_buckets().get("Buckets", [])}
        if self.bucket not in existing:
            self.client.create_bucket(Bucket=self.bucket)
        self._bucket_ready = True

    async def get(self, key: str) -> bytes | None:
        def fetch() -> bytes | None:
            self._ensure_bucket()
            try:
                return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
            except self.client.exceptions.NoSuchKey:
                return None

        return await asyncio.to_thread(fetch)

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        def upload() -> None:
            self._ensure_bucket()
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

        await asyncio.to_thread(upload)


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = (
            S3Storage() if settings.storage_backend == "s3" else LocalStorage(settings.storage_local_dir)
        )
    return _storage
