// power_ui.cpp — xem power_ui.h
#include "power_ui.h"

#include <bluefruit.h>  // sd_softdevice_is_enabled, sd_power_usbregstatus_get

#include "config.h"

// ============================================================================
// Pin
// ============================================================================
namespace Power {

void begin() {
  pinMode(VBAT_ENABLE, OUTPUT);
  digitalWrite(VBAT_ENABLE, LOW);  // LOW = nối cầu chia vào ADC (luôn để LOW)
  // Thang 0–3,6 V (mặc định của gói board): dùng chung cho đọc pin và ECG AD8232 (ra tới 3,3 V).
  analogReference(AR_DEFAULT);
  analogReadResolution(12);
}

uint16_t readBatteryMv() {
  uint32_t sum = 0;
  for (int i = 0; i < 8; i++) sum += analogRead(PIN_VBAT);
  float v_adc = (sum / 8.0f) * 3600.0f / 4096.0f;
  return (uint16_t)(v_adc * VBAT_DIVIDER);
}

uint8_t percentFromMv(uint16_t mv) {
  static const uint16_t table[][2] = {
      {4200, 100}, {4150, 95}, {4110, 90}, {4080, 85}, {4020, 80}, {3980, 70}, {3950, 60},
      {3910, 50},  {3870, 40}, {3850, 30}, {3840, 20}, {3800, 10}, {3700, 5},  {3500, 0},
  };
  const int n = sizeof(table) / sizeof(table[0]);
  if (mv >= table[0][0]) return 100;
  if (mv <= table[n - 1][0]) return 0;
  for (int i = 1; i < n; i++) {
    if (mv >= table[i][0]) {
      float f = (float)(mv - table[i][0]) / (table[i - 1][0] - table[i][0]);
      return (uint8_t)(table[i][1] + f * (table[i - 1][1] - table[i][1]));
    }
  }
  return 0;
}

bool usbPowered() {
  uint32_t reg = 0;
  uint8_t sd_en = 0;
  sd_softdevice_is_enabled(&sd_en);
  if (sd_en) {
    sd_power_usbregstatus_get(&reg);
  } else {
    reg = NRF_POWER->USBREGSTATUS;
  }
  return (reg & POWER_USBREGSTATUS_VBUSDETECT_Msk) != 0;
}

}  // namespace Power

// ============================================================================
// Motor rung (không chặn loop)
// ============================================================================
namespace Vibe {

const uint16_t PATTERN_IMPACT[] = {300, 200, 300, 200, 300, 0};  // "bạn có sao không?"
const uint16_t PATTERN_ALERT_SENT[] = {800, 0};
const uint16_t PATTERN_ACK[] = {150, 150, 150, 0};               // người nhà đã nhận
const uint16_t PATTERN_CANCEL[] = {100, 0};

static uint16_t single_[2] = {0, 0};
static const uint16_t* steps_ = nullptr;
static int idx_ = 0;
static uint32_t next_ms_ = 0;

void begin() {
  pinMode(PIN_VIBRATION, OUTPUT);
  digitalWrite(PIN_VIBRATION, LOW);
}

void pattern(const uint16_t* steps) {
  steps_ = steps;
  idx_ = 0;
  digitalWrite(PIN_VIBRATION, HIGH);
  next_ms_ = millis() + steps_[0];
}

void pulse(uint16_t on_ms) {
  single_[0] = on_ms;
  single_[1] = 0;
  pattern(single_);
}

void update() {
  if (!steps_ || (int32_t)(millis() - next_ms_) < 0) return;
  idx_++;
  if (steps_[idx_] == 0) {
    digitalWrite(PIN_VIBRATION, LOW);
    steps_ = nullptr;
    return;
  }
  digitalWrite(PIN_VIBRATION, (idx_ % 2 == 0) ? HIGH : LOW);
  next_ms_ = millis() + steps_[idx_];
}

}  // namespace Vibe

// ============================================================================
// Nút SOS: giữ 3 s = SOS; bấm ngắn (< 1 s) = huỷ đếm ngược té ngã
// ============================================================================
namespace Button {

static bool stable_pressed_ = false;
static bool last_raw_ = false;
static uint32_t last_change_ms_ = 0;
static uint32_t press_start_ms_ = 0;
static bool hold_fired_ = false;

void begin() { pinMode(PIN_SOS_BUTTON, INPUT_PULLUP); }

Event update() {
  bool raw = digitalRead(PIN_SOS_BUTTON) == LOW;
  uint32_t now = millis();
  if (raw != last_raw_) {
    last_raw_ = raw;
    last_change_ms_ = now;
  }
  if (now - last_change_ms_ < 30) return NONE;  // chống dội

  Event ev = NONE;
  if (raw && !stable_pressed_) {
    stable_pressed_ = true;
    press_start_ms_ = now;
    hold_fired_ = false;
  } else if (raw && stable_pressed_) {
    if (!hold_fired_ && now - press_start_ms_ >= SOS_HOLD_MS) {
      hold_fired_ = true;
      ev = LONG_HOLD;
    }
  } else if (!raw && stable_pressed_) {
    stable_pressed_ = false;
    if (!hold_fired_ && now - press_start_ms_ < CANCEL_PRESS_MAX_MS) ev = SHORT_PRESS;
  }
  return ev;
}

}  // namespace Button
