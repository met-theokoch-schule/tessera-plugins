// Execute the actual tile against the real Tessera API/ArduinoJson/LVGL headers.
// UI functions and transport are fakes; no pixel rendering or device emulation.
#include "../components/kidsplayer/kidsplayer.cpp"
#include <cassert>
#include <iostream>

static uint32_t now_ms = 100, next_re = 0;
static tessera::Point point{100, 100};
static JsonDocument request;
static std::string status;
static std::vector<std::string> label_events;
static int slides=0, slide_dx=0;
static uint32_t slide_ms=0;
struct Object { int x=0, y=0, width=0, height=20; bool hidden=false, mirror=false, no_placeholder=false; tessera::Turn turn=tessera::Turn::NONE; std::string source, text; };
static Object objects[1000];
static Object &object(lv_obj_t *p) { return *reinterpret_cast<Object *>(p); }
static int used = 0;
namespace esphome { uint32_t millis() { return now_ms; } }
extern "C" {
int32_t lv_font_get_line_height(const lv_font_t *font) { return font->line_height; }
void lv_obj_set_pos(lv_obj_t *p, int32_t x, int32_t y) { object(p).x=x; object(p).y=y; }
void lv_obj_set_size(lv_obj_t *p, int32_t w, int32_t h) { object(p).width=w; object(p).height=h; }
void lv_obj_set_width(lv_obj_t *p, int32_t w) { object(p).width=w; }
void lv_obj_set_style_text_align(lv_obj_t *, lv_text_align_t, lv_style_selector_t) {}
void lv_label_set_long_mode(lv_obj_t *, lv_label_long_mode_t) {}
void lv_label_set_text(lv_obj_t *p, const char *s) { status = s; object(p).text=s; label_events.push_back(s); }
void lv_obj_add_flag(lv_obj_t *p, lv_obj_flag_t flag) { if (flag == LV_OBJ_FLAG_HIDDEN) object(p).hidden=true; }
void lv_obj_remove_flag(lv_obj_t *p, lv_obj_flag_t flag) { if (flag == LV_OBJ_FLAG_HIDDEN) object(p).hidden=false; }
}
namespace tessera {
Plugin::Plugin() = default;
void Plugin::add_tile(const char *, std::function<Tile *()>) {}
Point tap_point() { return point; }
uint32_t send(const Plugin *, JsonObjectConst data) { request.set(data); return ++next_re; }
namespace ui {
const lv_font_t *font(Font) { static lv_font_t face{}; face.line_height=20; return &face; }
lv_obj_t *text(lv_obj_t *, Font, theme::Role) { return reinterpret_cast<lv_obj_t *>(&objects[used++]); }
lv_obj_t *picture(lv_obj_t *, Placeholder p) { objects[used].no_placeholder = p == Placeholder::NONE; return reinterpret_cast<lv_obj_t *>(&objects[used++]); }
void set_picture(lv_obj_t *p, const std::string &url, Fit, Turn turn, bool mirror) { object(p).source=url; object(p).turn=turn; object(p).mirror=mirror; }
void set_color(lv_obj_t *, theme::Role) {}
void slide_pictures(int dx, uint32_t ms) { ++slides; slide_dx=dx; slide_ms=ms; }
}
}
static void reply(esphome::kidsplayer::Kidsplayer &plugin, uint32_t re, const char *id, int index, int total, const char *cover="", bool animate=true, bool images_ready=true) {
  JsonDocument doc;
  doc["re"] = re; doc["ok"] = true;
  auto result = doc["result"].to<JsonObject>();
  result["total"] = total; result["index"] = index; result["revision"] = "rev1";
  result["center"]["id"] = id;
  result["center"]["title"] = id;
  result["animation"] = animate;
  for (auto slot : {"left3", "left2", "left", "center", "right", "right2", "right3"}) result[slot]["cover"] = cover;
  plugin.on_message(doc.as<JsonObjectConst>());
  // Fake the atlas-ready callback independently of the backend reply.
  if (images_ready) for (auto *tile : plugin.tiles) tile->on_picture(nullptr, tessera::PictureState::SHOWN);
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
  {
    const int first = used;
    LibraryTile tile(&plugin); context.width=400; context.height=380;
    tile.create(context);
    tile.on_tick(0); reply(plugin, next_re, "robin", 0, 3, "/cover_a");
    const int before = slides;
    // Objects are made header, left, right, centre, title, status.
    auto &left=objects[first+1], &right=objects[first+2], &center=objects[first+3];
    assert(left.height == center.height && right.height == center.height);
    assert(left.width == std::min(center.width * 55 / 100, center.x - tessera::ui::px(10)));
    assert(left.y == center.y && right.y == center.y);
    assert(left.mirror && center.mirror && right.mirror);
    assert(left.no_placeholder && center.no_placeholder && right.no_placeholder);
    const int gap = center.x - left.x - left.width;
    const int pitch = center.width/2 + gap + left.width/2;
    point={399,120}; tile.on_tap();
    assert(slides == before); // old covers wait in place during the backend round trip
    now_ms += 5000; tile.on_tick(0); assert(slides == before);
    reply(plugin, next_re, "conni", 1, 3, "/cover_b");
    assert(slides == before);
    point={0,120}; tile.on_tap();
    reply(plugin, next_re, "robin", 0, 3, "/cover_a");
    assert(slides == before);
    point={399,120}; tile.on_tap();
    reply(plugin, next_re, "ep_same_art", 1, 3, "/cover_a");
    assert(slides == before); // same album artwork: no atlas change, never leave it slid away
    point={399,120}; tile.on_tap();
    reply(plugin, next_re, "disabled", 2, 3, "/cover_c", false);
    assert(slides == before);
    point={0,120}; tile.on_tap();
    JsonDocument failure; failure["re"]=next_re; failure["ok"]=false;
    plugin.on_message(failure.as<JsonObjectConst>());
    assert(slides == before); // failed browse never animates
    point={200,120}; tile.on_tap(); // retry browsing
    reply(plugin, next_re, "pair", 0, 2, "/cover_d");
    assert(left.hidden && !right.hidden); // two items never duplicate a cover on both sides
    point={399,120}; tile.on_tap();
    reply(plugin, next_re, "only", 0, 1, "/cover_e");
    assert(left.hidden && right.hidden);
    const auto last_re=next_re;
    point={399,120}; tile.on_tap(); assert(next_re == last_re);
  }
  {
    // A wide/short tile fits all seven places by the original New music rules.
    const int first = used;
    LibraryTile tile(&plugin); context.width=600; context.height=100;
    tile.create(context);
    const int end = used;
    assert(end - first == 10); // header + seven pictures + title + status
    // Created outermost first, centre last: nearer covers layer over outer ones.
    const int offset_order[] = {-3, 3, -2, 2, -1, 1, 0};
    for (int n=1; n<=8; ++n) {
      if (n == 1) tile.on_tick(0);
      if (n > 1) { now_ms += 31000; tile.on_tick(0); }
      reply(plugin, next_re, "center", 0, n, "/art");
      int visible=0;
      for (int i=0; i<7; ++i) {
        auto &o=objects[first+1+i];
        const int offset=offset_order[i], far=std::abs(offset);
        const bool expected = 2*far < n || (2*far == n && offset > 0);
        assert(o.hidden != expected);
        if (!o.hidden) ++visible;
        assert(o.x >= 0 && o.x+o.width <= context.width);
        if (offset < 0) assert(o.turn == tessera::Turn::RIGHT);
        if (offset > 0) assert(o.turn == tessera::Turn::LEFT);
      }
      assert(visible == std::min(n,7));
    }
  }
  {
    LibraryTile tile(&plugin); context.width=400; context.height=380;
    tile.create(context); tile.on_tick(0);
    reply(plugin,next_re,"robin",0,3);
    point={200,120};tile.on_tap();reply(plugin,next_re,"episode",0,3);
    point={200,120};tile.on_tap();
    assert(request["ask"] == "kidsplayer/play" && request["data"]["protocol"] == 1);
    JsonDocument failure; failure["re"]=next_re;failure["ok"]=true;
    failure["result"]["ok"]=false;failure["result"]["message"]="Track nicht verfuegbar";
    plugin.on_message(failure.as<JsonObjectConst>());
    assert(status == "Track nicht verfuegbar"); // application error must precede play-success branch
    const auto last_re=next_re;
    now_ms += 31000;tile.on_tick(0);assert(next_re == last_re); // no automatic retry
  }
  {
    // Backend and image transfer may finish at different times. Neither starts a visible loading phase.
    const int first=used;
    LibraryTile tile(&plugin);context.width=400;context.height=380;
    tile.create(context);
    auto &header=objects[first], &title=objects[used-2], &note=objects[used-1];
    assert(note.text.empty());
    tile.on_tick(0);reply(plugin,next_re,"old",0,3,"/old");
    const auto count=label_events.size();
    point={399,120};tile.on_tap();
    assert(label_events.size() == count && title.text == "old" && note.text.empty());
    now_ms += 5000;tile.on_tick(0);
    assert(label_events.size() == count); // no delayed loading hint either
    reply(plugin,next_re,"new",1,3,"/new",true,false);
    assert(title.text == "old" && note.text.empty()); // still waiting for the atlas
    auto last=next_re;point={200,120};tile.on_tap();
    assert(next_re == last); // do not play/open new selection while old cover is still displayed
    tile.on_picture(nullptr,tessera::PictureState::SHOWN);
    assert(title.text == "new" && note.text.empty() && slides == 0);
    point={399,120};tile.on_tap();
    reply(plugin,next_re,"same_album",2,3,"/new",true,false);
    assert(title.text == "same_album"); // no new picture callback for identical artwork
    point={200,120};tile.on_tap(); // open category; keep old header until its picture is shown
    reply(plugin,next_re,"episode",0,3,"/episode",true,false);
    assert(header.text == "Reihen" && title.text == "same_album");
    tile.on_picture(nullptr,tessera::PictureState::SHOWN);
    assert(header.text == "< Zurueck" && title.text == "episode");
    point={200,120};tile.on_tap();assert(note.text == "Starte ...");
    reply(plugin,next_re,"episode",0,3,"/episode");assert(note.text == "Wiedergabe gestartet");
    point={399,120};tile.on_tap();
    reply(plugin,next_re,"missing",1,3,"/missing",true,false);
    tile.on_picture(nullptr,tessera::PictureState::FAILED);
    assert(title.text == "missing" && note.text == "Cover fehlt");
    now_ms += 31000;tile.on_tick(0);
    reply(plugin,next_re,"missing",1,3,"/missing",true,false);
    assert(note.text == "Cover fehlt"); // a metadata refresh cannot dismiss an unresolved image failure
    point={399,120};tile.on_tap();
    reply(plugin,next_re,"timeout",2,3,"/timeout",true,false);
    now_ms += 21000;tile.on_tick(0);
    assert(note.text == "Cover konnte nicht geladen werden");
    tile.on_picture(nullptr,tessera::PictureState::SHOWN);
    assert(note.text.empty()); // late success clears the prior image timeout
  }
  for (const auto &text : label_events) assert(text != "Laden ...");
  assert(plugin.tiles.empty());  // late replies cannot reference destroyed tiles
  std::cout << "Actual C++ tile: routing, navigation, isolation, playback timeout, compact geometry, cover-flow timing, seven-place flow, application errors, silent loading and destruction passed\n";
}
