# Giao thức BLE giữa đồng hồ và app

Tài liệu cho người làm app (SV2). Firmware tương ứng: `firmware/ble_suc_khoe/ble_suc_khoe.ino`.

## Cách hệ thống gửi cảnh báo (phương án 1, chốt 21/10/2026)

```
Đồng hồ (XIAO nRF52840) --BLE--> App Android trên điện thoại người già --SMS / gọi--> Người thân
                                          \--(sau M2) Firebase --> Web cho người thân xem
```

Đồng hồ chỉ có Bluetooth, không có SIM. App là thứ gửi SMS, nên:
- App phải chạy nền liên tục (Android: *foreground service* có thông báo cố định) và tự kết nối lại khi mất kết nối.
- Điện thoại phải ở trong khoảng ~10 m. Ngoài tầm thì cảnh báo nằm chờ trên đồng hồ, kết nối lại là được gửi
  (đồng hồ gửi lại mỗi 5 giây đến khi app xác nhận). Ghi giới hạn này vào báo cáo.

## Tìm và kết nối

- Tên quảng bá: `DoAn-SucKhoe`.
- Gói quảng bá chứa UUID service riêng `4b3a0001-8f6e-4c2a-9d1b-3e5f7a9c0b1d`: lọc khi quét theo UUID này.
- Không cần ghép đôi (pairing), không có mã PIN.

## Các service và đặc tính

| Service | Đặc tính | UUID | Thuộc tính | Nội dung |
|---|---|---|---|---|
| Riêng `4b3a0001-…` | **Số đo** | `4b3a0002-8f6e-4c2a-9d1b-3e5f7a9c0b1d` | Read, Notify | 10 byte, mỗi giây 1 lần |
| | **Cảnh báo** | `4b3a0003-8f6e-4c2a-9d1b-3e5f7a9c0b1d` | Read, Notify | 4 byte, khi có cảnh báo (gửi lại mỗi 5 giây đến khi xác nhận) |
| | **Lệnh** | `4b3a0004-8f6e-4c2a-9d1b-3e5f7a9c0b1d` | Write, Write without response | 1–2 byte, app gửi xuống |
| Heart Rate chuẩn `0x180D` | Heart Rate Measurement `0x2A37` | | Notify | nhịp tim, để thử bằng nRF Connect |
| Battery chuẩn `0x180F` | Battery Level `0x2A19` | | Read, Notify | % pin |
| Device Information `0x180A` | | | Read | tên hãng, model |

Mọi số nhiều byte đều **little endian** (byte thấp trước).

### Số đo (10 byte)

| Byte | Kiểu | Tên | Ý nghĩa |
|---|---|---|---|
| 0 | uint8 | phiên bản | luôn `1`; đổi định dạng thì tăng số này |
| 1 | uint8 | cờ | bit0 = đang đeo (cảm biến chạm da), bit1 = nhiệt độ hợp lệ, bit2 = SpO2 hợp lệ, bit3 = IMU hoạt động |
| 2 | uint8 | nhịp tim | lần/phút, `0` = chưa có |
| 3 | uint8 | SpO2 | %, `0` = chưa có |
| 4–5 | int16 | nhiệt độ | đơn vị 0,01 °C (`3650` = 36,50 °C) |
| 6–7 | uint16 | pin | mV |
| 8 | uint8 | pin | % (ước lượng 3,3 V = 0 %, 4,2 V = 100 %) |
| 9 | uint8 | cảnh báo đang chờ | số thứ tự cảnh báo chưa được app xác nhận, `0` = không có |

Ví dụ: `01 07 48 61 42 0E 68 10 50 00` → đang đeo, nhiệt độ + SpO2 hợp lệ, nhịp 72, SpO2 97 %,
nhiệt độ 0x0E42 = 3650 → 36,50 °C, pin 0x1068 = 4200 mV, 80 %, không có cảnh báo chờ.

**Lưu ý:** SpO2 đang dùng công thức chung, chưa hiệu chuẩn; nhiệt độ là nhiệt độ da cổ tay (thấp hơn thân nhiệt).
Cả hai sẽ được chỉnh khi đo đối chứng với máy kẹp ngón và nhiệt kế.

### Cảnh báo (4 byte)

| Byte | Kiểu | Tên | Ý nghĩa |
|---|---|---|---|
| 0 | uint8 | mã | xem bảng dưới; `0` = không có cảnh báo |
| 1 | uint8 | số thứ tự | 1–255, tăng mỗi cảnh báo mới. App dùng để không gửi SMS 2 lần cho cùng một cảnh báo |
| 2–3 | uint16 | giá trị | nhịp tim, SpO2 hoặc nhiệt độ (0,01 °C) lúc báo; `0` với SOS và té ngã |

| Mã | Tên | Khi nào đồng hồ báo | Mức |
|---|---|---|---|
| 1 | SOS | Giữ nút SOS 1 giây | Khẩn cấp |
| 2 | Té ngã | IMU phát hiện té ngã, rung 15 giây mà người đeo không bấm nút hủy | Khẩn cấp |
| 3 | Nhịp tim cao | > 120 lần/phút liên tục 15 giây | Chỉ số |
| 4 | Nhịp tim thấp | < 40 lần/phút liên tục 15 giây | Chỉ số |
| 5 | SpO2 thấp | < 90 % liên tục 15 giây | Chỉ số |
| 6 | Sốt | ≥ 38,0 °C liên tục 15 giây | Chỉ số |

Cảnh báo chỉ số cùng loại không báo lại trong 5 phút. Đồng hồ giữ **một** cảnh báo chờ tại một thời điểm;
SOS/té ngã được ghi đè lên cảnh báo chỉ số đang chờ, ngược lại thì không.

### Lệnh (app ghi xuống)

| Byte | Ý nghĩa |
|---|---|
| `01 nn` | Xác nhận đã xử lý cảnh báo số thứ tự `nn` (đã gửi SMS). Đồng hồ ngừng gửi lại và rung dài 1 giây để người đeo biết "đã báo người thân" |
| `02` | Tìm đồng hồ: rung 2 giây |

## Việc app cần làm khi nhận cảnh báo

1. Nếu `số thứ tự` trùng cảnh báo vừa xử lý → bỏ qua (đây là gói gửi lại).
2. Lấy vị trí GPS hiện tại của điện thoại.
3. Gửi SMS cho từng số người thân đã lưu trong app (Android `SmsManager`), ví dụ:
   `[DoAn-SucKhoe] CANH BAO TE NGA luc 14:32 21/10. Vi tri: https://maps.google.com/?q=21.0285,105.8542`
   Viết không dấu để 1 tin SMS chứa được 160 ký tự (có dấu chỉ còn 70).
4. Với SOS/té ngã: gọi điện cho người thân đầu tiên (tùy chọn).
5. Ghi `01 nn` vào đặc tính Lệnh.
6. (Sau M2) đẩy cảnh báo và số đo lên Firebase.

Quyền Android cần: `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`, `SEND_SMS`, `CALL_PHONE`, `ACCESS_FINE_LOCATION`,
`FOREGROUND_SERVICE`, `POST_NOTIFICATIONS`. App có quyền gửi SMS không đưa được lên Google Play nếu không phải
app SMS mặc định, nhưng cài file APK trực tiếp để demo thì không sao.

## Thử khi chưa có app

- **Điện thoại:** app nRF Connect → SCAN → CONNECT `DoAn-SucKhoe` → mở service `4b3a0001-…` → bấm biểu tượng
  3 mũi tên ở Số đo và Cảnh báo để bật notify. Giữ nút SOS (hoặc chạm dây D9 vào GND) 1 giây để thấy cảnh báo.
  Ghi `0101` (kiểu byte array) vào Lệnh để xác nhận cảnh báo số 1.
- **Máy tính có Bluetooth:** `pip install bleak`, rồi `python app/thu_ble_tren_may_tinh.py`. Script in số đo,
  in cảnh báo và tự gửi xác nhận, giống việc app sẽ làm (chỉ thiếu bước gửi SMS).
