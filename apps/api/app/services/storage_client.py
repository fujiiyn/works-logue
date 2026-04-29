import io
import logging
import time
import uuid

from PIL import Image

logger = logging.getLogger(__name__)

# Constants
AVATAR_SIZE = (256, 256)
COVER_SIZE = (1200, 340)
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB
MAX_COVER_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


class StorageError(Exception):
    pass


class SupabaseStorageClient:
    """Handles image upload/delete to Supabase Storage (D2, D14, D15)."""

    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._service_role_key}",
            "apikey": self._service_role_key,
        }

    def _storage_url(self, bucket: str, path: str) -> str:
        return f"{self._supabase_url}/storage/v1/object/{bucket}/{path}"

    def _public_url(self, bucket: str, path: str) -> str:
        return f"{self._supabase_url}/storage/v1/object/public/{bucket}/{path}"

    @staticmethod
    def validate_and_process_image(
        file_data: bytes,
        target_size: tuple[int, int],
        max_bytes: int,
    ) -> tuple[bytes, str]:
        """Validate MIME via Pillow magic bytes (D14), resize, return (data, ext)."""
        if len(file_data) > max_bytes:
            raise StorageError(
                f"File size {len(file_data)} exceeds maximum {max_bytes} bytes"
            )

        try:
            img = Image.open(io.BytesIO(file_data))
            img.verify()
            # Re-open after verify (verify closes the image)
            img = Image.open(io.BytesIO(file_data))
        except Exception as e:
            raise StorageError(f"Invalid image file: {e}")

        fmt = img.format
        if fmt not in ("JPEG", "PNG"):
            raise StorageError(f"Unsupported image format: {fmt}. Only JPEG and PNG allowed.")

        ext = "jpg" if fmt == "JPEG" else "png"

        # Resize with center crop
        img = _center_crop_resize(img, target_size)

        # Save to bytes
        buf = io.BytesIO()
        save_format = "JPEG" if ext == "jpg" else "PNG"
        if save_format == "JPEG":
            img = img.convert("RGB")
        img.save(buf, format=save_format, quality=85)
        return buf.getvalue(), ext

    async def upload(
        self,
        bucket: str,
        user_id: uuid.UUID,
        file_data: bytes,
        target_size: tuple[int, int],
        max_bytes: int,
    ) -> tuple[str, str]:
        """Upload image, return (public_url, storage_path)."""
        processed_data, ext = self.validate_and_process_image(
            file_data, target_size, max_bytes
        )

        timestamp = int(time.time() * 1000)
        path = f"{user_id}/{timestamp}.{ext}"
        content_type = "image/jpeg" if ext == "jpg" else "image/png"

        import httpx

        url = self._storage_url(bucket, path)
        headers = {
            **self._headers(),
            "Content-Type": content_type,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, content=processed_data, headers=headers)
            if resp.status_code not in (200, 201):
                raise StorageError(f"Upload failed: {resp.status_code} {resp.text}")

        public_url = self._public_url(bucket, path)
        return public_url, path

    async def delete(self, bucket: str, path: str) -> None:
        """Delete file from storage. Failure is logged, not raised (D15)."""
        import httpx

        url = f"{self._supabase_url}/storage/v1/object/{bucket}"
        headers = self._headers()

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.request(
                    "DELETE", url, json={"prefixes": [path]}, headers=headers
                )
                if resp.status_code not in (200, 204):
                    logger.warning(
                        "Failed to delete %s/%s: %s %s",
                        bucket, path, resp.status_code, resp.text,
                    )
        except Exception:
            logger.warning("Failed to delete %s/%s", bucket, path, exc_info=True)


def _center_crop_resize(img: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """Resize with center crop to target dimensions."""
    target_w, target_h = target_size
    target_ratio = target_w / target_h
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Image is wider — crop sides
        new_w = int(img.height * target_ratio)
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        # Image is taller — crop top/bottom
        new_h = int(img.width / target_ratio)
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))

    return img.resize(target_size, Image.LANCZOS)
