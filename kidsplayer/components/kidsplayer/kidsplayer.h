#pragma once
#include "esphome/core/component.h"
#include "esphome/components/smart_display/plugin_api.h"
namespace esphome::kidsplayer {
class LibraryTile;
class Kidsplayer : public Component, public tessera::Plugin {
 public:
  void setup() override;
  float get_setup_priority() const override { return setup_priority::DATA; }
  void on_message(JsonObjectConst message) override;
  tessera::List<LibraryTile *> tiles;
};
}
