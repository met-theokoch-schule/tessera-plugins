#pragma once
#include <string>

namespace esphome::kidsplayer {
// API 0.24 only opens plugin cards. Reuse a real media tile in the existing
// layout so the native card retains its subscriptions, capabilities and queue.
// Keep the adapter small: this is the only dependency on Tessera internals.
template<class Model, class Open>
bool open_native_media(const Model &model, const std::string &entity, Open open) {
  if (entity.rfind("media_player.", 0) != 0) return false;
  for (unsigned i = 0; i < model.count; ++i) {
    if (model.tiles[i].entity == entity) {
      open(i);
      return true;
    }
  }
  return false;
}
}
