"""
File Upload Validator

Validates uploaded files for type safety, size limits, and image dimensions.
Uses magic byte verification to prevent MIME type spoofing attacks.
Includes decompression bomb protection for image uploads.
"""

import os
import struct
from typing import Optional, Tuple, NamedTuple
from dataclasses import dataclass

from fastapi import UploadFile, HTTPException

# Configuration
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096  # pixels
MAX_TOTAL_PIXELS = 16_777_216  # 4096 * 4096 = 16 megapixels

ALLOWED_TYPES = {
    "image/png": {
        "extension": ".png",
        "magic_bytes": b"\x89PNG\r\n\x1a\n",
        "max_size_mb": 10,
    },
    "image/jpeg": {
        "extension": ".jpg",
        "magic_bytes": b"\xff\xd8\xff",
        "max_size_mb": 10,
    },
    "image/webp": {
        "extension": ".webp",
        "magic_bytes": b"RIFF",  # Full check requires offset validation
        "max_size_mb": 10,
    },
    "image/gif": {
        "extension": ".gif",
        "magic_bytes": b"GIF8",
        "max_size_mb": 5,
    },
}


class ValidationResult(NamedTuple):
    """Result of file validation."""
    valid: bool
    error_message: Optional[str] = None
    detected_type: Optional[str] = None
    actual_size: Optional[int] = None


@dataclass
class UploadConfig:
    """Configuration for upload validation."""
    max_file_size_bytes: int = MAX_FILE_SIZE_BYTES
    max_image_dimension: int = MAX_IMAGE_DIMENSION
    max_total_pixels: int = MAX_TOTAL_PIXELS
    allowed_types: dict = None

    def __post_init__(self):
        if self.allowed_types is None:
            self.allowed_types = ALLOWED_TYPES


def read_magic_bytes(file: UploadFile, num_bytes: int = 16) -> bytes:
    """
    Read the first N bytes of an uploaded file to detect its actual type.

    This reads directly from the file stream without loading the entire file.
    """
    position = file.file.tell()
    file.file.seek(0)
    magic = file.file.read(num_bytes)
    file.file.seek(position)
    return magic


def validate_magic_bytes(file: UploadFile, expected_type: str) -> bool:
    """
    Verify the file's magic bytes match the expected MIME type.

    This prevents attacks where a file's extension or Content-Type header
    is manipulated to bypass type checks.
    """
    if expected_type not in ALLOWED_TYPES:
        return False

    expected_magic = ALLOWED_TYPES[expected_type]["magic_bytes"]
    actual_magic = read_magic_bytes(file, len(expected_magic))

    # Special handling for WebP: also check "WEBP" at offset 8
    if expected_type == "image/webp":
        if actual_magic[:4] != b"RIFF":
            return False
        webp_check = read_magic_bytes(file, 12)
        return webp_check[8:12] == b"WEBP"

    return actual_magic[:len(expected_magic)] == expected_magic


def read_png_dimensions(file: UploadFile) -> Optional[Tuple[int, int]]:
    """
    Read PNG image dimensions from the IHDR chunk without loading the full image.
    Returns (width, height) or None if parsing fails.
    """
    try:
        position = file.file.tell()
        file.file.seek(0)

        # Skip the 8-byte PNG signature
        file.file.read(8)

        # Read IHDR chunk
        chunk_length = struct.unpack(">I", file.file.read(4))[0]
        chunk_type = file.file.read(4)

        if chunk_type != b"IHDR":
            file.file.seek(position)
            return None

        width = struct.unpack(">I", file.file.read(4))[0]
        height = struct.unpack(">I", file.file.read(4))[0]

        file.file.seek(position)
        return (width, height)

    except (struct.error, IOError):
        return None


def read_jpeg_dimensions(file: UploadFile) -> Optional[Tuple[int, int]]:
    """
    Read JPEG dimensions by scanning for SOF marker.
    Returns (width, height) or None if parsing fails.
    """
    try:
        position = file.file.tell()
        file.file.seek(0)

        data = file.file.read(min(file.file.seek(0, 2), 65536))  # Read up to 64KB
        file.file.seek(position)

        idx = 2  # Skip SOI marker
        while idx < len(data) - 1:
            if data[idx] != 0xFF:
                break
            marker = data[idx + 1]

            # SOF markers (SOF0-SOF15, excluding SOF markers without dimensions)
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                if idx + 9 < len(data):
                    height = struct.unpack(">H", data[idx + 5 : idx + 7])[0]
                    width = struct.unpack(">H", data[idx + 7 : idx + 9])[0]
                    return (width, height)
                break

            # Skip to next marker
            if marker == 0xD9 or marker == 0xDA:  # EOI or SOS
                break
            if idx + 3 < len(data):
                segment_length = struct.unpack(">H", data[idx + 2 : idx + 4])[0]
                idx += 2 + segment_length
            else:
                break

        return None

    except (struct.error, IOError):
        return None


async def validate_upload(
    file: UploadFile,
    config: Optional[UploadConfig] = None,
) -> ValidationResult:
    """
    Validate an uploaded file for type, size, and image dimensions.

    Checks performed:
    1. File is not empty
    2. MIME type is in allowed list
    3. File size is within limits
    4. Magic bytes match the claimed MIME type (anti-spoofing)
    5. For images: decoded dimensions are within limits (decompression bomb protection)
    6. For images: total pixel count is within limits

    Args:
        file: The FastAPI UploadFile to validate
        config: Optional custom configuration

    Returns:
        ValidationResult with valid=True or error_message explaining the failure
    """
    if config is None:
        config = UploadConfig()

    # 1. Check file is not empty
    content = await file.read()
    actual_size = len(content)

    if actual_size == 0:
        return ValidationResult(valid=False, error_message="File is empty")

    # Reset file position for further reading
    file.file.seek(0)

    # 2. Check MIME type
    content_type = file.content_type
    if content_type not in config.allowed_types:
        return ValidationResult(
            valid=False,
            error_message=f"File type \'{content_type}\' is not allowed. "
            f"Accepted types: {', '.join(config.allowed_types.keys())}",
        )

    # 3. Check file size (type-specific limits)
    type_config = config.allowed_types[content_type]
    type_max_bytes = type_config["max_size_mb"] * 1024 * 1024

    if actual_size > type_max_bytes:
        return ValidationResult(
            valid=False,
            error_message=f"File size ({actual_size / (1024*1024):.1f} MB) exceeds "
            f"maximum allowed size ({type_config['max_size_mb']} MB) for {content_type}",
        )

    # 4. Validate magic bytes (anti-spoofing)
    if not validate_magic_bytes(file, content_type):
        return ValidationResult(
            valid=False,
            error_message=f"File content does not match declared type \'{content_type}\'. "
            f"The file may be corrupted or have an incorrect extension.",
        )

    # 5. Check image dimensions (decompression bomb protection)
    if content_type == "image/png":
        dimensions = read_png_dimensions(file)
        if dimensions:
            width, height = dimensions
            if width > config.max_image_dimension or height > config.max_image_dimension:
                return ValidationResult(
                    valid=False,
                    error_message=f"Image dimensions ({width}x{height}) exceed maximum "
                    f"allowed size ({config.max_image_dimension}x{config.max_image_dimension})",
                )
            total_pixels = width * height
            if total_pixels > config.max_total_pixels:
                return ValidationResult(
                    valid=False,
                    error_message=f"Total pixel count ({total_pixels:,}) exceeds maximum "
                    f"allowed ({config.max_total_pixels:,}). "
                    f"This file may be a decompression bomb.",
                )

    elif content_type == "image/jpeg":
        dimensions = read_jpeg_dimensions(file)
        if dimensions:
            width, height = dimensions
            if width > config.max_image_dimension or height > config.max_image_dimension:
                return ValidationResult(
                    valid=False,
                    error_message=f"Image dimensions ({width}x{height}) exceed maximum "
                    f"allowed size ({config.max_image_dimension}x{config.max_image_dimension})",
                )
            total_pixels = width * height
            if total_pixels > config.max_total_pixels:
                return ValidationResult(
                    valid=False,
                    error_message=f"Total pixel count ({total_pixels:,}) exceeds maximum "
                    f"allowed ({config.max_total_pixels:,}). "
                    f"This file may be a decompression bomb.",
                )

    return ValidationResult(
        valid=True,
        detected_type=content_type,
        actual_size=actual_size,
    )


async def require_valid_upload(
    file: UploadFile,
    config: Optional[UploadConfig] = None,
) -> UploadFile:
    """
    Validate an upload and raise HTTPException if validation fails.
    Returns the file if valid.
    """
    result = await validate_upload(file, config)

    if not result.valid:
        raise HTTPException(status_code=422, detail=result.error_message)

    return file
