# Changelog

## 0.1.12

- Raise the cover group into the navigation row and restore New music's 30% reflection on normal-height tiles.
- Keep heading and controls above artwork; their hit areas take priority over the partially covered side covers.
- Add a small rounded, light-grey theme background sized to the configured heading. Hide it with the heading on episode level or when the heading is empty.
- Keep large cover proportions, centred footer titles and silent artwork changes; compact single-row tiles still omit reflections.
- Increase declared per-tile memory to 7600 bytes for the additional heading surface.
- Firmware-only update; Home Assistant companion remains 0.1.7.

## 0.1.11

- Replace the media-control ellipsis with the user's HomePod mini SVG, embedded as a small alpha image.
- Follow Tessera's light/dark text colour and retain the existing round button position, hit area and native media opener.
- Keep the source SVG, upstream MIT notice, generated mask and optional macOS regeneration tool in the repository. No runtime SVG decoder, font or network image request.
- Use the existing speaker glyph on builds without LVGL image support.
- Firmware-only update; Home Assistant companion remains 0.1.7.

## 0.1.10

- Keep Tessera's default rounded corners on the stable plugin background instead of overriding the radius to zero.
- Let the native pressed tile rim remain visible around the rounded surface while keeping the cover area steady.
- Firmware-only visual update; Home Assistant companion remains 0.1.7.

## 0.1.9

- Increase the main cover width cap to three quarters of the width after side gaps (about 71% of a 400 px tile).
- Prefer a larger unreflected cover on shallow tiles; retain the original 30% reflection only when it costs at most 10% of possible cover size.
- Centre unreflected covers in the artwork space between the navigation row and full-width title.
- Keep both inner neighbours at least one sixth as wide as the main cover; the pinned New music frame loop itself remains unchanged.
- Extend native geometry checks for 400 × 250, 400 × 300, 400 × 380 and 400 × 500 tiles, including title/button clearance, neighbour visibility and adaptive reflection.
- Firmware-only update; Home Assistant companion remains 0.1.7. Includes the top-right player controls and centred titles from 0.1.8.

## 0.1.8

- Move the native media and Play/Pause buttons to the top right, with the same size and vertical position as Back.
- Restore full-width centred series/episode titles and centre the status line; reserve heading width so long headings cannot overlap controls.
- Remove the button space from the footer and keep the cover artwork below the navigation row.
- Clarify the missing-native-tile message: a normal media tile for the same Inspector player is required anywhere in the Tessera layout. This prerequisite is unchanged; no Home Assistant configuration is modified.
- Extend native tests for shared button position/size, centred title/status geometry, heading clearance and control routing.
- Firmware-only update; HA companion remains 0.1.7.

## 0.1.7

- Add a per-tile Heading text option, defaulting to Reihen, and a circular Back arrow on the episode level.
- Add circular native media-controls and Play/Pause buttons on tiles at least 280 × 220 reference pixels with an Inspector player.
- Reuse Tessera's existing media detail card via a small codegen adapter; the same player needs a normal media tile anywhere in the layout. No page switch or core patch.
- Use Tessera's optimistic PLAYING wish for the existing queue; never restart an episode to resume playback. Follow Home Assistant state for the icon and handle unavailable players/send failures.
- Reserve footer space for buttons and titles, preserve silent artwork changes and independent tile navigation.
- Firmware-only update. HA companion stays on 0.1.7; library YAML is unchanged. The native-card adapter depends on the inspected Tessera core internals (API 0.24).

## 0.1.6

- Add a stable plugin-local background matching the host's normal tile colour, masking touch darkening within the cover area without changing the core or other tiles.
- Increase the main cover width cap from 50% to about 63%, shorten the header and centre the cover group vertically.
- Share one single-line footer between title and playback/error status, keeping text off the cover motif.
- Preserve the original outer-neighbour loop, seven-place limit, reflections and silent static image changes.
- Firmware-only update; companion remains 0.1.4.

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
