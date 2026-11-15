#!/bin/sh
# Usage: tools/test-native.sh CORE_CHECKOUT ARDUINOJSON_CHECKOUT LVGL_CHECKOUT
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
core=$(CDPATH= cd -- "$1" && pwd)
json=$(CDPATH= cd -- "$2" && pwd)
lvgl=$(CDPATH= cd -- "$3" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/esphome/components"
ln -s "$core/components/smart_display" "$work/esphome/components/smart_display"
clang++ -std=c++17 -DLV_CONF_SKIP -I"$root/kidsplayer/tests/support" -I"$work" -I"$json/src" -I"$lvgl" "$root/kidsplayer/tests/test_navigation.cpp" -o "$work/navigation"
"$work/navigation"
