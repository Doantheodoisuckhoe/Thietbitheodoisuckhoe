// power_ui.h — pin, phát hiện đang sạc, motor rung, nút SOS.
#pragma once
#include <Arduino.h>

namespace Power {
void begin();
uint16_t readBatteryMv();          // trung bình 8 lần đọc ADC
uint8_t percentFromMv(uint16_t mv);  // ước lượng % theo đường xả LiPo
bool usbPowered();                 // có điện áp USB (VBUS) = đang cắm sạc
}  // namespace Power

namespace Vibe {
void begin();
void pulse(uint16_t on_ms);
// Mẫu rung: mảng thời gian [bật, tắt, bật, tắt, ...] ms, kết thúc bằng 0
void pattern(const uint16_t* steps);
void update();  // gọi trong loop()
extern const uint16_t PATTERN_IMPACT[];
extern const uint16_t PATTERN_ALERT_SENT[];
extern const uint16_t PATTERN_ACK[];
extern const uint16_t PATTERN_CANCEL[];
}  // namespace Vibe

namespace Button {
enum Event { NONE, SHORT_PRESS, LONG_HOLD };
void begin();
Event update();  // gọi thường xuyên trong loop()
}  // namespace Button
