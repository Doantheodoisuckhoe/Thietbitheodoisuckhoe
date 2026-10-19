// config.h — MỌI thông số phần cứng và ngưỡng của firmware đặt ở đây.
//
// Board: "Seeed XIAO nRF52840 Sense" trong gói "Seeed nRF52 Boards"
// (KHÔNG chọn bản "mbed-enabled" — firmware dùng thư viện Bluefruit).
#pragma once

#define FW_VERSION "1.0.0"
#define DEVICE_NAME_PREFIX "HealthWatch"

// ============================================================================
// CHÂN KẾT NỐI — theo sơ đồ nguyên lý hardware/pcb v0.1 (15/10/2026)
// ============================================================================
//  D0 (A0) : ECG_OUT — ngõ ra analog AD8232
//  D1      : ECG_LO+ — AD8232 báo tuột điện cực (HIGH = tuột)
//  D2      : MOTOR_EN — motor rung qua MOSFET AO3400A (HIGH = rung)
//  D3      : ECG_LO- — AD8232 báo tuột điện cực
//  D4/D5   : I2C SDA/SCL -> MAX30101 (0x57) + TMP117 (0x48)
//  D6/D7/D8/D10 : màn hình GC9A01 (DC/CS/SCK/MOSI) — firmware này CHƯA dùng màn hình
//  D9      : SOS_BTN — nút nối GND, INPUT_PULLUP. Lưu ý D9 cũng là MISO của SPI: khi thêm
//            màn hình, khởi tạo SPI không dùng MISO để không chiếm chân này.
//  IMU LSM6DS3TR-C nằm sẵn trên XIAO Sense (bus I2C nội Wire1)
#define PIN_ECG_OUT A0
#define PIN_ECG_LO_PLUS 1
#define PIN_VIBRATION 2
#define PIN_ECG_LO_MINUS 3
#define PIN_SOS_BUTTON 9

// ---- Pin, sạc
// XIAO nRF52840: VBAT qua cầu chia 1M/510k vào P0.31; P0.14 (VBAT_ENABLE) phải
// kéo LOW để đọc. Gói "Seeed nRF52 Boards" đã định nghĩa sẵn các tên dưới đây.
#ifndef PIN_VBAT
#define PIN_VBAT (32)
#endif
#ifndef VBAT_ENABLE
#define VBAT_ENABLE (14)
#endif
#define VBAT_DIVIDER (1510.0f / 510.0f)
#define LOW_BATTERY_PCT 15

// ============================================================================
// AD8232 (ECG) — lấy mẫu ADC 12 bit bằng TIMER4 (cách làm giống sketch doc_ad8232)
// ============================================================================
#define ECG_FS 250.0f              // mẫu/giây (TIMER4 ngắt mỗi 4 ms)
#define ECG_ADC_MID 2048           // giữa thang ADC 12 bit; gói BLE gửi (giá trị - 2048)
#define ECG_DURATION_S 30          // thời gian đo ECG mặc định
#define ECG_MAX_DURATION_S 30      // giới hạn bộ đệm (RAM)
#define ECG_LEAD_ON_TIMEOUT_S 15   // chờ người dùng đặt ngón tay

// ============================================================================
// MAX30101 (PPG)
// ============================================================================
// LED dùng cho nhịp tim liên tục và PAT: 0 = xanh lá (theo đề cương), 1 = hồng ngoại.
// Mạch v0.1 cấp VLED+ = 3,3 V qua JP1: đèn xanh có thể yếu. Nếu tín hiệu xanh kém,
// đặt 1 (hoặc nối JP1 2-3 lấy thẳng từ pin) — xem hardware/pcb/README.md.
#define PPG_HR_USE_IR 0
#define PPG_HR_FS 50.0f        // liên tục (100 sps, trung bình 2)
#define PPG_SPO2_FS 100.0f     // đỏ + IR khi đo SpO2
#define PPG_PAT_FS 200.0f      // khi đo ECG (tính PAT)
#define PPG_GREEN_PA 0x1F      // dòng LED xanh (0,2 mA/LSB) — chỉnh theo thực tế
#define PPG_RED_PA 0x24
#define PPG_IR_PA 0x24
#define PPG_CONTACT_DC_MIN 30000.0f  // DC xanh tối thiểu khi đeo sát da — PHẢI đo và chỉnh lại

// ============================================================================
// SpO2
// ============================================================================
#define SPO2_DURATION_S 30
#define SPO2_PERIOD_MIN 15         // đo định kỳ mỗi 15 phút ...
#define SPO2_STILL_REQUIRED_S 10   // ... khi đã đứng yên ít nhất 10 s
#define SPO2_RECHECK_MIN 2         // đo lại sớm nếu kết quả thấp/lỗi
#define SPO2_RECHECK_BELOW 94
#define SPO2_MOTION_MAX_ACTIVITY 300  // số mẫu IMU có chuyển động tối đa trong 30 s
// Hệ số đường cong SpO2 = A*R^2 + B*R + C  (fit lại bằng scripts/fit_spo2_coeffs.py)
#define SPO2_COEF_A (-45.060f)
#define SPO2_COEF_B (30.354f)
#define SPO2_COEF_C (94.845f)

// ============================================================================
// IMU / té ngã
// ============================================================================
#define IMU_FS 104.0f
#define FALL_IMPACT_G 2.8f
#define FALL_STILL_S 30.0f
#define SOS_HOLD_MS 3000
#define CANCEL_PRESS_MAX_MS 1000

// ============================================================================
// Gửi dữ liệu
// ============================================================================
#define VITALS_INTERVAL_S 10       // chu kỳ gửi gói chỉ số (đổi được qua BLE)
#define TEMP_READ_INTERVAL_MS 2000
#define BATTERY_READ_INTERVAL_MS 30000
#define VITALS_QUEUE_LEN 720       // 2 giờ dữ liệu khi mất kết nối điện thoại (10 s/gói)
#define EVENT_QUEUE_LEN 16

// ============================================================================
// Gỡ lỗi
// ============================================================================
#define RAW_STREAM_DEFAULT 0   // 1 = in dữ liệu thô qua USB ngay khi khởi động
#define USE_WATCHDOG 0         // bật (1) cho bản demo cuối; tắt khi đang phát triển
