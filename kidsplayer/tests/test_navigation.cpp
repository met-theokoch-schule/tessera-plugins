// Execute the actual tile against the real Tessera API/ArduinoJson/LVGL headers.
// UI functions and transport are fakes; no pixel rendering or device emulation.
#include "../components/kidsplayer/kidsplayer.cpp"
#include <cassert>
#include <iostream>

static uint32_t now_ms = 100, next_re = 0;
static tessera::Point point{100, 100};
static JsonDocument request;
static std::string status;
struct Object { int x=0, y=0, width=0, height=20; bool hidden=false; };
static Object objects[100];
static Object &object(lv_obj_t *p) { return *reinterpret_cast<Object *>(p); }
static int used = 0;
namespace esphome { uint32_t millis() { return now_ms; } }
extern "C" {
void lv_obj_set_pos(lv_obj_t *p, int32_t x, int32_t y) { object(p).x=x; object(p).y=y; }
void lv_obj_set_size(lv_obj_t *p, int32_t w, int32_t h) { object(p).width=w; object(p).height=h; }
void lv_obj_set_width(lv_obj_t *p, int32_t w) { object(p).width=w; }
void lv_obj_set_style_text_align(lv_obj_t *, lv_text_align_t, lv_style_selector_t) {}
void lv_label_set_long_mode(lv_obj_t *, lv_label_long_mode_t) {}
void lv_label_set_text(lv_obj_t *, const char *s) { status = s; }
void lv_obj_add_flag(lv_obj_t *p, lv_obj_flag_t flag) { if (flag == LV_OBJ_FLAG_HIDDEN) object(p).hidden=true; }
void lv_obj_remove_flag(lv_obj_t *p, lv_obj_flag_t flag) { if (flag == LV_OBJ_FLAG_HIDDEN) object(p).hidden=false; }
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
  // Newly allowed intermediate sizes must fit vertically and keep Back usable.
  for (auto shape : {std::pair<int,int>{180,100}, {400,100}, {180,250}, {400,380}}) {
    const int first = used;
    LibraryTile tile(&plugin);
    context.width=shape.first; context.height=shape.second;
    tile.create(context);
    for (int i=first; i<used; ++i) {
      if (objects[i].hidden) continue;
      assert(objects[i].y >= 0);
      assert(objects[i].y + objects[i].height <= context.height);
    }
    tile.on_tick(0); reply(plugin, next_re, "robin", 0, 2);
    point={context.width/2, context.height/2}; tile.on_tap();
    assert(request["data"]["category"] == "robin");
    reply(plugin, next_re, "ep1", 0, 2);
    point={10,10}; tile.on_tap();
    assert(request["data"]["category"] == "");
    reply(plugin, next_re, "robin", 0, 2);
  }
  assert(plugin.tiles.empty());  // late replies cannot reference destroyed tiles
  std::cout << "Actual C++ tile: routing, navigation, isolation, playback timeout, compact geometry and destruction passed\n";
}
