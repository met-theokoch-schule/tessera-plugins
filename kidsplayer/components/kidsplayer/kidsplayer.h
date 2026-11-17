#pragma once
#include "esphome/core/component.h"
#include "esphome/components/smart_display/plugin_api.h"
#include "native_media.h"
#include <functional>
#include <utility>
namespace esphome::kidsplayer {
class LibraryTile;
class Kidsplayer : public Component, public tessera::Plugin {
 public:
  void setup() override;
  float get_setup_priority() const override { return setup_priority::DATA; }
  void on_message(JsonObjectConst message) override;
  using MediaOpener = std::function<bool(const std::string &)>;
  void set_media_opener(MediaOpener opener) { media_opener_ = std::move(opener); }
  bool open_media(const std::string &entity) { return media_opener_ && media_opener_(entity); }
  tessera::List<LibraryTile *> tiles;
 private:
  MediaOpener media_opener_;
};
}
