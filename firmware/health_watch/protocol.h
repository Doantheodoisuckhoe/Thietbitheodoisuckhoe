// protocol.h — giao thức BLE giữa đồng hồ và điện thoại.
// App Flutter (app/lib/ble/protocol.dart) phải khớp 100% với file này.
// Tài liệu đầy đủ: docs/ble_protocol.md. Mọi số nhiều byte là little-endian.
#pragma once
#include <stdint.h>

// UUID 128-bit, cơ sở: a7e1xxxx-4b2c-4d8e-9f10-5c3e2a1b0d47
// Bluefruit cần mảng byte theo thứ tự ĐẢO (LSB trước).
#define HW_UUID(x) \
  { 0x47, 0x0d, 0x1b, 0x2a, 0x3e, 0x5c, 0x10, 0x9f, 0x8e, 0x4d, 0x2c, 0x4b, (x) & 0xFF, ((x) >> 8) & 0xFF, 0xe1, 0xa7 }

#define UUID_SERVICE 0x0000     // a7e10000-...
#define UUID_VITALS 0x0001      // notify  : VitalsPacket (20 B)
#define UUID_EVENT 0x0002       // indicate: EventPacket (16 B) — cần xác nhận
#define UUID_ECG_DATA 0x0003    // notify  : EcgDataHeader + int16 mẫu
#define UUID_ECG_RESULT 0x0004  // notify  : EcgResultPacket (24 B)
#define UUID_CONTROL 0x0005     // write   : lệnh từ điện thoại

#define PROTO_VERSION 1

// ---- cờ chung (flags)
#define FLAG_WORN 0x01
#define FLAG_CHARGING 0x02
#define FLAG_STILL 0x04
#define FLAG_TIME_SYNCED 0x08  // timestamp là Unix epoch (giây). Nếu 0: số giây từ lúc bật máy
#define FLAG_LOW_BATTERY 0x10

#define TEMP_NONE INT16_MIN

struct __attribute__((packed)) VitalsPacket {
  uint8_t version;
  uint8_t flags;
  uint16_t seq;
  uint32_t timestamp;
  uint8_t hr_bpm;        // 0 = không có
  uint8_t hr_quality;    // 0..100
  uint8_t spo2;          // 0 = không có lần đo mới trong chu kỳ này
  uint8_t spo2_quality;
  int16_t skin_temp_c100;  // °C x 100, TEMP_NONE = không có
  uint16_t activity;     // số mẫu IMU có chuyển động trong chu kỳ
  uint8_t battery_pct;
  uint8_t interval_s;
  uint16_t battery_mv;
};

enum EventType : uint8_t {
  EV_FALL = 1,            // té ngã đã xác nhận (va chạm + bất động 30 s)
  EV_SOS = 2,             // giữ nút 3 s
  EV_FALL_CANCELLED = 3,  // người dùng bấm nút huỷ trong lúc đếm ngược
  EV_LOW_BATTERY = 4,
  EV_IMPACT = 5,          // phát hiện va chạm, đang đếm ngược 30 s (thông tin)
};

struct __attribute__((packed)) EventPacket {
  uint8_t version;
  uint8_t type;
  uint16_t seq;
  uint32_t timestamp;
  int16_t value1;   // FALL/IMPACT: gia tốc đỉnh (g x 100); LOW_BATTERY: %
  int16_t value2;   // FALL: góc thay đổi tư thế (độ)
  uint16_t value3;  // FALL: bit0 = có rơi tự do trước va chạm
  uint8_t flags;
  uint8_t reserved;
};

#define ECG_FLAG_LEAD_OFF 0x01
struct __attribute__((packed)) EcgDataHeader {
  uint8_t session;
  uint8_t flags;
  uint16_t seq;
  uint8_t count;  // số mẫu int16 theo sau
  uint8_t reserved;
};
#define ECG_SAMPLES_PER_PACKET_MAX 100

enum EcgStatus : uint8_t {
  ECG_ST_OK = 0,
  ECG_ST_LEAD_OFF = 1,
  ECG_ST_CHARGING = 2,   // đang cắm sạc -> từ chối đo (an toàn điện)
  ECG_ST_LOW_QUALITY = 3,
  ECG_ST_ABORTED = 4,
  ECG_ST_SENSOR_ERROR = 5,
  ECG_ST_BUSY = 6,
  ECG_ST_STARTED = 7,    // thông báo đã bắt đầu ghi (chờ đủ thời gian)
};

struct __attribute__((packed)) EcgResultPacket {
  uint8_t version;
  uint8_t status;
  uint8_t session;
  uint8_t n_beats;
  uint32_t timestamp;
  uint8_t hr_bpm;
  uint8_t quality;
  uint16_t pat_ms_x10;  // PAT (ms x 10), 0 = không có
  uint16_t pat_iqr_x10;
  uint8_t n_pat;
  uint8_t flags;
  uint16_t fs_hz;
  uint16_t n_samples;
  uint16_t rr_ms;
  uint16_t reserved;
};

enum ControlCmd : uint8_t {
  CMD_START_ECG = 0x01,     // [thời gian s (tuỳ chọn, u8)]
  CMD_STOP_ECG = 0x02,
  CMD_START_SPO2 = 0x03,
  CMD_SET_TIME = 0x10,      // [epoch u32]
  CMD_SET_INTERVAL = 0x20,  // [giây u8]
  CMD_SET_FALL = 0x21,      // [impact_g x 10 u8][still_s u8]
  CMD_VIBRATE = 0x30,       // [ms u16]
  CMD_ALERT_ACKED = 0x31,   // người nhà đã xác nhận cảnh báo -> rung nhẹ 2 lần trấn an
};

static_assert(sizeof(VitalsPacket) == 20, "VitalsPacket phải 20 byte");
static_assert(sizeof(EventPacket) == 16, "EventPacket phải 16 byte");
static_assert(sizeof(EcgDataHeader) == 6, "EcgDataHeader phải 6 byte");
static_assert(sizeof(EcgResultPacket) == 24, "EcgResultPacket phải 24 byte");
