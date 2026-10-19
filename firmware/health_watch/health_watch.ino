// =============================================================================
//  health_watch.ino — Thiết bị đeo tay giám sát sức khỏe người cao tuổi
//  Board : Seeed XIAO nRF52840 Sense  (gói "Seeed nRF52 Boards", không phải mbed)
//
//  Chức năng:
//   - Nhịp tim liên tục (PPG xanh, MAX30101)             -> gói VITALS mỗi 10 s
//   - SpO2 định kỳ khi đứng yên (PPG đỏ + IR)             -> trong gói VITALS
//   - Nhiệt độ da liên tục (TMP117)                       -> trong gói VITALS
//   - Té ngã (IMU: va chạm + bất động 30 s), nút SOS 3 s  -> gói EVENT (indicate)
//   - ECG 1 chuyển đạo 30 s theo yêu cầu + PAT cho huyết áp (AD8232 + PPG)
//     -> luồng ECG_DATA + gói ECG_RESULT. KHÔNG đo khi đang cắm sạc.
//  Đồng hồ chỉ gửi dữ liệu; quyết định cảnh báo nằm ở server.
//
//  Lệnh qua cổng USB (Serial Monitor 115200, kết thúc bằng Enter):
//    help | status | ecg | spo2 | raw on | raw off | sos | time <epoch>
// =============================================================================
#include "app.h"

// Logic nằm trong app.cpp để không phụ thuộc vào việc Arduino IDE tự sinh prototype.
void setup() { app_setup(); }

void loop() { app_loop(); }
