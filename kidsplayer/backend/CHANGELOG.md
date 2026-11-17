# Home Assistant companion changelog

## 0.1.7

- Read HTTP cover bodies to EOF in bounded chunks instead of treating the first available network buffer as the complete image.
- Keep the 2 MiB limit, reject error/redirect/empty responses explicitly, and report cover download/decoder failures in the HA log without signed image URLs.
- Change cover cache keys so previous failed downloads do not mask the correction.
- Add regression coverage for fragmented image delivery, download limits and the actual HA cover-view download path.
- Companion-only update. Display plugin 0.1.6 remains compatible; no firmware build or YAML migration required.
