"""Compile the actual codegen callback and adapter with a layout/core double.

No replacement media UI is rendered here. The real core/card itself still needs
firmware compilation and visual acceptance on the display.
"""
import ast
import asyncio
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import types
import sys

COMPONENT = Path(__file__).resolve().parents[1] / "components" / "kidsplayer"


class NativeMediaTest(unittest.TestCase):
    def test_codegen_requests_alpha_image_renderer(self):
        tree = ast.parse((COMPONENT / "__init__.py").read_text())
        function = next(node for node in tree.body
                        if isinstance(node, ast.AsyncFunctionDef) and node.name == "to_code")
        module = ast.Module(body=[function], type_ignores=[])
        cg = MagicMock()
        cg.register_component = AsyncMock()
        smart_display = types.SimpleNamespace(register_plugin=AsyncMock())
        lvgl = types.ModuleType("esphome.components.lvgl")
        lvgl.defines = types.SimpleNamespace(add_define=MagicMock())
        namespace = {"cg": cg, "smart_display": smart_display, "CONF_ID": "id",
                     "__file__": str(COMPONENT / "__init__.py"),
                     "coroutine_with_priority": lambda priority: lambda function: function}
        exec(compile(module, str(COMPONENT / "__init__.py"), "exec"), namespace)
        modules = {name: types.ModuleType(name) for name in ("esphome", "esphome.components")}
        modules["esphome.components.lvgl"] = lvgl
        with patch.dict(sys.modules, modules):
            asyncio.run(namespace["to_code"]({"id": "kidsplayer"}))
        lvgl.defines.add_define.assert_called_once_with("LV_DRAW_SW_SUPPORT_A8", "1")
        smart_display.register_plugin.assert_awaited_once()

    @unittest.skipUnless(shutil.which("clang++"), "clang++ required")
    def test_generated_callback_routes_real_entity_without_changing_page(self):
        tree = ast.parse((COMPONENT / "__init__.py").read_text())
        expressions = [node.args[0].value for node in ast.walk(tree)
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                       and node.func.attr == "RawExpression"]
        self.assertEqual(len(expressions), 1)
        source = r'''
#include "native_media.h"
#include <cassert>
namespace runtime_tiles {
struct Tile { std::string entity; };
struct Model { unsigned count; Tile tiles[4]; };
Model model{4, {{"plugin:kidsplayer.library"}, {"media_player.other"},
                 {"media_player.child"}, {"media_player.child"}}};
bool enabled = true;
int opened = -1, calls = 0, current_page = 0;
void hold_card(unsigned index) { opened = index; ++calls; }
}
int main() {
  auto open = CALLBACK;
  assert(!open(""));
  assert(!open("light.bedroom"));
  assert(!open("media_player.absent"));
  assert(runtime_tiles::calls == 0);
  assert(open("media_player.child"));
  assert(runtime_tiles::opened == 2 && runtime_tiles::calls == 1);
  assert(runtime_tiles::current_page == 0);
  assert(open("media_player.other"));
  assert(runtime_tiles::opened == 1);
  runtime_tiles::enabled = false;
  assert(!open("media_player.child"));
  assert(runtime_tiles::calls == 2);
}
'''.replace("CALLBACK", expressions[0])
        with tempfile.TemporaryDirectory() as folder:
            cpp = Path(folder) / "adapter.cpp"
            binary = Path(folder) / "adapter"
            cpp.write_text(source)
            subprocess.run(["clang++", "-std=c++17", "-I" + str(COMPONENT),
                            str(cpp), "-o", str(binary)], check=True, capture_output=True)
            subprocess.run([str(binary)], check=True, capture_output=True)
