// Cover-flow layout and picture API based on New music, Copyright (c) 2026 Max Gramser. MIT.
#include "kidsplayer.h"
#include <algorithm>
#include <string>
namespace esphome::kidsplayer {
namespace ui = tessera::ui;
static constexpr int SIDE = 3;
static std::string plain(const tessera::Text &s) { return {s.data(), s.size()}; }
class LibraryTile : public tessera::Tile {
 public:
  explicit LibraryTile(Kidsplayer *plugin) : plugin_(plugin) { plugin_->tiles.push_back(this); }
  ~LibraryTile() override {
    auto &tiles = plugin_->tiles;
    tiles.erase(std::remove(tiles.begin(), tiles.end(), this), tiles.end());
  }
  void create(const tessera::TileContext &c) override {
    library_ = tessera::Text(c.options["library"] | "");
    player_ = tessera::Text(c.entity ? c.entity : "");
    w_ = c.width; h_ = c.height;
    header_ = ui::text(c.parent, tessera::Font::BODY, theme::INK);
    lv_obj_set_pos(header_, 6, 2);
    lv_obj_set_width(header_, w_ - 12);
    lv_label_set_text(header_, "Reihen");
    // One-row tiles are also the intermediate step when dragging a 1x1 to 2x2.
    // Keep the back header and status clear; compact tiles omit the title row.
    compact_ = h_ < 160;
    y_ = compact_ ? std::min(32, h_ / 3) : 42;
    mirror_ = !compact_;
    // The reference's image-flow geometry, within the area below Kidsplayer's Back header.
    const int width_ = w_, height_ = h_ - y_, gap_ = ui::px(6);
    const int text = compact_ ? 18 : ui::line_height(tessera::Font::TITLE) + ui::line_height(tessera::Font::BODY);
    const int room = std::max(1, height_ - text - gap_);
    int h = mirror_ ? std::min(room * 100 / (100 + tessera::MIRROR_PERCENT / 2), height_ * 100 / (100 + tessera::MIRROR_PERCENT))
                    : room;
    h = std::min(h, width_ / 2);
    size_ = std::max(8, h);
    frame_h_ = mirror_ ? size_ * (100 + tessera::MIRROR_PERCENT) / 100 : size_;
    x_ = (w_ - size_) / 2;
    const int w = size_, centre_x_ = x_;
    const int gap = ui::px(10);
    const int side = std::min(w * 55 / 100, centre_x_ - gap);
    tessera::List<Slot> frames;
    if (side >= w / 4) {
      // BEGIN NEW MUSIC IMAGE FRAMES: copied unchanged from the pinned reference.
      const int spread = SIDE > 1 ? (centre_x_ - gap - side) / (SIDE - 1) : 0;
      // Close together, as a stack of records: on a wide tile the flow keeps to the middle.
      const int stepx = std::max(w / 6, std::min(side * 70 / 100, spread));
      for (int k = SIDE; k >= 1; --k) {   // the outermost first: a place made later lies over one made earlier
        const int inner = centre_x_ - gap - side - (k - 1) * stepx;
        if (inner < 0) continue;
        frames.push_back({-k, inner, side, nullptr});
        frames.push_back({k, width_ - inner - side, side, nullptr});
      }
      // END NEW MUSIC IMAGE FRAMES
    }
    frames.push_back({0, centre_x_, w, nullptr});
    pitch_ = side >= w / 4 ? w / 2 + gap + side / 2 : w + gap;
    for (Slot f : frames) {
      f.place = ui::picture(c.parent, tessera::Placeholder::NONE);
      lv_obj_set_pos(f.place, f.x, y_);
      lv_obj_set_size(f.place, f.w, frame_h_);
      slots_.push_back(f);
    }
    title_ = ui::text(c.parent, compact_ ? tessera::Font::BODY : tessera::Font::TITLE, theme::INK);
    lv_obj_set_pos(title_, 4, h_ - text);
    lv_obj_set_width(title_, w_ - 8);
    lv_label_set_long_mode(title_, LV_LABEL_LONG_DOT);
    lv_obj_set_style_text_align(title_, LV_TEXT_ALIGN_CENTER, 0);
    if (compact_) lv_obj_add_flag(title_, LV_OBJ_FLAG_HIDDEN);
    status_ = ui::text(c.parent, tessera::Font::BODY, theme::MUTED);
    lv_obj_set_pos(status_, 4, h_ - 22);
    lv_obj_set_width(status_, w_ - 8);
    lv_label_set_long_mode(status_, LV_LABEL_LONG_DOT);
    lv_label_set_text(status_, "Laden ...");
  }
  void on_tick(uint32_t) override {
    const uint32_t now = esphome::millis();
    if (pending_ && now - sent_ > 20000) {
      pending_ = 0;
      // A play request is NEVER retried; a timeout may mean the server already started it.
      lv_label_set_text(status_, playing_ ? "Keine Antwort; Player pruefen" : "Keine Antwort; tippen");
      playing_ = false;
      failed_ = true;
      refreshed_ = now;
    }
    if (!pending_ && ((!loaded_ && !failed_) || (!failed_ && now - refreshed_ > 30000))) request(false);
  }
  void on_tap() override {
    if (pending_) return;
    auto p = tessera::tap_point();
    if (p.x < 0 || p.y < 0) return;
    if (p.y < y_ && !category_.empty()) {
      category_ = tessera::Text(); index_ = saved_; request(false); return;
    }
    if (failed_ || !loaded_) { request(false); return; }
    if (p.x < x_) { index_ = (index_ + total_ - 1) % total_; move(1); return; }
    if (p.x >= x_ + size_) { index_ = (index_ + 1) % total_; move(-1); return; }
    if (category_.empty()) {
      saved_ = index_; category_ = selected_; index_ = 0; request(false);
    } else request(true);
  }
  void answer(JsonObjectConst message) {
    if (!pending_ || (message["re"] | 0u) != pending_) return;
    pending_ = 0; refreshed_ = esphome::millis();
    if (!(message["ok"] | false)) {
      lv_label_set_text(status_, message["error"] | "Fehler");
      failed_ = true; playing_ = false; return;
    }
    if (playing_) {
      lv_label_set_text(status_, "Wiedergabe gestartet"); playing_ = false; failed_ = false; return;
    }
    JsonObjectConst data = message["result"];
    total_ = data["total"] | 0;
    if (total_ < 1) { failed_ = true; lv_label_set_text(status_, "Bibliothek leer"); return; }
    index_ = data["index"] | 0;
    revision_ = tessera::Text(data["revision"] | "");
    selected_ = tessera::Text(data["center"]["id"] | "");
    animation_ = data["animation"] | true;
    const char *keys[] = {"left3", "left2", "left", "center", "right", "right2", "right3"};
    const std::string next_cover = data["center"]["cover"] | "";
    // Unlike New music, browsing is asynchronous. Keep the old atlas stationary
    // until the new addresses are available, then slide beside set_picture().
    // A shared album cover (or no cover) creates no new atlas: sliding it could
    // otherwise remain displaced forever, since Tessera resets on a new atlas.
    if (direction_ && animation_ && loaded_ && !covers_[SIDE].empty() &&
        !next_cover.empty() && plain(covers_[SIDE]) != next_cover)
      ui::slide_pictures(std::max(-w_, std::min(w_, direction_ * pitch_)), 320);
    direction_ = 0;
    for (auto &slot : slots_) {
      const int i = slot.offset + SIDE;
      auto item = data[keys[i]];
      const bool visible = shown(slot.offset) && !item.isNull();
      covers_[i] = tessera::Text(visible ? (item["cover"] | "") : "");
      const tessera::Turn turn = !slot.offset ? tessera::Turn::NONE
                                  : slot.offset < 0 ? tessera::Turn::RIGHT : tessera::Turn::LEFT;
      ui::set_picture(slot.place, plain(covers_[i]), tessera::Fit::CONTAIN, turn, mirror_);
      if (visible) lv_obj_remove_flag(slot.place, LV_OBJ_FLAG_HIDDEN);
      else lv_obj_add_flag(slot.place, LV_OBJ_FLAG_HIDDEN);
    }
    lv_label_set_text(header_, category_.empty() ? "Reihen" : "< Zurueck");
    lv_label_set_text(title_, (data["show_titles"] | true) ? (data["center"]["title"] | "") : "");
    lv_label_set_text(status_, "");
    loaded_ = true; failed_ = false;
  }
  void on_picture(lv_obj_t *, tessera::PictureState state) override {
    if (state == tessera::PictureState::NONE || state == tessera::PictureState::FAILED)
      lv_label_set_text(status_, "Cover fehlt");
  }
  void on_theme() override {
    ui::set_color(title_, theme::INK); ui::set_color(header_, theme::INK); ui::set_color(status_, theme::MUTED);
  }
 private:
  struct Slot {
    int offset = 0, x = 0, w = 0;
    lv_obj_t *place = nullptr;
  };
  // New music's no-duplicate rule, applied to the active category/episode count.
  bool shown(int offset) const {
    const int n = total_, far = offset < 0 ? -offset : offset;
    return 2 * far < n || (2 * far == n && offset > 0);
  }
  void move(int direction) {
    if (total_ > 1) request(false, direction);
  }
  void request(bool play, int direction = 0) {
    direction_ = direction;
    if (library_.empty()) { lv_label_set_text(status_, "Bibliotheks-ID fehlt"); loaded_ = true; failed_ = true; return; }
    JsonDocument doc;
    doc["ask"] = play ? "kidsplayer/play" : "kidsplayer/browse";
    auto d = doc["data"].to<JsonObject>();
    d["library"] = plain(library_); d["player"] = plain(player_); d["category"] = plain(category_);
    if (play) { d["episode"] = plain(selected_); d["revision"] = plain(revision_); }
    else d["index"] = index_;
    playing_ = play;
    pending_ = tessera::send(plugin_, doc.as<JsonObjectConst>());
    sent_ = esphome::millis(); refreshed_ = sent_;
    lv_label_set_text(status_, pending_ ? (play ? "Starte ..." : "Laden ...") : "Tessera nicht verbunden");
    if (!pending_) { failed_ = true; loaded_ = true; playing_ = false; }
  }
  Kidsplayer *plugin_;
  tessera::Text library_, player_, category_, selected_, revision_, covers_[2 * SIDE + 1];
  tessera::List<Slot> slots_;
  lv_obj_t *header_ = nullptr, *title_ = nullptr, *status_ = nullptr;
  int w_ = 0, h_ = 0, x_ = 0, y_ = 0, size_ = 0, frame_h_ = 0, pitch_ = 0, direction_ = 0, index_ = 0, saved_ = 0, total_ = 0;
  uint32_t pending_ = 0, sent_ = 0, refreshed_ = 0;
  bool mirror_ = false, compact_ = false, playing_ = false, loaded_ = false, failed_ = false, animation_ = true;
};
void Kidsplayer::setup() { add_tile("library", [this]() { return new LibraryTile(this); }); }
void Kidsplayer::on_message(JsonObjectConst message) { for (auto *tile : tiles) tile->answer(message); }
}
