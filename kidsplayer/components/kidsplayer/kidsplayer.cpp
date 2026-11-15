// Cover-flow layout and picture API based on New music, Copyright (c) 2026 Max Gramser. MIT.
#include "kidsplayer.h"
#include <algorithm>
#include <string>
namespace esphome::kidsplayer {
namespace ui = tessera::ui;
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
    int available = std::max(24, h_ - 82);
    size_ = std::max(24, std::min(w_ * 62 / 100, available));
    x_ = (w_ - size_) / 2;
    y_ = 42;
    for (int slot : {0, 2, 1}) {
      art_[slot] = ui::picture(c.parent);
      int d = slot == 1 ? size_ : size_ * 65 / 100;
      int x = slot == 0 ? x_ - d * 80 / 100 : slot == 2 ? x_ + size_ - d / 5 : x_;
      lv_obj_set_pos(art_[slot], x, y_ + (size_ - d) / 2);
      lv_obj_set_size(art_[slot], d, d);
    }
    title_ = ui::text(c.parent, tessera::Font::BODY, theme::INK);
    lv_obj_set_pos(title_, 4, y_ + size_ + 2);
    lv_obj_set_width(title_, w_ - 8);
    lv_label_set_long_mode(title_, LV_LABEL_LONG_DOT);
    lv_obj_set_style_text_align(title_, LV_TEXT_ALIGN_CENTER, 0);
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
    if (p.y < 42 && !category_.empty()) {
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
    const char *slots[] = {"left", "center", "right"};
    for (int i = 0; i < 3; ++i) {
      auto item = data[slots[i]];
      ui::set_picture(art_[i], item["cover"] | "", tessera::Fit::CONTAIN,
        i == 0 ? tessera::Turn::RIGHT : i == 2 ? tessera::Turn::LEFT : tessera::Turn::NONE);
      if (i != 1 && total_ == 1) lv_obj_add_flag(art_[i], LV_OBJ_FLAG_HIDDEN);
      else lv_obj_remove_flag(art_[i], LV_OBJ_FLAG_HIDDEN);
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
  void move(int direction) {
    if (animation_) ui::slide_pictures(direction * size_ / 2, 220);
    request(false);
  }
  void request(bool play) {
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
  tessera::Text library_, player_, category_, selected_, revision_;
  lv_obj_t *art_[3] = {}, *header_ = nullptr, *title_ = nullptr, *status_ = nullptr;
  int w_ = 0, h_ = 0, x_ = 0, y_ = 0, size_ = 0, index_ = 0, saved_ = 0, total_ = 0;
  uint32_t pending_ = 0, sent_ = 0, refreshed_ = 0;
  bool playing_ = false, loaded_ = false, failed_ = false, animation_ = true;
};
void Kidsplayer::setup() { add_tile("library", [this]() { return new LibraryTile(this); }); }
void Kidsplayer::on_message(JsonObjectConst message) { for (auto *tile : tiles) tile->answer(message); }
}
