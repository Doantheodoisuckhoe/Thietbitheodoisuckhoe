# Firmware – XIAO nRF52840 Sense

Code Arduino cho đồng hồ. Mỗi thư mục con là một sketch mở được bằng Arduino IDE.

| Sketch | Mục đích | Trạng thái |
|---|---|---|
| `kiem_tra_thu_vien/` | Kiểm tra đã cài đủ thư viện; khi cắm cảm biến thì báo MAX30102, DS18B20, IMU có được nhận không | Biên dịch được (05/10/2026), chưa chạy trên board |

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

Chân dùng tạm trong sketch: DS18B20 → D2; màn hình GC9A01: CS → D7, DC → D6; MAX30102 và IMU qua I2C.

## Lỗi đã gặp và cách xử lý

- **Arduino IDE không hiện board Seeed / menu trống:** IDE trên máy SV1 mất khoảng 1 phút mới tải xong
  danh sách board. Chờ thanh trạng thái phía dưới chạy xong rồi mới mở Boards Manager hoặc menu Board.
- **`Adafruit GFX Library has multiple installations`** khi cài GC9A01A: trong
  `Documents\Arduino\libraries` có nhiều bản GFX cũ. Dời các bản cũ ra ngoài thư mục `libraries`
  (trên máy SV1 đã dời sang `Documents\Arduino\_thu_vien_cu_backup`), rồi cài lại GC9A01A và chọn **Install all**.
- **Cảnh báo `OneWire. Fallback mode` khi biên dịch:** OneWire chưa có code tối ưu riêng cho nRF52 nên dùng
  `digitalRead/digitalWrite`. Chỉ là cảnh báo; DS18B20 vẫn chạy. Bản mạch thật dùng TMP117 qua I2C nên
  không còn phụ thuộc OneWire.
- **MAX30102 không trả lời I2C:** nhiều module giá rẻ (mạch tím) có điện trở kéo lên I2C nối vào 1,8 V,
  thấp hơn mức logic cao của XIAO (3,3 V). Nếu gặp, chuyển điện trở kéo lên sang 3,3 V (cắt/hàn lại jumper
  trên module) hoặc thêm điện trở 4,7 kΩ lên 3,3 V cho SDA và SCL.
