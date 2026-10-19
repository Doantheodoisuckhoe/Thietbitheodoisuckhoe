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
| `app/` | App Flutter cho người đeo (kết nối đồng hồ qua BLE) và người nhà | SV2 |
| `server/` | Backend FastAPI, cơ sở dữ liệu, bộ xử lý cảnh báo, gửi push/SMS; web dashboard trong `server/web_dashboard/` | SV2 |
| `hardware/pcb/` | File KiCad: sơ đồ nguyên lý, layout, Gerber, BOM, CPL | SV1 |
| `hardware/enclosure/` | File thiết kế vỏ (Fusion 360, STL) | SV1 |
| `data/` | Dữ liệu đo thô (CSV) và kết quả kiểm chứng | Chung |
| `docs/` | Tài liệu, hình ảnh cho báo cáo | Chung |

Cách chạy từng phần của code hệ thống (firmware chính `firmware/health_watch`, thuật toán, server,
dashboard, app) và kết quả đã kiểm tra: [`docs/huong-dan-code.md`](docs/huong-dan-code.md).

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
2. Boards Manager → cài **Seeed nRF52 Boards** (1.1.13) → chọn board **Seeed XIAO nRF52840 Sense**.
3. Library Manager → cài: SparkFun MAX3010x Pulse and Proximity Sensor Library, OneWire,
   DallasTemperature, Adafruit GC9A01A (chọn *Install all* để cài kèm Adafruit GFX, BusIO), Seeed Arduino LSM6DS3.
4. Mở `firmware/kiem_tra_thu_vien` và bấm Verify để kiểm tra. Phiên bản đã kiểm chứng và các lỗi
   thường gặp: [`firmware/README.md`](firmware/README.md).

**Vỏ thiết bị:** Onshape (gói Education, đăng ký bằng email sinh viên), xuất STL vào `hardware/enclosure/`.

**Thuật toán (Python 3.10+)**
```
pip install -r algorithm/requirements.txt
cd algorithm
python -m pytest -q
```

## Mốc tiến độ

| Mốc | Hạn | Tiêu chí |
|---|---|---|
| M1 | 11/10/2026 | Đề cương được duyệt, linh kiện đã đặt |
| M2 | 01/11/2026 | Breadboard đo đủ chỉ số qua BLE; đã đặt mạch JLCPCB |
| M3 | 22/11/2026 | Thiết bị đeo tay chạy đầu-cuối ổn định 24 giờ |
| M4 | 06/12/2026 | Bản thảo báo cáo đầy đủ gửi GVHD |

## Tài liệu và công cụ của nhóm

| Ở đâu | Có gì |
|---|---|
| [`docs/nhat-ky.md`](docs/nhat-ky.md) | Nhật ký thực hiện và các quyết định theo ngày |
| [`docs/mua-sam/`](docs/mua-sam/) | Danh sách mua linh kiện, máy đo đối chứng, ngân sách |
| [`docs/huong-dan-code.md`](docs/huong-dan-code.md) | Hướng dẫn chạy firmware, thuật toán, server, dashboard, app |
| [`docs/ble_protocol.md`](docs/ble_protocol.md) | Giao thức BLE giữa đồng hồ và app |
| Trello: bảng *Đồ án – Thiết bị đeo tay giám sát sức khỏe* | Việc từng tuần, mốc; báo cáo tiến độ tự động tối Chủ Nhật |
| Google Drive: thư mục *Đồ án tốt nghiệp – Thiết bị đeo tay giám sát sức khỏe* | Datasheet, dữ liệu đo dài, báo cáo, ảnh/video, file phát hành mạch và vỏ, giấy tờ |

## Làm việc với Git trên máy

Thư mục làm việc trên máy SV1: `C:\DoAnTotNghiep` (bản clone của repo này).

1. Trước khi làm: mở Git Bash trong thư mục đó, chạy `git pull` để lấy thay đổi mới nhất.
2. Sau khi làm xong một việc nhỏ:
   ```
   git add .
   git commit -m "firmware: mô tả ngắn việc vừa làm"
   git push
   ```
3. Lần đầu `git push`, Windows sẽ mở cửa sổ đăng nhập GitHub — đăng nhập một lần là xong.

## Quy ước làm việc

- Mỗi người làm trên nhánh riêng (`sv1/...`, `sv2/...`), gộp vào `main` khi chạy được.
- Commit nhỏ, mô tả rõ bằng tiếng Việt, ví dụ: `firmware: đọc FIFO MAX30102 ở 100 Hz`.
- Không đẩy file lớn hơn 50 MB; dữ liệu đo dài lưu trên Drive, chỉ để mẫu nhỏ trong `data/`.
