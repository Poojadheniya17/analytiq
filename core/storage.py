# core/storage.py
# Analytiq — Storage abstraction layer
# STORAGE=local  → uses local disk (development, default)
# STORAGE=s3     → uses AWS S3 or Cloudflare R2 (production)
#
# Switching storage backend requires only one env var change.
# All routers use this module — never write files directly.

import os
import shutil
from pathlib import Path
from typing import Optional

STORAGE_BACKEND = os.environ.get("STORAGE", "local")

# Local base directory
LOCAL_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "users")
)


# ── Local storage implementation ──────────────────────────────

class LocalStorage:
    """Stores files on local disk. Used in development."""

    def save(self, user_id: int, client_name: str, filename: str, content: bytes) -> str:
        path = self._get_path(user_id, client_name, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def read(self, user_id: int, client_name: str, filename: str) -> Optional[bytes]:
        path = self._get_path(user_id, client_name, filename)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def exists(self, user_id: int, client_name: str, filename: str) -> bool:
        return os.path.exists(self._get_path(user_id, client_name, filename))

    def delete(self, user_id: int, client_name: str, filename: str) -> bool:
        path = self._get_path(user_id, client_name, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_path(self, user_id: int, client_name: str, filename: str) -> str:
        """Returns absolute local path — for libraries that need a file path."""
        return self._get_path(user_id, client_name, filename)

    def get_client_dir(self, user_id: int, client_name: str) -> str:
        safe   = client_name.lower().replace(" ", "_")
        folder = os.path.join(LOCAL_BASE, str(user_id), safe)
        os.makedirs(folder, exist_ok=True)
        return folder

    def list_files(self, user_id: int, client_name: str) -> list[str]:
        folder = self.get_client_dir(user_id, client_name)
        if not os.path.exists(folder):
            return []
        return os.listdir(folder)

    def _get_path(self, user_id: int, client_name: str, filename: str) -> str:
        safe = client_name.lower().replace(" ", "_")
        return os.path.join(LOCAL_BASE, str(user_id), safe, filename)


# ── S3 / R2 storage implementation ────────────────────────────

class S3Storage:
    """
    Stores files in AWS S3 or Cloudflare R2.
    Used in production when STORAGE=s3.

    Required env vars:
      R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
      R2_BUCKET_NAME (or AWS equivalents)
    """

    def __init__(self):
        try:
            import boto3
            endpoint = os.environ.get("R2_ENDPOINT_URL")  # Cloudflare R2 only
            self.client = boto3.client(
                "s3",
                endpoint_url          = endpoint,
                aws_access_key_id     = os.environ.get("R2_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key = os.environ.get("R2_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name           = os.environ.get("AWS_REGION", "auto"),
            )
            self.bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("AWS_BUCKET_NAME", "analytiq-data")
        except ImportError:
            raise RuntimeError("boto3 not installed. Run: pip install boto3")

    def _key(self, user_id: int, client_name: str, filename: str) -> str:
        safe = client_name.lower().replace(" ", "_")
        return f"users/{user_id}/{safe}/{filename}"

    def save(self, user_id: int, client_name: str, filename: str, content: bytes) -> str:
        key = self._key(user_id, client_name, filename)
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return key

    def read(self, user_id: int, client_name: str, filename: str) -> Optional[bytes]:
        try:
            key = self._key(user_id, client_name, filename)
            res = self.client.get_object(Bucket=self.bucket, Key=key)
            return res["Body"].read()
        except Exception:
            return None

    def exists(self, user_id: int, client_name: str, filename: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=self._key(user_id, client_name, filename)
            )
            return True
        except Exception:
            return False

    def delete(self, user_id: int, client_name: str, filename: str) -> bool:
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=self._key(user_id, client_name, filename)
            )
            return True
        except Exception:
            return False

    def get_path(self, user_id: int, client_name: str, filename: str) -> str:
        """
        S3 doesn't have local paths. Download to a temp file and return path.
        Used by libraries (joblib, fpdf) that need a file path.
        """
        import tempfile
        content = self.read(user_id, client_name, filename)
        if content is None:
            return ""
        ext  = Path(filename).suffix
        tmp  = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(content)
        tmp.close()
        return tmp.name

    def get_client_dir(self, user_id: int, client_name: str) -> str:
        """
        S3 doesn't have directories. Return a temp local dir for
        libraries that need to write multiple files.
        """
        import tempfile
        tmp_dir = tempfile.mkdtemp()
        # Download all files for this client
        safe = client_name.lower().replace(" ", "_")
        prefix = f"users/{user_id}/{safe}/"
        try:
            res = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            for obj in res.get("Contents", []):
                key      = obj["Key"]
                filename = key.split("/")[-1]
                content  = self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
                with open(os.path.join(tmp_dir, filename), "wb") as f:
                    f.write(content)
        except Exception:
            pass
        return tmp_dir

    def list_files(self, user_id: int, client_name: str) -> list[str]:
        safe   = client_name.lower().replace(" ", "_")
        prefix = f"users/{user_id}/{safe}/"
        try:
            res = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj["Key"].split("/")[-1] for obj in res.get("Contents", [])]
        except Exception:
            return []

    def get_presigned_url(self, user_id: int, client_name: str,
                          filename: str, expires: int = 3600) -> str:
        """Generate a presigned URL for direct browser download."""
        key = self._key(user_id, client_name, filename)
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires
        )


# ── Factory — returns the right backend ───────────────────────

def get_storage() -> LocalStorage | S3Storage:
    if STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage()


# Singleton — import this everywhere
storage = get_storage()
