// Execute the actual tile against the real Tessera API/ArduinoJson/LVGL headers.
// UI functions and transport are fakes; no pixel rendering or device emulation.
#include "../components/kidsplayer/kidsplayer.cpp"
#include <cassert>
#include <iostream>

static uint32_t now_ms = 100, next_re = 0;
static tessera::Point point{100, 100};
static JsonDocument request;
static std::string status;
static int objects[100];
static int used = 0;
namespace esphome { uint32_t millis() { return now_ms; } }
extern "C" {
void lv_obj_set_pos(lv_obj_t *, int32_t, int32_t) {}
void lv_obj_set_size(lv_obj_t *, int32_t, int32_t) {}
void lv_obj_set_width(lv_obj_t *, int32_t) {}
void lv_obj_set_style_text_align(lv_obj_t *, lv_text_align_t, lv_style_selector_t) {}
void lv_label_set_long_mode(lv_obj_t *, lv_label_long_mode_t) {}
void lv_label_set_text(lv_obj_t *, const char *s) { status = s; }
void lv_obj_add_flag(lv_obj_t *, lv_obj_flag_t) {}
void lv_obj_remove_flag(lv_obj_t *, lv_obj_flag_t) {}
}
namespace tessera {
Plugin::Plugin() = default;
void Plugin::add_tile(const char *, std::function<Tile *()>) {}
Point tap_point() { return point; }
uint32_t send(const Plugin *, JsonObjectConst data) { request.set(data); return ++next_re; }
namespace ui {
lv_obj_t *text(lv_obj_t *, Font, theme::Role) { return reinterpret_cast<lv_obj_t *>(&objects[used++]); }
lv_obj_t *picture(lv_obj_t *, Placeholder) { return reinterpret_cast<lv_obj_t *>(&objects[used++]); }
void set_picture(lv_obj_t *, const std::string &, Fit, Turn, bool) {}
void set_color(lv_obj_t *, theme::Role) {}
void slide_pictures(int, uint32_t) {}
}
}
static void reply(esphome::kidsplayer::Kidsplayer &plugin, uint32_t re, const char *id, int index, int total) {
  JsonDocument doc;
  doc["re"] = re; doc["ok"] = true;
  auto result = doc["result"].to<JsonObject>();
  result["total"] = total; result["index"] = index; result["revision"] = "rev1";
  result["center"]["id"] = id;
  plugin.on_message(doc.as<JsonObjectConst>());
}
int main() {
  using namespace esphome::kidsplayer;
  Kidsplayer plugin;
  JsonDocument opts; opts["library"] = "child_a";
  tessera::TileContext context{nullptr, 400, 380, 2, 2, "", "media_player.child_a", 0, opts.as<JsonObjectConst>()};
  {
    LibraryTile a(&plugin), b(&plugin);
    a.create(context);
    opts["library"] = "child_b"; context.options = opts.as<JsonObjectConst>(); b.create(context);
    a.on_tick(0); auto ra = next_re;
    b.on_tick(0); auto rb = next_re;
    reply(plugin, rb, "conni", 0, 2);
    reply(plugin, ra, "robin", 0, 2);  // answers in reverse order stay on their own tile
    point = {200, 120}; a.on_tap();
    assert(request["data"]["library"] == "child_a");
    assert(request["data"]["category"] == "robin");
    reply(plugin, next_re, "episode1", 0, 3);
    point = {399,120}; a.on_tap(); assert(request["data"]["index"] == 1);
    reply(plugin, next_re, "episode2", 1, 3);
    point = {200,120}; a.on_tap(); assert(request["ask"] == "kidsplayer/play");
    assert(request["data"]["episode"] == "episode2");
    auto play_re = next_re;
    now_ms += 21000; a.on_tick(0); assert(next_re == play_re); // never retry playback after timeout
    point = {10,10}; a.on_tap(); assert(request["data"]["category"] == "");
    reply(plugin, next_re, "robin", 0, 2);
    point = {200,120}; b.on_tap(); assert(request["data"]["category"] == "conni");
    assert(request["data"]["library"] == "child_b");
  }
  assert(plugin.tiles.empty());  // late replies cannot reference destroyed tiles
  std::cout << "Actual C++ tile: routing, navigation, isolation, playback timeout and destruction passed\n";
}
