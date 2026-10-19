// ad8232.cpp — xem ad8232.h
#include "ad8232.h"

#include <bluefruit.h>  // sd_clock_hfclk_request / release (SoftDevice)

#include "config.h"

namespace {
const uint16_t BUF = 512;            // ~2 s dữ liệu, phải là lũy thừa của 2
const uint16_t LEAD_OFF_BIT = 0x8000;  // ADC chỉ 12 bit -> dùng bit 15 làm cờ tuột điện cực
volatile uint16_t buf[BUF];
volatile uint16_t head = 0;  // ngắt ghi
volatile uint16_t tail = 0;  // loop() đọc
volatile uint32_t lost = 0;
bool running = false;
}  // namespace

extern "C" void TIMER4_IRQHandler(void) {
  if (NRF_TIMER4->EVENTS_COMPARE[0]) {
    NRF_TIMER4->EVENTS_COMPARE[0] = 0;
    uint16_t next = (head + 1) & (BUF - 1);
    if (next == tail) {
      lost++;
      return;
    }
    uint16_t v = (uint16_t)analogRead(PIN_ECG_OUT) & 0x0FFF;
    if (digitalRead(PIN_ECG_LO_PLUS) || digitalRead(PIN_ECG_LO_MINUS)) v |= LEAD_OFF_BIT;
    buf[head] = v;
    head = next;
  }
}

namespace Ad8232 {

void begin() {
  pinMode(PIN_ECG_LO_PLUS, INPUT);
  pinMode(PIN_ECG_LO_MINUS, INPUT);
}

void start() {
  stop();
  head = tail = 0;
  lost = 0;
  uint8_t sd_en = 0;
  sd_softdevice_is_enabled(&sd_en);
  if (sd_en) sd_clock_hfclk_request();  // timer chạy theo thạch anh thay vì RC nội (±1,5%)
  analogReadResolution(12);
  NRF_TIMER4->MODE = TIMER_MODE_MODE_Timer;
  NRF_TIMER4->BITMODE = TIMER_BITMODE_BITMODE_32Bit;
  NRF_TIMER4->PRESCALER = 4;  // 16 MHz / 2^4 = 1 MHz
  NRF_TIMER4->CC[0] = (uint32_t)(1000000.0f / ECG_FS);
  NRF_TIMER4->SHORTS = TIMER_SHORTS_COMPARE0_CLEAR_Msk;
  NRF_TIMER4->INTENSET = TIMER_INTENSET_COMPARE0_Msk;
  NVIC_SetPriority(TIMER4_IRQn, 3);  // mức ưu tiên ứng dụng được phép khi có BLE
  NVIC_ClearPendingIRQ(TIMER4_IRQn);
  NVIC_EnableIRQ(TIMER4_IRQn);
  NRF_TIMER4->TASKS_CLEAR = 1;
  NRF_TIMER4->TASKS_START = 1;
  running = true;
}

void stop() {
  NRF_TIMER4->TASKS_STOP = 1;
  NRF_TIMER4->INTENCLR = TIMER_INTENCLR_COMPARE0_Msk;
  NVIC_DisableIRQ(TIMER4_IRQn);
  if (running) {
    uint8_t sd_en = 0;
    sd_softdevice_is_enabled(&sd_en);
    if (sd_en) sd_clock_hfclk_release();
  }
  running = false;
}

int read(uint16_t* values, bool* leadOff, int max_samples) {
  int n = 0;
  while (n < max_samples && tail != head) {
    uint16_t v = buf[tail];
    tail = (tail + 1) & (BUF - 1);
    values[n] = v & 0x0FFF;
    leadOff[n] = (v & LEAD_OFF_BIT) != 0;
    n++;
  }
  return n;
}

bool leadOffNow() { return digitalRead(PIN_ECG_LO_PLUS) || digitalRead(PIN_ECG_LO_MINUS); }

uint32_t dropped() { return lost; }

}  // namespace Ad8232
