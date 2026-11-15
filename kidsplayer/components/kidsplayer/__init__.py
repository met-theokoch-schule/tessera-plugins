"""Kidsplayer ESPHome component registration."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import smart_display
from esphome.const import CONF_ID
DEPENDENCIES = ['smart_display']
ns = cg.esphome_ns.namespace('kidsplayer')
Kidsplayer = ns.class_('Kidsplayer', cg.Component)
CONFIG_SCHEMA = cv.Schema({cv.GenerateID(): cv.declare_id(Kidsplayer)}).extend(cv.COMPONENT_SCHEMA)
async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await smart_display.register_plugin(var, __file__)
