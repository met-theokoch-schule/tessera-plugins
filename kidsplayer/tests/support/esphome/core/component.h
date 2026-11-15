#pragma once
#include <cstdint>
namespace esphome {
namespace setup_priority { constexpr float DATA=600; }
uint32_t millis();
class Component { public: virtual ~Component() = default; virtual void setup() {} virtual float get_setup_priority() const {return 0;} };
}
