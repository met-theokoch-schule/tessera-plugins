// Render the actual embedded icon with real LVGL, not UI doubles.
#include "../components/kidsplayer/homepod_mini_icon.h"
#include <cstdio>
#include <cstdint>
#include <cmath>
#include <cstring>
using namespace esphome::kidsplayer;
alignas(32) static uint16_t pixels[64*64];
int main(int argc,char **argv) {
  const bool dark = argc > 2 && std::strcmp(argv[2], "dark") == 0;
  lv_init();
  lv_display_t *display=lv_display_create(64,64);
  lv_display_set_color_format(display,LV_COLOR_FORMAT_RGB565);
  lv_display_set_buffers(display,pixels,nullptr,sizeof(pixels),LV_DISPLAY_RENDER_MODE_DIRECT);
  lv_display_set_flush_cb(display,[](lv_display_t *d,const lv_area_t *,uint8_t *) {lv_display_flush_ready(d);});
  auto *root=lv_screen_active();
  lv_obj_set_style_bg_color(root,lv_color_hex(dark ? 0 : 0xFFFFFF),0);
  lv_obj_set_style_bg_opa(root,LV_OPA_COVER,0);
  auto *image=lv_image_create(root);
  lv_image_set_src(image,&homepod_mini_image());
  lv_image_set_scale(image,224);
  lv_obj_set_style_image_recolor(image,lv_color_hex(dark ? 0xFFFFFF : 0),0);
  lv_obj_set_style_image_recolor_opa(image,LV_OPA_COVER,0);
  lv_obj_set_pos(image,16,16);
  lv_refr_now(display);
  if(argc>1) {
    FILE *out=fopen(argv[1],"wb");fprintf(out,"P6\n64 64\n255\n");
    for(auto pixel:pixels) {
      unsigned char rgb[]={static_cast<unsigned char>(((pixel>>11)&31)*255/31),static_cast<unsigned char>(((pixel>>5)&63)*255/63),static_cast<unsigned char>((pixel&31)*255/31)};
      fwrite(rgb,1,3,out);
    }
    fclose(out);
  }
  int checked=0,mismatched=0;
  for(int y=0;y<64;++y) for(int x=0;x<64;++x) {
    const int sx=int(std::floor((x-32)/0.875+16)),sy=int(std::floor((y-32)/0.875+16));
    if(sx<1||sy<1||sx>=31||sy>=31)continue;
    bool opaque=true,transparent=true;
    for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){
      const auto alpha=HOMEPOD_MINI_ALPHA[(sy+dy)*32+sx+dx];
      opaque=opaque&&alpha>240;transparent=transparent&&alpha<15;
    }
    if(!opaque&&!transparent)continue;
    ++checked;
    int grey=((pixels[y*64+x]>>11)&31)*255/31;
    if (dark) grey=255-grey;
    if((opaque&&grey>25)||(transparent&&grey<230))++mismatched;
  }
  printf("Real LVGL rendered icon: %d checked interior/background pixels, %d mismatches\n",checked,mismatched);
  lv_display_delete(display);lv_deinit();
  return mismatched?2:0;
}
