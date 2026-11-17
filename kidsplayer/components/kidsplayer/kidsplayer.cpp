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
    heading_ = tessera::Text(c.options["heading"] | "Reihen");
    player_ = tessera::Text(c.entity ? c.entity : "");
    w_ = c.width; h_ = c.height;
    parent_ = c.parent;
    // The host presses its card, but its atlas keeps the unpressed ground colour.
    // A non-interactive local surface keeps the image area visually steady.
    // Keep block's Tessera-rounded corners so the host's pressed rim stays visible.
    background_ = ui::block(c.parent, theme::CARD);
    lv_obj_set_pos(background_, 0, 0);
    lv_obj_set_size(background_, w_, h_);
    paint_background();
    header_ = ui::label(c.parent, tessera::Font::BODY, theme::INK);
    lv_obj_set_width(header_, w_ - 12);
    lv_label_set_long_mode(header_, LV_LABEL_LONG_DOT);
    lv_label_set_text(header_, plain(heading_).c_str());
    // One-row tiles are also the intermediate step when dragging a 1x1 to 2x2.
    // Keep the back header and status clear; compact tiles omit the title row.
    compact_ = h_ < 160;
    controls_ = w_ >= ui::px(280) && h_ >= ui::px(220) && !player_.empty();
    const int button = ui::px(44), button_gap = ui::px(8), margin = ui::px(4);
    const int back_size = controls_ ? button : std::min(ui::px(40), h_ / 3);
    const int key_y = controls_ ? margin : 0;
    y_ = std::max(key_y + back_size + ui::px(4), ui::line_height(tessera::Font::BODY) + 4);
    lv_obj_set_pos(header_, 6, key_y + (back_size - ui::line_height(tessera::Font::BODY)) / 2);
    if (controls_) lv_obj_set_width(header_, w_ - margin - 2 * button - button_gap - 12);
    // One footer alternates between title and status. Keep the entire cover
    // above it; only the reflection may extend behind the footer.
    const int width_ = w_, height_ = h_ - y_, gap_ = ui::px(6);
    const int text = std::max(ui::line_height(tessera::Font::TITLE), ui::line_height(tessera::Font::BODY)) + ui::px(4);
    const int footer = text;
    const int room = std::max(1, height_ - footer - gap_);
    // Let the cover use roughly 71% of a wide tile while keeping both inner
    // neighbours. On shallow tiles the fixed 30% reflection used too much of
    // the available height: retain it only if it costs at most 10% cover size.
    const int width_cap = std::max(8, (width_ - 2 * ui::px(10)) * 3 / 4);
    const int full_size = std::min(room, width_cap);
    const int reflected_size = std::min(width_cap, std::min(
        room * 100 / (100 + tessera::MIRROR_PERCENT / 2),
        height_ * 100 / (100 + tessera::MIRROR_PERCENT)));
    mirror_ = !compact_ && reflected_size * 100 >= full_size * 90;
    size_ = std::max(8, mirror_ ? reflected_size : full_size);
    frame_h_ = mirror_ ? size_ * (100 + tessera::MIRROR_PERCENT) / 100 : size_;
    const int frame_area = mirror_ ? height_ : room;
    frame_y_ = y_ + std::max(0, (frame_area - frame_h_) / 2);
    x_ = (w_ - size_) / 2;
    const int w = size_, centre_x_ = x_;
    const int gap = ui::px(10);
    const int side = std::min(w * 55 / 100, centre_x_ - gap);
    tessera::List<Slot> frames;
    if (side >= std::max(1, w / 6)) {
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
    for (Slot f : frames) {
      f.place = ui::picture(c.parent, tessera::Placeholder::NONE);
      lv_obj_set_pos(f.place, f.x, frame_y_);
      lv_obj_set_size(f.place, f.w, frame_h_);
      slots_.push_back(f);
    }
    back_ = make_key(c.parent, margin, key_y, back_size, 0xF004D);
    visible(back_, false);
    if (controls_) {
      media_ = make_key(c.parent, w_ - margin - 2 * button - button_gap,
                        key_y, button, 0xF01D8);
      playback_ = make_key(c.parent, w_ - margin - button,
                           key_y, button, 0xF040E);
    }
    const int words_width = w_ - 8;
    const int words_y = h_ - footer + (footer - text) / 2;
    title_ = ui::label(c.parent, compact_ ? tessera::Font::BODY : tessera::Font::TITLE, theme::INK);
    lv_obj_set_pos(title_, 4, words_y);
    lv_obj_set_width(title_, words_width);
    lv_label_set_long_mode(title_, LV_LABEL_LONG_DOT);
    lv_obj_set_style_text_align(title_, LV_TEXT_ALIGN_CENTER, 0);
    if (compact_) lv_obj_add_flag(title_, LV_OBJ_FLAG_HIDDEN);
    status_ = ui::label(c.parent, tessera::Font::BODY, theme::MUTED);
    lv_obj_set_pos(status_, 4, words_y);
    lv_obj_set_width(status_, words_width);
    lv_label_set_long_mode(status_, LV_LABEL_LONG_DOT);
    lv_obj_set_style_text_align(status_, LV_TEXT_ALIGN_CENTER, 0);
    show_status("");
  }
  void on_state(JsonObjectConst data) override {
    const char *state = data["state"] | "";
    player_playing_ = std::string(state) == "playing";
    player_unavailable_ = std::string(state) == "unavailable" || std::string(state) == "unknown";
    if (playback_.icon) {
      const uint32_t glyph = player_playing_ ? 0xF03E4 : !*state ? 0xF040E : 0xF040A;
      lv_label_set_text(playback_.icon, ui::icon(glyph).c_str());
      ui::set_color(playback_.icon, player_unavailable_ ? theme::MUTED : theme::INK);
    }
  }
  void on_tick(uint32_t) override {
    paint_background();
    const uint32_t now = esphome::millis();
    if (pending_ && now - sent_ > 20000) {
      pending_ = 0;
      // A play request is NEVER retried; a timeout may mean the server already started it.
      show_status(playing_ ? "Keine Antwort; Player pruefen" : "Keine Antwort; tippen");
      playing_ = false;
      failed_ = true;
      refreshed_ = now;
    }
    if (awaiting_picture_ && now - picture_sent_ > 20000) {
      commit_browse();
      picture_failed_ = true;
      show_status("Cover konnte nicht geladen werden");
    }
    if (!pending_ && !awaiting_picture_ && ((!loaded_ && !failed_) || (!failed_ && now - refreshed_ > 30000))) request(false);
  }
  void on_tap() override {
    auto p = tessera::tap_point();
    if (p.x < 0 || p.y < 0 || p.x >= w_ || p.y >= h_) return;
    // Player controls remain usable while metadata/artwork is on its way.
    if (controls_ && media_.contains(p)) {
      if (!plugin_->open_media(plain(player_))) show_status("Normale Medienkachel fehlt");
      return;
    }
    if (controls_ && playback_.contains(p)) {
      const uint32_t now = esphome::millis();
      if (control_sent_ && now - control_sent_ < 400) return;
      if (player_unavailable_) { show_status("Player nicht erreichbar"); return; }
      // Operate the current queue; never resend kidsplayer/play on resume.
      if (!tessera::wish(plain(player_), tessera::Wish::PLAYING, player_playing_ ? "0" : "1"))
        show_status("Steuerung nicht verbunden");
      else control_sent_ = now;
      return;
    }
    if (pending_ || awaiting_picture_) return;
    if (!category_.empty() && back_.contains(p)) {
      category_ = tessera::Text(); index_ = saved_; request(false); return;
    }
    if (p.y < y_) return;
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
      show_status(message["error"] | "Fehler");
      failed_ = true; playing_ = false; return;
    }
    JsonObjectConst data = message["result"];
    if (data["ok"].is<bool>() && !(data["ok"] | true)) {
      show_status(data["message"] | "Fehler; HA-Protokoll pruefen");
      failed_ = true; playing_ = false; return;
    }
    if (playing_) {
      show_status("Wiedergabe gestartet"); playing_ = false; failed_ = false; return;
    }
    total_ = data["total"] | 0;
    if (total_ < 1) { failed_ = true; show_status("Bibliothek leer"); return; }
    index_ = data["index"] | 0;
    revision_ = tessera::Text(data["revision"] | "");
    selected_ = tessera::Text(data["center"]["id"] | "");
    const char *keys[] = {"left3", "left2", "left", "center", "right", "right2", "right3"};
    pending_title_ = tessera::Text((data["show_titles"] | true) ? (data["center"]["title"] | "") : "");
    pending_back_ = !category_.empty();
    awaiting_picture_ = false;
    picture_sent_ = esphome::millis();
    for (auto &slot : slots_) {
      const int i = slot.offset + SIDE;
      auto item = data[keys[i]];
      const bool visible = shown(slot.offset) && !item.isNull();
      const std::string next_cover = visible ? (item["cover"] | "") : "";
      // set_picture keeps the old atlas until the replacement arrives. Keep the
      // old title/header too; a shared cover needs no new atlas/callback.
      if (!next_cover.empty() && next_cover != plain(covers_[i])) awaiting_picture_ = true;
      covers_[i] = tessera::Text(next_cover);
      const tessera::Turn turn = !slot.offset ? tessera::Turn::NONE
                                  : slot.offset < 0 ? tessera::Turn::RIGHT : tessera::Turn::LEFT;
      ui::set_picture(slot.place, plain(covers_[i]), tessera::Fit::CONTAIN, turn, mirror_);
      if (visible) lv_obj_remove_flag(slot.place, LV_OBJ_FLAG_HIDDEN);
      else lv_obj_add_flag(slot.place, LV_OBJ_FLAG_HIDDEN);
    }
    loaded_ = true; failed_ = false;
    if (!awaiting_picture_) commit_browse();
  }
  void on_picture(lv_obj_t *, tessera::PictureState state) override {
    if (state == tessera::PictureState::SHOWN) {
      const bool recovering = picture_failed_;
      picture_failed_ = false;
      if (awaiting_picture_) commit_browse();
      else if (recovering) show_status("");
    } else {
      picture_failed_ = true;
      if (awaiting_picture_) commit_browse();
      show_status("Cover fehlt");
    }
  }
  void on_theme() override {
    background_custom_ = false;
    ui::set_fill(background_, tessera::Tone::NORMAL, theme::CARD);
    ui::set_color(title_, theme::INK); ui::set_color(header_, theme::INK); ui::set_color(status_, theme::MUTED);
    for (auto *key : {&back_, &media_, &playback_}) {
      if (!key->body) continue;
      ui::set_fill(key->body, tessera::Tone::NORMAL, theme::KEY);
      ui::set_color(key->icon, key == &playback_ && player_unavailable_ ? theme::MUTED : theme::INK);
    }
  }
 private:
  struct RoundKey {
    lv_obj_t *body = nullptr, *icon = nullptr;
    int x = 0, y = 0, size = 0;
    bool contains(tessera::Point p) const {
      // A generous square touch area around the visible circle.
      return body && p.x >= x && p.x < x + size && p.y >= y && p.y < y + size;
    }
  };
  static RoundKey make_key(lv_obj_t *parent, int x, int y, int size, uint32_t glyph) {
    RoundKey key;
    key.x = x; key.y = y; key.size = size;
    key.body = ui::block(parent, theme::KEY);
    lv_obj_set_pos(key.body, x, y);
    lv_obj_set_size(key.body, size, size);
    lv_obj_set_style_radius(key.body, LV_RADIUS_CIRCLE, 0);
    key.icon = ui::label(key.body, tessera::Font::ICON_SMALL, theme::INK);
    lv_label_set_text(key.icon, ui::icon(glyph).c_str());
    lv_obj_set_width(key.icon, size);
    lv_obj_set_pos(key.icon, 0, (size - ui::line_height(tessera::Font::ICON_SMALL)) / 2);
    lv_obj_set_style_text_align(key.icon, LV_TEXT_ALIGN_CENTER, 0);
    return key;
  }
  static void visible(const RoundKey &key, bool show) {
    if (show) lv_obj_remove_flag(key.body, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_add_flag(key.body, LV_OBJ_FLAG_HIDDEN);
  }
  void show_status(const char *message) {
    lv_label_set_text(status_, message);
    if (compact_ || *message) lv_obj_add_flag(title_, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_remove_flag(title_, LV_OBJ_FLAG_HIDDEN);
  }
  void paint_background() {
    // Read only the host's normal local style, never its current pressed style.
    // Do not modify the host or any neighbouring tile.
    lv_obj_t *host = parent_ ? lv_obj_get_parent(parent_) : nullptr;
    lv_style_value_t value;
    if (host && lv_obj_get_local_style_prop(host, LV_STYLE_BG_OPA, &value, LV_PART_MAIN) == LV_STYLE_RES_FOUND && value.num == LV_OPA_TRANSP) {
      background_custom_ = false;
      ui::set_fill(background_, tessera::Tone::NORMAL, theme::PAGE);
    } else if (host && lv_obj_get_local_style_prop(host, LV_STYLE_BG_COLOR, &value, LV_PART_MAIN) == LV_STYLE_RES_FOUND) {
      if (!background_custom_ || !lv_color_eq(background_color_, value.color))
        lv_obj_set_style_bg_color(background_, value.color, 0);
      background_color_ = value.color;
      background_custom_ = true;
    } else {
      background_custom_ = false;
      ui::set_fill(background_, tessera::Tone::NORMAL, theme::CARD);
    }
  }
  struct Slot {
    int offset = 0, x = 0, w = 0;
    lv_obj_t *place = nullptr;
  };
  // New music's no-duplicate rule, applied to the active category/episode count.
  bool shown(int offset) const {
    const int n = total_, far = offset < 0 ? -offset : offset;
    return 2 * far < n || (2 * far == n && offset > 0);
  }
  void commit_browse() {
    awaiting_picture_ = false;
    if (pending_back_) lv_obj_add_flag(header_, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_remove_flag(header_, LV_OBJ_FLAG_HIDDEN);
    visible(back_, pending_back_);
    lv_label_set_text(title_, plain(pending_title_).c_str());
    if (!picture_failed_) show_status("");
  }
  void move(int) {
    if (total_ > 1) request(false);
  }
  void request(bool play) {
    if (library_.empty()) { show_status("Bibliotheks-ID fehlt"); loaded_ = true; failed_ = true; return; }
    JsonDocument doc;
    doc["ask"] = play ? "kidsplayer/play" : "kidsplayer/browse";
    auto d = doc["data"].to<JsonObject>();
    d["protocol"] = 1;
    d["library"] = plain(library_); d["player"] = plain(player_); d["category"] = plain(category_);
    if (play) { d["episode"] = plain(selected_); d["revision"] = plain(revision_); }
    else d["index"] = index_;
    playing_ = play;
    pending_ = tessera::send(plugin_, doc.as<JsonObjectConst>());
    sent_ = esphome::millis(); refreshed_ = sent_;
    if (!pending_) show_status("Tessera nicht verbunden");
    else if (play) show_status("Starte ...");
    if (!pending_) { failed_ = true; loaded_ = true; playing_ = false; }
  }
  Kidsplayer *plugin_;
  tessera::Text library_, player_, heading_, category_, selected_, revision_, pending_title_, covers_[2 * SIDE + 1];
  RoundKey back_, media_, playback_;
  tessera::List<Slot> slots_;
  lv_obj_t *parent_ = nullptr, *background_ = nullptr, *header_ = nullptr, *title_ = nullptr, *status_ = nullptr;
  int w_ = 0, h_ = 0, x_ = 0, y_ = 0, frame_y_ = 0, size_ = 0, frame_h_ = 0, index_ = 0, saved_ = 0, total_ = 0;
  uint32_t pending_ = 0, sent_ = 0, refreshed_ = 0, picture_sent_ = 0, control_sent_ = 0;
  lv_color_t background_color_{};
  bool background_custom_ = false, mirror_ = false, compact_ = false, playing_ = false, loaded_ = false, failed_ = false, awaiting_picture_ = false, picture_failed_ = false;
  bool controls_ = false, pending_back_ = false, player_playing_ = false, player_unavailable_ = false;
};
void Kidsplayer::setup() { add_tile("library", [this]() { return new LibraryTile(this); }); }
void Kidsplayer::on_message(JsonObjectConst message) { for (auto *tile : tiles) tile->answer(message); }
}
