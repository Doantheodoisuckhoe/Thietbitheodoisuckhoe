# Giao thức BLE đồng hồ ↔ điện thoại

Nguồn chuẩn: `firmware/health_watch/protocol.h`. Phía app: `app/lib/ble/protocol.dart`.
Mọi số nhiều byte là **little-endian**. Đồng hồ quảng bá tên `HealthWatch-XXXX`.

## Dịch vụ và đặc tính

| UUID | Tên | Thuộc tính | Nội dung |
|---|---|---|---|
| `a7e10000-4b2c-4d8e-9f10-5c3e2a1b0d47` | Service | | |
| `a7e10001-…` | VITALS | read, notify | `VitalsPacket` 20 B, mỗi 10 s |
| `a7e10002-…` | EVENT | read, **indicate** | `EventPacket` 16 B — đồng hồ giữ lại cho đến khi điện thoại xác nhận |
| `a7e10003-…` | ECG_DATA | notify | header 6 B + tối đa 100 mẫu int16 |
| `a7e10004-…` | ECG_RESULT | read, notify | `EcgResultPacket` 24 B |
| `a7e10005-…` | CONTROL | write | lệnh từ điện thoại |
| `0x180F` | Battery Service | | % pin |

## Cờ (flags)

| bit | Ý nghĩa |
|---|---|
| 0x01 | đang đeo (PPG có tiếp xúc da) |
| 0x02 | đang cắm sạc |
| 0x04 | đứng yên ≥ 10 s |
| 0x08 | `timestamp` là Unix epoch (đã đồng bộ giờ). Nếu 0: số giây từ lúc bật máy |
| 0x10 | pin yếu |

## VitalsPacket (20 byte)

| Offset | Kiểu | Trường | Ghi chú |
|---|---|---|---|
| 0 | u8 | version | = 1 |
| 1 | u8 | flags | |
| 2 | u16 | seq | |
| 4 | u32 | timestamp | |
| 8 | u8 | hr_bpm | 0 = không có |
| 9 | u8 | hr_quality | 0–100 |
| 10 | u8 | spo2 | 0 = không có lần đo mới trong chu kỳ |
| 11 | u8 | spo2_quality | |
| 12 | i16 | skin_temp | °C × 100, −32768 = không có |
| 14 | u16 | activity | số mẫu IMU có chuyển động trong chu kỳ (104 mẫu/s) |
| 16 | u8 | battery_pct | |
| 17 | u8 | interval_s | |
| 18 | u16 | battery_mv | |

## EventPacket (16 byte)

| Offset | Kiểu | Trường |
|---|---|---|
| 0 | u8 | version |
| 1 | u8 | type: 1 FALL, 2 SOS, 3 FALL_CANCELLED, 4 LOW_BATTERY, 5 IMPACT |
| 2 | u16 | seq |
| 4 | u32 | timestamp |
| 8 | i16 | value1 — FALL/IMPACT: gia tốc đỉnh (g × 100); LOW_BATTERY: % |
| 10 | i16 | value2 — FALL: góc đổi tư thế (độ) |
| 12 | u16 | value3 — bit0: có rơi tự do trước va chạm |
| 14 | u8 | flags |
| 15 | u8 | — |

## ECG_DATA

`[session u8][flags u8 (bit0 lead-off)][seq u16][count u8][—]` + `count` × int16 = giá trị ADC 12 bit của AD8232 − 2048 (250 mẫu/s).

## EcgResultPacket (24 byte)

| Offset | Kiểu | Trường |
|---|---|---|
| 0 | u8 | version |
| 1 | u8 | status: 0 OK, 1 LEAD_OFF, 2 CHARGING (từ chối), 3 LOW_QUALITY, 4 ABORTED, 5 SENSOR_ERROR, 6 BUSY, 7 STARTED |
| 2 | u8 | session |
| 3 | u8 | n_beats |
| 4 | u32 | timestamp |
| 8 | u8 | hr_bpm |
| 9 | u8 | quality |
| 10 | u16 | pat_ms × 10 (0 = không có) |
| 12 | u16 | pat_iqr × 10 |
| 14 | u8 | n_pat |
| 15 | u8 | flags |
| 16 | u16 | fs_hz |
| 18 | u16 | n_samples |
| 20 | u16 | rr_ms |
| 22 | u16 | — |

## Lệnh CONTROL

| Byte 0 | Tham số | Ý nghĩa |
|---|---|---|
| 0x01 | [giây u8] | bắt đầu đo ECG (mặc định 30 s) |
| 0x02 | | dừng ECG |
| 0x03 | | đo SpO2 ngay |
| 0x10 | [epoch u32] | đồng bộ giờ — app gửi ngay sau khi kết nối |
| 0x20 | [giây u8] | chu kỳ gửi VITALS |
| 0x21 | [impact_g×10 u8][still_s u8] | tham số té ngã |
| 0x30 | [ms u16] | rung |
| 0x31 | | người nhà đã xác nhận cảnh báo → rung nhẹ 2 lần |

## Trình tự kết nối

1. App quét theo tên/UUID dịch vụ → kết nối → xin MTU 247–512.
2. Đăng ký nhận notify/indicate cho VITALS, EVENT, ECG_DATA, ECG_RESULT.
3. Ghi `0x10 + epoch` để đồng bộ giờ. Đồng hồ chờ tối đa 3 s cho lệnh này rồi mới xả hàng đợi.
4. Đồng hồ gửi các gói tồn đọng (tối đa 2 giờ VITALS, 16 EVENT), sau đó gửi theo thời gian thực.
