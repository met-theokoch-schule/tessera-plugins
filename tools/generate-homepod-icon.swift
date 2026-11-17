// Optional macOS asset tool. Firmware builds use the already generated header.
// Usage: swift tools/generate-homepod-icon.swift SOURCE.svg OUTPUT.h [PREVIEW.png]
import AppKit

guard CommandLine.arguments.count >= 3 else {
    fatalError("Usage: generate-homepod-icon.swift SOURCE.svg OUTPUT.h [PREVIEW.png]")
}
guard let image = NSImage(contentsOfFile: CommandLine.arguments[1]),
      let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 32, pixelsHigh: 32,
          bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
          colorSpaceName: .deviceRGB, bytesPerRow: 128, bitsPerPixel: 32),
      let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fatalError("Could not render the SVG")
}
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
NSColor.clear.setFill()
NSRect(x: 0, y: 0, width: 32, height: 32).fill()
image.draw(in: NSRect(x: 0, y: 0, width: 32, height: 32), from: .zero,
           operation: .copy, fraction: 1)
NSGraphicsContext.restoreGraphicsState()

var mask = [UInt8]()
for y in 0..<32 {
    for x in 0..<32 {
        var pixel = [Int](repeating: 0, count: 4)
        bitmap.getPixel(&pixel, atX: x, y: y)
        mask.append(UInt8(pixel[3]))
    }
}
guard mask.contains(255) && mask.contains(0) else { fatalError("Empty or opaque icon") }
var lines = [
    "#pragma once", "#include <lvgl.h>", "", "namespace esphome::kidsplayer {",
    "// Rasterized from assets/homepod-mini.svg (Custom Brand Icons, MIT).",
    "// See assets/LICENSE.custom-brand-icons and NOTICE.",
    "alignas(4) inline constexpr uint8_t HOMEPOD_MINI_ALPHA[] = {"
]
for offset in stride(from: 0, to: mask.count, by: 32) {
    lines.append("  " + mask[offset..<offset+32].map { String($0) }.joined(separator: ", ") + ",")
}
lines += [
    "};", "inline const lv_image_dsc_t &homepod_mini_image() {",
    "  static const lv_image_dsc_t image = [] {", "    lv_image_dsc_t value{};",
    "    value.header.magic = LV_IMAGE_HEADER_MAGIC;",
    "    value.header.cf = LV_COLOR_FORMAT_A8;",
    "    value.header.w = 32; value.header.h = 32; value.header.stride = 32;",
    "    value.data_size = sizeof(HOMEPOD_MINI_ALPHA);", "    value.data = HOMEPOD_MINI_ALPHA;",
    "    return value;", "  }();", "  return image;", "}", "}", ""
]
try lines.joined(separator: "\n").write(toFile: CommandLine.arguments[2], atomically: true, encoding: .utf8)
if CommandLine.arguments.count > 3 {
    try bitmap.representation(using: .png, properties: [:])!.write(
        to: URL(fileURLWithPath: CommandLine.arguments[3]))
}
