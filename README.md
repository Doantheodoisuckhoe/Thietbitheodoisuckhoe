# Thiết bị đeo tay giám sát sức khỏe người cao tuổi

Đồ án tốt nghiệp ngành Điện tử – Viễn thông.

Thiết bị đeo tay theo dõi nhịp tim, SpO2, nhiệt độ da, ECG 1 chuyển đạo và ước lượng huyết áp (PAT),
phát hiện té ngã, gửi cảnh báo tự động đến người thân qua app, web và SMS.

> Nguyên mẫu nghiên cứu, **không phải thiết bị y tế**, không dùng để chẩn đoán.

## Kiến trúc

```
Đồng hồ (XIAO nRF52840 Sense + MAX30101 + AD8232 + TMP117)
   │ BLE
   ▼
App Android (Flutter) ──Internet──► Server (FastAPI + PostgreSQL)
                                        │ khi vượt ngưỡng
                                        ▼
                         Người nhà, bác sĩ: push, SMS, web dashboard
```

## Cấu trúc thư mục

| Thư mục | Nội dung | Phụ trách |
|---|---|---|
| `firmware/` | Code Arduino/C cho XIAO nRF52840: đọc cảm biến, xử lý tín hiệu, BLE | SV1 |
| `algorithm/` | Thuật toán viết và kiểm thử bằng Python (nhịp tim, SpO2, Pan-Tompkins, PAT, té ngã) | SV2 |
| `app/` | App Flutter cho người đeo và người nhà; web dashboard (Flutter Web) | SV2 |
| `server/` | Backend FastAPI, cơ sở dữ liệu, bộ xử lý cảnh báo, gửi push/SMS | SV2 |
| `hardware/pcb/` | File KiCad: sơ đồ nguyên lý, layout, Gerber, BOM, CPL | SV1 |
| `hardware/enclosure/` | File thiết kế vỏ (Fusion 360, STL) | SV1 |
| `data/` | Dữ liệu đo thô (CSV) và kết quả kiểm chứng | Chung |
| `docs/` | Tài liệu, hình ảnh cho báo cáo | Chung |

## Phần cứng

| Khối | Linh kiện |
|---|---|
| Vi điều khiển + BLE + IMU | Seeed XIAO nRF52840 Sense |
| PPG (nhịp tim, SpO2) | MAX30101 (thử nghiệm: module MAX30102) |
| ECG 1 chuyển đạo | AD8232 |
| Nhiệt độ da | TMP117 (thử nghiệm: DS18B20) |
| Hiển thị, cảnh báo | Màn hình tròn 1,28" GC9A01, motor rung, nút SOS |
| Nguồn | Pin LiPo 200–250 mAh, sạc qua chân pogo |

## Cài đặt môi trường

**Firmware (Arduino IDE)**
1. File → Preferences → Additional boards manager URLs:
   `https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json`
2. Boards Manager → cài **Seeed nRF52 Boards** → chọn board **Seeed XIAO nRF52840 Sense**.
3. Library Manager → cài: SparkFun MAX3010x Pulse and Proximity Sensor Library, OneWire,
   DallasTemperature, Adafruit GC9A01A, Adafruit GFX Library, Seeed Arduino LSM6DS3.

**Thuật toán (Python 3.10+)**
```
pip install numpy scipy matplotlib wfdb pandas
```

## Mốc tiến độ

| Mốc | Hạn | Tiêu chí |
|---|---|---|
| M1 | 11/10/2026 | Đề cương được duyệt, linh kiện đã đặt |
| M2 | 01/11/2026 | Breadboard đo đủ chỉ số qua BLE; đã đặt mạch JLCPCB |
| M3 | 22/11/2026 | Thiết bị đeo tay chạy đầu-cuối ổn định 24 giờ |
| M4 | 06/12/2026 | Bản thảo báo cáo đầy đủ gửi GVHD |

## Quy ước làm việc

- Mỗi người làm trên nhánh riêng (`sv1/...`, `sv2/...`), gộp vào `main` khi chạy được.
- Commit nhỏ, mô tả rõ bằng tiếng Việt, ví dụ: `firmware: đọc FIFO MAX30102 ở 100 Hz`.
- Không đẩy file lớn hơn 50 MB; dữ liệu đo dài lưu trên Drive, chỉ để mẫu nhỏ trong `data/`.
