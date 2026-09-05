from __future__ import annotations

from dataclasses import dataclass
import struct
import zlib

from django.core.exceptions import ValidationError

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_IMAGE_PIXELS = 25_000_000
MAX_INFLATED_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class SanitizedImage:
    data: bytes
    content_type: str
    extension: str
    width: int
    height: int


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def _channels_for_color_type(color_type: int) -> int:
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValidationError("unsupported PNG color type")
    return channels


def _validate_bit_depth(color_type: int, bit_depth: int) -> None:
    allowed = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if bit_depth not in allowed.get(color_type, set()):
        raise ValidationError("unsupported PNG bit depth")


def sanitize_png(payload: bytes) -> SanitizedImage:
    if not payload.startswith(PNG_SIGNATURE):
        raise ValidationError("image byte signature does not match PNG")

    offset = len(PNG_SIGNATURE)
    ihdr: bytes | None = None
    idat_parts: list[bytes] = []
    palette: bytes | None = None
    transparency: bytes | None = None
    saw_iend = False

    while offset < len(payload):
        if len(payload) - offset < 12:
            raise ValidationError("truncated PNG chunk")
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        kind = payload[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(payload):
            raise ValidationError("truncated PNG chunk data")
        data = payload[data_start:data_end]
        expected_crc = struct.unpack(">I", payload[data_end:crc_end])[0]
        actual_crc = zlib.crc32(kind)
        actual_crc = zlib.crc32(data, actual_crc) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise ValidationError("invalid PNG chunk checksum")

        if ihdr is None and kind != b"IHDR":
            raise ValidationError("PNG IHDR must be first")
        if kind == b"IHDR":
            if ihdr is not None or length != 13:
                raise ValidationError("invalid PNG IHDR")
            ihdr = data
        elif kind == b"PLTE":
            if palette is not None:
                raise ValidationError("duplicate PNG palette")
            palette = data
        elif kind == b"tRNS":
            if transparency is not None:
                raise ValidationError("duplicate PNG transparency")
            transparency = data
        elif kind == b"IDAT":
            idat_parts.append(data)
        elif kind == b"IEND":
            if length != 0:
                raise ValidationError("invalid PNG IEND")
            saw_iend = True
            offset = crc_end
            break
        elif kind and 65 <= kind[0] <= 90:
            raise ValidationError("unsupported critical PNG chunk")
        offset = crc_end

    if ihdr is None or not idat_parts or not saw_iend or offset != len(payload):
        raise ValidationError("incomplete or trailing PNG data")

    width, height, bit_depth, color_type, compression, filter_method, interlace = (
        struct.unpack(">IIBBBBB", ihdr)
    )
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise ValidationError("image pixel dimensions exceed the safe limit")
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise ValidationError("unsupported PNG encoding")
    channels = _channels_for_color_type(color_type)
    _validate_bit_depth(color_type, bit_depth)
    if color_type == 3 and palette is None:
        raise ValidationError("indexed PNG requires a palette")

    bits_per_row = width * channels * bit_depth
    row_bytes = (bits_per_row + 7) // 8
    expected_inflated = height * (1 + row_bytes)
    if expected_inflated > MAX_INFLATED_BYTES:
        raise ValidationError("image decoded size exceeds the safe limit")

    compressed = b"".join(idat_parts)
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(compressed, expected_inflated + 1)
        raw += decoder.flush()
    except zlib.error as exc:
        raise ValidationError("invalid PNG compressed image data") from exc
    if (
        len(raw) != expected_inflated
        or decoder.unused_data
        or decoder.unconsumed_tail
        or not decoder.eof
    ):
        raise ValidationError("PNG decoded size does not match its dimensions")
    for row in range(height):
        if raw[row * (row_bytes + 1)] > 4:
            raise ValidationError("invalid PNG row filter")

    output = bytearray(PNG_SIGNATURE)
    output.extend(_png_chunk(b"IHDR", ihdr))
    if palette is not None:
        output.extend(_png_chunk(b"PLTE", palette))
    if transparency is not None:
        output.extend(_png_chunk(b"tRNS", transparency))
    output.extend(_png_chunk(b"IDAT", zlib.compress(raw, level=9)))
    output.extend(_png_chunk(b"IEND", b""))
    return SanitizedImage(
        data=bytes(output),
        content_type="image/png",
        extension=".png",
        width=width,
        height=height,
    )


def sanitize_image(*, payload: bytes, declared_content_type: str) -> SanitizedImage:
    if declared_content_type != "image/png":
        raise ValidationError("secure image processing currently accepts PNG only")
    return sanitize_png(payload)
