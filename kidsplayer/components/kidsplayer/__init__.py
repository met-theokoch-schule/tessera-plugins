"""Kidsplayer ESPHome component registration."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import smart_display
from esphome.const import CONF_ID
from esphome.core import coroutine_with_priority
DEPENDENCIES = ['smart_display']
ns = cg.esphome_ns.namespace('kidsplayer')
Kidsplayer = ns.class_('Kidsplayer', cg.Component)
CONFIG_SCHEMA = cv.Schema({cv.GenerateID(): cv.declare_id(Kidsplayer)}).extend(cv.COMPONENT_SCHEMA)
@coroutine_with_priority(1.0)
async def to_code(config):
    from esphome.components.lvgl import defines as lvgl_defines

    # Register before LVGL's default-priority codegen writes lv_conf.h.
    # C++-created images are invisible to ESPHome's YAML image discovery.
    # A8 transforms are compiled out unless explicitly requested, which leaves
    # the scaled icon's intermediate pixels unpainted (garbled output).
    lvgl_defines.add_define("LV_DRAW_SW_SUPPORT_A8", "1")
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await smart_display.register_plugin(var, __file__)
    # Generated main.cpp already includes smart_display.h/runtime_tiles.h.
    # No core patch, synthetic tile, page switch or second media UI is needed.
    cg.add(var.set_media_opener(cg.RawExpression("""[](const std::string &entity) -> bool {
      if (!runtime_tiles::enabled) return false;
      return esphome::kidsplayer::open_native_media(runtime_tiles::model, entity,
        [](unsigned index) { runtime_tiles::hold_card(index); });
    }""")))
