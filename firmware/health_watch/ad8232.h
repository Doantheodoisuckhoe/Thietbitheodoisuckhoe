// ad8232.h — lấy mẫu ECG từ AD8232 (ngõ ra analog) bằng TIMER4.
//
// Cách làm giống sketch firmware/doc_ad8232: ngắt TIMER4 mỗi 4 ms đọc ADC và chân
// tuột điện cực LO+/LO-, cất vào bộ đệm vòng; loop() lấy ra. Lấy mẫu đều nhịp là điều
// kiện để bộ lọc và Pan-Tompkins đúng. Trong lúc đo, firmware giữ thạch anh 32 MHz chạy
// (sd_clock_hfclk_request) để nhịp timer chính xác, và KHÔNG gọi analogRead ở nơi khác
// (đọc pin bị tạm dừng) vì ADC không dùng chung được giữa ngắt và loop().
#pragma once
#include <Arduino.h>

namespace Ad8232 {
void begin();           // cấu hình chân
void start();           // xoá bộ đệm, bật timer lấy mẫu ECG_FS
void stop();            // tắt timer, trả thạch anh
// Lấy các mẫu đã có: values 0..4095 (ADC 12 bit), leadOff = điện cực tuột lúc lấy mẫu.
int read(uint16_t* values, bool* leadOff, int max_samples);
bool leadOffNow();      // đọc trực tiếp LO+/LO-
uint32_t dropped();     // số mẫu mất do loop() lấy không kịp
}  // namespace Ad8232
