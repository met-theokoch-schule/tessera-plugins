"""Bounded HTTP cover download, including bodies delivered in multiple chunks."""
MAX_IMAGE_BYTES = 2 * 1024 * 1024


class CoverError(ValueError):
    """A safe diagnostic that contains neither source URLs nor credentials."""


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
