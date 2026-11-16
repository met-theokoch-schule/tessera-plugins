# Changelog

## 0.1.5

- Keep browsing silent: remove initial and per-request loading text while retaining playback and error feedback.
- Use a static cover-atlas swap instead of sliding old pictures during image transfer.
- Keep title and navigation header until the new atlas is reported, and update immediately for shared artwork.
- Block selection of unseen pending entries and recover from image timeouts/failures.
- Firmware-only update; HA companion remains 0.1.4 and existing library YAML remains valid.

## 0.1.4

- Fix playback/cover metadata calls for Home Assistant 2026.11.1 with MA client 1.6.0 and server 2.10.12 (schema 65).
- Use supported contextual calls, disable autoplay through the compatible alias, and send one ordered replace command with shuffle=false on schema 65.
- Preserve playback user attribution without passing unsupported user arguments to legacy metadata/queue methods.
- Carry application errors through Tessera for new firmware, retain safe error behavior for old firmware, and include exception detail on the first HA log line.
- Add strict legacy-signature, actual client-1.6-source, cross-version and error-transport regression tests.

## 0.1.3

- Remove the three-cover limit; declare seven picture places and page the centre plus three neighbours on each side from the companion.
- Reuse the pinned New music image-frame loop unchanged, including outermost-first layering, spacing, clipping and no-duplicate rules.
- Use the reference height calculation below the Back header; keep compact layouts and contain fit for original cover motifs.
- Resolve repeated neighbours once per browse; retain bounded transport and per-tile state.
- Test the actual reference block equality, seven-place rendering, wraparound, duplicate suppression and seven-cover response size.

- Update both the plugin firmware and Home Assistant companion for this release; library YAML is unchanged.

## 0.1.2

- Restore New music's full-height perspective, centre/side proportions, physical gap, reflection and 320 ms slide distance based on actual frame spacing (three visible places).
- Start the slide alongside new cover addresses after the asynchronous browse response, not before waiting on the backend.
- Do not slide identical or missing centre artwork; a shared album image otherwise may never produce the new atlas needed to reset the slide.
- Omit duplicate neighbours for one/two entries and remove placeholder bars during cover loads.
- Extend native tests for delayed/failed responses, direction/distance/duration, shared artwork, animation disabled, geometry and reflections.

## 0.1.1

- Allow 1x1, 2x1 and 1x2 intermediate sizes so Tessera exposes resize handles and tiles can grow to 2x2.
- Keep covers, back navigation and status within short tiles; omit the title row in compact layouts.
- Add regression checks against Tessera's actual editor resize functions and native compact-tile geometry.

## 0.1.0

- Independent nested cover browser with per-tile library and player.
- Companion integration validates YAML, pages covers and preflights ordered playback.
- Explicit track groups, complete albums, user attribution and authenticated local covers.
