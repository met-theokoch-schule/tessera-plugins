# HomePod mini icon

`homepod-mini.svg` is the exact SVG supplied by the user. Its path matches
`cbi:homepod-mini` from [Custom Brand Icons](https://github.com/elax46/custom-brand-icons).
The upstream MIT license is preserved in `LICENSE.custom-brand-icons` and the
repository's `NOTICE` identifies its use.

The firmware uses a 32 × 32 alpha mask (1024 constant bytes) generated from this
SVG, not a font glyph. Its colour comes from Tessera's `INK` theme role. The image
is scaled to 28 reference pixels and centred in the existing round control.
There is no HTTP request, new font, runtime SVG decoder or additional cover slot.
Since 0.1.13 the component explicitly enables `LV_DRAW_SW_SUPPORT_A8` before
ESPHome generates `lv_conf.h`. ESPHome cannot infer formats of images created
in C++; omitting A8 support corrupts the scaled alpha image. The SVG and the
embedded mask are unchanged.
A firmware built without LVGL image support uses Tessera's existing speaker glyph.

Optional regeneration on macOS (Swift/AppKit, development only):

```sh
swift tools/generate-homepod-icon.swift kidsplayer/assets/homepod-mini.svg \
  kidsplayer/components/kidsplayer/homepod_mini_icon.h /tmp/homepod-mini.png
```

The generated header is included in Git. Installing or compiling the plugin does
not require Swift or this generation step. Other platforms can generate the same
32 × 32, 8-bit alpha mask from the source SVG with their own SVG renderer.
