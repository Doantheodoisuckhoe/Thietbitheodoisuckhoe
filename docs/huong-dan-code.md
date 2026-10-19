# Hướng dẫn code hệ thống

Code đầy đủ cho thiết bị và hệ thống: firmware đồng hồ, thuật toán Python, server + bộ xử lý cảnh báo,
web dashboard và app Flutter. Đồng hồ chỉ gửi dữ liệu; **quyết định cảnh báo nằm ở server**.

```
 Đồng hồ (XIAO nRF52840 Sense)        Điện thoại người cao tuổi        Server (FastAPI + PostgreSQL)
 ┌──────────────────────────┐  BLE   ┌──────────────────────┐ HTTP  ┌──────────────────────────────┐
 │ MAX30101  PPG (HR, SpO2) │◄──────►│ App Flutter (gateway)│──────►│ Lưu dữ liệu                  │
 │ AD8232    ECG            │        │ - nhận gói BLE       │       │ Bộ xử lý cảnh báo (ngưỡng    │
 │ TMP117    nhiệt độ da    │        │ - hàng đợi offline   │       │   theo từng người)           │
 │ LSM6DS3   té ngã         │        │ - đo ECG, vẽ sóng    │       │ Push (FCM) → leo thang SMS   │
 │ Nút SOS, motor rung      │        └──────────────────────┘       │ Web dashboard (/dashboard)   │
 └──────────────────────────┘                                       └──────────┬───────────────────┘
                                                    App Flutter (người nhà) ◄──┘ push / SMS
```

| Thư mục | Nội dung |
|---|---|
| `firmware/health_watch/` | Firmware chính (Arduino) cho XIAO nRF52840 Sense theo sơ đồ `hardware/pcb` v0.1 |
| `firmware/tests/` | Chạy thuật toán C của firmware trên máy tính, so khớp với bản Python |
| `algorithm/hwalgo/` | Thuật toán Python tham chiếu (nhịp tim, SpO2, Pan-Tompkins, PAT, huyết áp, té ngã) |
| `algorithm/scripts/` | Đánh giá trên MIT-BIH, BIDMC, dữ liệu té ngã; Bland–Altman; ghi/chạy lại dữ liệu thô |
| `algorithm/tests/` | 33 kiểm thử tự động |
| `server/` | API FastAPI, bộ xử lý cảnh báo, push/SMS, giả lập thiết bị; `server/web_dashboard/` là web dashboard |
| `app/` | App Flutter: chế độ “Kết nối đồng hồ” (gateway) và “Người nhà” |
| `docs/ble_protocol.md` | Giao thức BLE — hợp đồng giữa firmware và app |

---

## 1. Chạy thử nhanh không cần phần cứng

```bash
cd server
python -m venv .venv && .venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

1. Mở http://localhost:8000/dashboard → **Đăng ký** (tài khoản đầu tiên là quản trị).
2. **+ Thêm người** → tab **Cài đặt** → **Đăng ký thiết bị** → chép API key (chỉ hiện 1 lần).
3. Mở cửa sổ dòng lệnh thứ hai (vẫn trong `server/`, đã kích hoạt `.venv`) để giả lập đồng hồ:
   ```bash
   python scripts/simulate_device.py --key <API_KEY> --backfill 24     # đổ 24 giờ dữ liệu
   python scripts/simulate_device.py --key <API_KEY> --scenario ecg
   python scripts/simulate_device.py --key <API_KEY> --scenario fall   # cảnh báo nguy hiểm
   python scripts/simulate_device.py --key <API_KEY> --scenario low_spo2
   ```
4. Xem cảnh báo trên dashboard. Không bấm **Đã nhận** trong 30 giây thì log server in ra tin SMS
   (chế độ `console`).

Tài liệu API tự sinh: http://localhost:8000/docs

**PostgreSQL** (theo đề cương): `copy server\.env.example server\.env` rồi `docker compose up -d --build`
ở thư mục gốc repo. Chạy không dùng Docker thì đặt `DATABASE_URL` trong `server/.env`; để trống thì
server dùng SQLite cho thử nhanh.

## 2. Firmware

Môi trường như `firmware/README.md` (Arduino IDE 2.3.x, gói **Seeed nRF52 Boards** 1.1.13, board
**Seeed XIAO nRF52840 Sense**). Firmware chính **không cần thư viện ngoài**: driver MAX30101, TMP117,
IMU viết sẵn, BLE dùng Bluefruit có trong gói board.

Mở `firmware/health_watch/health_watch.ino` → Upload → Serial Monitor 115200 → gõ `status`.

**Gán chân** (theo `hardware/pcb/README.md`, sửa trong `config.h`):

| Chân | Tín hiệu |
|---|---|
| D0 (A0) | ECG_OUT (AD8232), lấy mẫu 250 Hz bằng TIMER4 như sketch `doc_ad8232` |
| D1 / D3 | ECG_LO+ / ECG_LO- (tuột điện cực) |
| D2 | Motor rung |
| D4 / D5 | I2C: MAX30101 (0x57), TMP117 (0x48) |
| D9 | Nút SOS (INPUT_PULLUP) |
| D6, D7, D8, D10 | Dành cho màn hình GC9A01 — **firmware chưa dùng màn hình** |

**Cách hoạt động**
- Nhịp tim: PPG 50 Hz liên tục. Mặc định dùng LED xanh lá theo đề cương. Mạch v0.1 cấp VLED+ = 3,3 V
  nên đèn xanh có thể yếu; nếu vậy đặt `PPG_HR_USE_IR 1` trong `config.h` hoặc nối JP1 2-3.
- SpO2: đo 30 s bằng đỏ + IR mỗi 15 phút khi đứng yên ≥ 10 s; đo lại sau 2 phút nếu < 94%.
- ECG: 30 s theo lệnh từ app (hoặc gõ `ecg`), ghi đồng thời PPG 200 Hz để tính PAT. Chờ người dùng
  chạm điện cực ổn định 1 s mới bắt đầu ghi. **Từ chối đo khi có điện 5 V (chân pogo/USB)** và dừng ngay
  nếu cắm sạc giữa chừng. Trong lúc đo ECG tạm không đọc pin (ADC đang được ngắt TIMER4 dùng).
- Té ngã: IMU 104 Hz, ±16 g. Va chạm ≥ 2,8 g → đồng hồ rung 3 lần; người dùng **bấm ngắn nút** trong
  30 s để huỷ; bất động đủ 30 s → gửi sự kiện té ngã. Giữ nút 3 s = SOS.
- Mất kết nối điện thoại: giữ tối đa 2 giờ dữ liệu, gửi bù khi kết nối lại.

**Cần đo và chỉnh khi có board:** `PPG_CONTACT_DC_MIN` (nhận biết đang đeo), dòng LED `PPG_*_PA`,
hệ số SpO2 `SPO2_COEF_*` (dùng `algorithm/scripts/fit_spo2_coeffs.py`), ngưỡng va chạm `FALL_IMPACT_G`.

**Lệnh qua USB**: `status`, `ecg`, `spo2`, `sos`, `raw on|off`, `time <epoch>`.
Thu dữ liệu thô rồi chạy lại thuật toán Python trên đó:
```bash
python algorithm/scripts/serial_logger.py --port COM5 --out data/lan_do_01 --command "raw on"
python algorithm/scripts/replay_log.py data/lan_do_01
```

**Kiểm tra bản C khớp bản Python** (cần g++; trên Windows cài MSYS2):
`cd firmware/tests && python run_host_tests.py`

## 3. Thuật toán Python

```bash
cd algorithm
pip install -r requirements.txt
python -m pytest -q                                   # 33 kiểm thử
python scripts/eval_mitbih.py                         # đỉnh R trên MIT-BIH (tải từ PhysioNet)
python scripts/eval_bidmc.py --plot hr.png            # nhịp tim PPG trên BIDMC
python scripts/eval_falls.py ../data/imu --still-s 3  # dữ liệu té ngã của nhóm
```

Chạy lệnh trong thư mục `algorithm/`, không bấm Run/F5 trực tiếp trên file test.
`algorithm/te_nga/` (thuật toán ngưỡng ban đầu của nhóm) giữ nguyên; `hwalgo/fall.py` là bản chạy trong
firmware theo quy tắc “va chạm + bất động 30 s”.

## 4. App Flutter

```bash
cd app
flutter create --platforms=android --org vn.datn.healthwatch .   # sinh thư mục android/
python tool/setup_android.py                                      # quyền Bluetooth, http LAN, minSdk 23
flutter pub get
flutter test
flutter run
```

- **Kết nối đồng hồ** (điện thoại người cao tuổi): nhập địa chỉ server (IP máy tính cùng Wi-Fi, ví dụ
  `http://192.168.1.10:8000`) và API key → **Tìm đồng hồ**. Tự kết nối lại, giữ hàng đợi khi mất mạng,
  có nút **Đo ECG** và **Đo SpO2**. Khi người nhà bấm “Đã nhận”, đồng hồ rung nhẹ trấn an.
- **Người nhà**: đăng nhập tài khoản web → xem cảnh báo, bấm **Đã nhận** để dừng leo thang SMS.

**Push**: tạo project Firebase → `dart pub global activate flutterfire_cli` → `flutterfire configure`
trong `app/`. Server: tải service-account JSON (Firebase Console → Project settings → Service accounts),
đặt đường dẫn vào `FIREBASE_CREDENTIALS` trong `server/.env`. Chưa cấu hình Firebase thì app vẫn chạy
(không có push) và server gửi SMS ngay.

**SMS**: mặc định `SMS_PROVIDER=console` (chỉ in log). Gửi thật: đặt `twilio`, hoặc thêm nhà mạng Việt Nam
(eSMS, SpeedSMS...) bằng một lớp có hàm `send(phone, text)` trong `server/app/notifier.py`.

## 5. Bộ xử lý cảnh báo

Ngưỡng mặc định theo đề cương, **chỉnh được cho từng người** ở tab Cài đặt của dashboard:

| Tình huống | Cảnh báo | Nguy hiểm | Điều kiện “liên tục” |
|---|---|---|---|
| SpO2 | < 94% | < 90% | 2 lần đo liên tiếp |
| Nhịp tim lúc nghỉ | < 50 hoặc > 120 | kèm SpO2 thấp trong 30 phút | ≥ 90% mẫu trong 5 phút, lúc ít vận động |
| Nhiệt độ da | +1 °C so với mức nền cá nhân | — | trung vị 30 phút; mức nền = trung vị 7 ngày |
| Huyết áp tâm thu (ước lượng) | ≥ 140 mỗi ngày trong 3 ngày | ≥ 180 | |
| Té ngã | — | va chạm + bất động 30 s | đồng hồ xác nhận |
| Không cử động ban ngày | 3 giờ không chuyển động | — | cửa sổ nằm trọn trong 7h–21h, đang đeo |
| SOS | — | giữ nút 3 s | |
| Mất kết nối > 30 phút, pin yếu | thông tin | | chỉ push |

Leo thang: push gửi ngay → không ai bấm “Đã nhận” sau 30 s (nguy hiểm) / 5 phút (cảnh báo) thì gửi SMS
theo thứ tự ưu tiên. Không lặp cùng loại trong 30 phút, trừ khi mức độ tăng.

## 6. Kiểm chứng theo mục tiêu đề cương

| Mục tiêu | Công cụ |
|---|---|
| Nhịp tim ≤ 5 lần/phút lúc nghỉ | `eval_bidmc.py`; trên người: `serial_logger.py` + `bland_altman.py` |
| SpO2 Arms ≤ 4% | `fit_spo2_coeffs.py`, `bland_altman.py --arms` |
| Nhiệt độ 0,1 °C | TMP117 (0,0078 °C); so nhiệt kế bằng `bland_altman.py` |
| ECG ≥ 95% đỉnh R | `eval_mitbih.py` (Se, +P theo ANSI/AAMI EC57, cửa sổ 150 ms) |
| Huyết áp ME ≤ 5, SD ≤ 8 mmHg | hiệu chuẩn trên dashboard, so máy vòng bít: `bland_altman.py --unit mmHg` |
| Té ngã ≥ 90% | `eval_falls.py` (`--sweep` để chọn ngưỡng va chạm) |
| Push < 30 s, SMS < 60 s | `GET /api/alerts/latency-stats`, cột “Độ trễ” tab Cảnh báo |
| Pin ≥ 24 giờ | cột `battery_mv` trong bảng `vital_samples` (mỗi 10 s) |

## 7. Đã kiểm tra / chưa kiểm tra (19/10/2026)

Đã chạy:
- 33 kiểm thử thuật toán; MIT-BIH bản ghi 100 ở 250 Hz: Se 99,96%, +P 100% (bản ghi dễ — cần chạy đủ
  48 bản ghi trên máy có mạng để lấy số liệu báo cáo).
- Dữ liệu té ngã của nhóm (17/10): 6 lần ngã có đỉnh 3,2–12,2 g, đi bộ/ngồi xuống ≤ 1,7 g. Với
  `--still-s 3`: phát hiện 6/6, không báo nhầm 5/5. Chưa kiểm được điều kiện bất động 30 s vì mỗi bản ghi
  chỉ dài 10 s → cần thu bản ghi nằm yên ≥ 35 s sau khi ngã.
- Bản C khớp bản Python trên cả 5 thuật toán (`run_host_tests.py`).
- Firmware biên dịch cho XIAO nRF52840 Sense (gói 1.1.13): 145 KB flash (17%), 123 KB RAM (51%).
- 20 kiểm thử server; chạy đầu-cuối: té ngã/SOS → push ngay → SMS sau ~33 s khi không ai xác nhận.
  Dashboard chạy thử trên Chromium (máy tính + điện thoại).

Chưa kiểm tra:
- **Chưa chạy trên board thật.** Thanh ghi cảm biến theo datasheet; các ngưỡng ở mục 2 cần chỉnh.
- **App Flutter chưa được biên dịch** (môi trường viết code không có Flutter SDK). Đã kiểm tra cú pháp, ghim
  `flutter_blue_plus 1.32.12`; nếu `flutter analyze` báo lỗi API thường chỉ cần sửa nhỏ.
- Màn hình GC9A01 chưa có trong firmware chính.

## 8. Giới hạn nên ghi trong báo cáo

- Huyết áp từ PAT chỉ tham khảo, cần hiệu chuẩn cá nhân và hiệu chuẩn lại định kỳ (2–4 tuần).
- SpO2 phản xạ ở cổ tay khó hơn ngón tay; người khoẻ chỉ có 95–100% nên không kiểm chứng được vùng thấp
  theo đúng ISO 80601-2-61.
- Android có thể dừng app gateway chạy nền lâu; hiện yêu cầu để app mở. Hướng phát triển: foreground service.
- BLE chưa bật ghép đôi mã hoá; khi triển khai thật cần HTTPS và ghép đôi BLE.
