# Home Assistant companion changelog

## 0.1.8

- Include a hash of local cover file contents in the authenticated image URL. Replacing only a JPEG now bypasses Tessera's stale artwork cache on the next browse refresh, without changing YAML or filenames.
- Hash in Home Assistant's executor with bounded 64 KiB reads and the existing 2 MiB size limit; unchanged image bytes retain the same URL, even after restarts or timestamp changes.
- Keep cover-root containment checks, short URLs, bounded registration and automatic Music Assistant cover identities unchanged.
- Test the actual Backend.cover method, same-name/same-size/preserved-timestamp replacements, stable unchanged files, size/empty/missing cases, and rejected traversal/symlink escapes.
- Companion-only update. Display plugin 0.1.13 and earlier compatible versions need no firmware rebuild.

## 0.1.7

- Read HTTP cover bodies to EOF in bounded chunks instead of treating the first available network buffer as the complete image.
- Keep the 2 MiB limit, reject error/redirect/empty responses explicitly, and report cover download/decoder failures in the HA log without signed image URLs.
- Change cover cache keys so previous failed downloads do not mask the correction.
- Add regression coverage for fragmented image delivery, download limits and the actual HA cover-view download path.
- Companion-only update. Display plugin 0.1.6 remains compatible; no firmware build or YAML migration required.
