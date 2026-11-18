"""Bounded cover reads and cache identities for local artwork."""
import hashlib
from pathlib import Path

MAX_IMAGE_BYTES = 2 * 1024 * 1024


class CoverError(ValueError):
    """A safe diagnostic that contains neither source URLs nor credentials."""


def local_cover_source(root, filename):
    """Resolve inside the allowed folder and hash actual bytes, off the HA loop.

    Replacing a JPEG must change its URL even when name, size and copied mtime
    are preserved. A byte-for-byte unchanged file keeps the same cache identity.
    """
    root = Path(root).resolve()
    source = (root / filename).resolve()
    if not source.is_relative_to(root):
        raise CoverError('Cover ausserhalb cover_root')
    digest = hashlib.sha256()
    total = 0
    with source.open('rb') as handle:
        while True:
            chunk = handle.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise CoverError('Cover groesser als 2 MiB')
            digest.update(chunk)
    if not total:
        raise CoverError('Leere Coverdatei')
    return str(source), digest.hexdigest()


async def read_image_response(response, limit=MAX_IMAGE_BYTES):
    # raise_for_status() alone accepts redirects; their HTML is not an image.
    if not 200 <= response.status < 300:
        raise CoverError('HTTP %s beim Coverdownload' % response.status)
    if response.content_length is not None and response.content_length > limit:
        raise CoverError('Cover groesser als 2 MiB')
    raw = bytearray()
    # StreamReader.read(n) can return just the currently buffered first chunk.
    # Iterate to EOF, while enforcing the byte limit on every received chunk.
    async for chunk in response.content.iter_chunked(64 * 1024):
        if len(raw) + len(chunk) > limit:
            raise CoverError('Cover groesser als 2 MiB')
        raw.extend(chunk)
    if not raw:
        raise CoverError('Leere Coverantwort')
    return bytes(raw)
