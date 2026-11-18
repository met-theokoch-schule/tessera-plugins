#!/usr/bin/env python3
"""Build real LVGL and check the embedded icon with/without A8 transforms.

Usage: python3 tools/test-icon-render.py /path/to/lvgl /tmp/render-build
Requires clang/clang++ and ar. The build folder is a reusable local cache;
no toolchain or network access is needed on the Home Assistant machine.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import subprocess
import sys

core, work = (Path(arg).resolve() for arg in sys.argv[1:3])
work.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
flags = ["-DLV_CONF_SKIP", "-DLV_COLOR_DEPTH=16", "-DLV_DRAW_BUF_ALIGN=32",
         "-DLV_DRAW_BUF_STRIDE_ALIGN=1", "-I" + str(core)]


def run(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def compile_c(source):
    # Include the configuration and source version in the cache key. Use a new
    # build folder after changing LVGL headers/configuration.
    key = hashlib.sha256(source.read_bytes() + repr(flags).encode()).hexdigest()[:12]
    target = work / (str(source.relative_to(core)).replace("/", "_") + key + ".o")
    if not target.exists():
        run(["clang", "-std=c99", "-O1", *flags, "-c", str(source), "-o", str(target)])
    return str(target)


with ThreadPoolExecutor(max_workers=4) as pool:
    objects = list(pool.map(compile_c, (core / "src").rglob("*.c")))
library = work / "liblvgl.a"
run(["ar", "rcs", str(library), *objects])
test = root / "kidsplayer/tests/test_icon_render.cpp"
fixed = work / "icon-fixed"
run(["clang++", "-std=c++17", *flags, str(test), str(library), "-o", str(fixed)])
for theme in ("light", "dark"):
    result = run([str(fixed), str(work / ("icon-" + theme + ".ppm")), theme])
    print(theme + ": " + result.stdout.strip(), flush=True)

# Reproduce the original codegen omission: LVGL's A8 transform is compiled out.
# Link this object ahead of the archive so it replaces the enabled transform.
disabled = work / "no_a8.o"
run(["clang", "-std=c99", "-O1", *flags, "-DLV_DRAW_SW_SUPPORT_A8=0", "-c",
     str(core / "src/draw/sw/lv_draw_sw_transform.c"), "-o", str(disabled)])
broken = work / "icon-broken"
run(["clang++", "-std=c++17", *flags, str(test), str(disabled), str(library), "-o", str(broken)])
result = subprocess.run([str(broken), str(work / "icon-broken.ppm")], capture_output=True, text=True)
if result.returncode != 2:
    raise RuntimeError("Missing A8 support was not detected by the pixel checks: " + result.stdout)
print("Negative control reproduced: " + result.stdout.strip(), flush=True)
