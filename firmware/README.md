# Firmware – XIAO nRF52840 Sense

Code Arduino cho đồng hồ. Mỗi thư mục con là một sketch mở được bằng Arduino IDE.

| Sketch | Mục đích | Trạng thái |
|---|---|---|
| `kiem_tra_chan/` | Sau khi hàn header vào XIAO: tìm chân D0-D10 bị chập GND, chập 3V3 hoặc dính nhau (rút hết dây trước khi chạy) | Biên dịch được (21/10/2026), chưa chạy trên board |
| `test_breadboard/` | **Bắt đầu từ đây khi cắm breadboard.** Test cùng lúc MAX30102, MAX30205, AD8232, IMU, nút SOS theo đúng chân mạch in `hardware/pcb_module`; có sơ đồ cắm dây trong README của thư mục | Biên dịch được (21/10/2026), chưa chạy trên board |
| `kiem_tra_thu_vien/` | Kiểm tra đã cài đủ thư viện; khi cắm cảm biến thì báo MAX30102, DS18B20, IMU có được nhận không | Biên dịch được (05/10/2026), chưa chạy trên board |
| `doc_max30102/` | Đọc MAX30102 ở 100 mẫu/giây, in CSV `t_ms,red,ir` ra Serial cho SV2 phân tích | Biên dịch được (11/10/2026), chưa chạy trên board |
| `doc_ad8232/` | Lấy mẫu ECG từ AD8232 ở 250 mẫu/giây bằng timer phần cứng (TIMER4), in CSV `t_ms,ecg,tuot_dien_cuc` | Biên dịch được (11/10/2026), chưa chạy trên board |
| `ble_suc_khoe/` | **Firmware chính để nối với app.** Gửi nhịp tim, SpO2, nhiệt độ, pin qua BLE mỗi giây; cảnh báo SOS (giữ nút 1 giây), té ngã (rung 15 giây, bấm nút để hủy), chỉ số bất thường; app xác nhận thì rung dài. Màn tròn GC9A01 (28/10): chỉ số, đếm ngược té ngã, SOS, cảnh báo; tắt sau 10 giây, bấm nhanh nút để bật; ảnh mô phỏng trong `ble_suc_khoe/xem_truoc/`. ECG 30 giây (28/10): app gửi lệnh `03`, đồng hồ lấy mẫu AD8232 250 mẫu/giây (A0, tuột điện cực D1) và gửi qua đặc tính ECG. Xem giờ (30/10): app gửi giờ điện thoại mỗi lần kết nối (lệnh `05`), màn chính hiện HH:MM trên cùng, chưa có giờ thì `--:--`. Giao thức: `docs/giao-thuc-ble.md` | Biên dịch được (28/10/2026, có màn hình: Flash 21 %, RAM 9 %); biên dịch 30/10 (có xem giờ: Flash 21 %, RAM 10 %); phần màn hình chưa thử với màn thật |
| `ble_nhip_tim/` | Tính nhịp tim từ MAX30102, gửi lên điện thoại qua BLE Heart Rate Service mỗi giây; thử bằng app nRF Connect | Biên dịch được (11/10/2026), chưa chạy trên board |
| `ghi_imu/` | Ghi gia tốc và con quay của IMU trên board ở 100 mẫu/giây, in CSV `t_ms,ax,ay,az,gx,gy,gz` để thu dữ liệu té ngã (xem `algorithm/te_nga/README.md`) | Biên dịch được (17/10/2026), chưa chạy trên board |

## Môi trường đã kiểm chứng (máy SV1, 05/10/2026)

| Thành phần | Phiên bản |
|---|---|
| Arduino IDE | 2.3.10 |
| Gói board **Seeed nRF52 Boards** (dùng gói này, không dùng gói mbed) | 1.1.13 |
| Board | Seeed XIAO nRF52840 Sense |
| SparkFun MAX3010x Pulse and Proximity Sensor Library | 1.1.2 |
| OneWire | 2.3.8 |
| DallasTemperature | 4.0.6 |
| Adafruit GC9A01A | 1.1.1 |
| Adafruit GFX Library | 1.12.6 |
| Adafruit BusIO | 1.17.4 |
| Seeed Arduino LSM6DS3 | 2.0.7 |

Chọn gói **Seeed nRF52 Boards** thay vì *Seeed nRF52 mbed-enabled Boards* vì gói này có thư viện
Bluefruit cho BLE và chế độ ngủ tiết kiệm pin tốt hơn.

## Chạy sketch kiểm tra

1. Mở `kiem_tra_thu_vien/kiem_tra_thu_vien.ino`.
2. Tools → Board → Seeed nRF52 Boards → **Seeed XIAO nRF52840 Sense**; Tools → Port → cổng COM của board.
3. Upload, mở Serial Monitor ở **115200**.
4. Kết quả mong đợi khi đã nối dây:
   ```
   Kiem tra thu vien
   MAX30102: OK
   DS18B20 tim thay: 1
   IMU: OK
   Gia toc Z (g): 1.0xx      <- board nằm phẳng
   ```

Chân trên breadboard và mạch in (xem sơ đồ trong `test_breadboard/README.md`):

| Linh kiện | Chân XIAO |
|---|---|
| MAX30102 (0x57), MAX30205 (0x48) | SDA → D4, SCL → D5. IMU trên XIAO nằm ở bus I2C riêng bên trong, không chung D4/D5 |
| AD8232 | OUTPUT → A0 (D0), LO+ → D1, LO- → D3 (breadboard). Mạch in: LO+ và LO- gộp vào D1 qua 2 diode |
| Nút SOS | D9 → GND (INPUT_PULLUP) |
| Động cơ rung | D2 qua MOSFET AO3400A, không nối thẳng |
| Màn hình GC9A01 | CS → D7, DC → D6, SCL → D8, SDA → D10, BLK → D3 (mạch in), RST không dùng (-1) |

`kiem_tra_thu_vien` còn dùng DS18B20 ở D2 theo phương án cũ; phương án cuối đã bỏ DS18B20.

## Lưu dữ liệu CSV để phân tích

Sketch `doc_max30102` và `doc_ad8232` in mỗi mẫu thành một dòng CSV. Để lưu thành file: đóng Serial Monitor
của Arduino IDE (chỉ một chương trình được mở cổng COM), rồi dùng một chương trình đọc cổng nối tiếp ghi ra file,
ví dụ script Python với thư viện `pyserial`. Dòng bắt đầu bằng `#` là thông báo, không phải dữ liệu.

Đo ECG chỉ khi XIAO chạy pin hoặc cắm laptop đang **rút sạc**, không đo khi laptop cắm điện lưới.

## Lỗi đã gặp và cách xử lý

- **Arduino IDE không hiện board Seeed / menu trống:** IDE trên máy SV1 mất khoảng 1 phút mới tải xong
  danh sách board. Chờ thanh trạng thái phía dưới chạy xong rồi mới mở Boards Manager hoặc menu Board.
- **`Adafruit GFX Library has multiple installations`** khi cài GC9A01A: trong
  `Documents\Arduino\libraries` có nhiều bản GFX cũ. Dời các bản cũ ra ngoài thư mục `libraries`
  (trên máy SV1 đã dời sang `Documents\Arduino\_thu_vien_cu_backup`), rồi cài lại GC9A01A và chọn **Install all**.
- **Cảnh báo `OneWire. Fallback mode` khi biên dịch:** OneWire chưa có code tối ưu riêng cho nRF52 nên dùng
  `digitalRead/digitalWrite`. Chỉ là cảnh báo; DS18B20 vẫn chạy. Bản mạch thật dùng MAX30205 qua I2C nên
  không còn phụ thuộc OneWire.
- **MAX30102 không trả lời I2C:** nhiều module giá rẻ (mạch tím) có điện trở kéo lên I2C nối vào 1,8 V,
  thấp hơn mức logic cao của XIAO (3,3 V). Nếu gặp, chuyển điện trở kéo lên sang 3,3 V (cắt/hàn lại jumper
  trên module) hoặc thêm điện trở 4,7 kΩ lên 3,3 V cho SDA và SCL.
