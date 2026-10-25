# App điện thoại

App Android nhận dữ liệu từ đồng hồ qua BLE và gửi SMS / gọi cho người thân khi có cảnh báo
(phương án 1, chốt 21/10/2026). Giao thức BLE: [`docs/giao-thuc-ble.md`](../docs/giao-thuc-ble.md).

| File | Mục đích |
|---|---|
| `suc_khoe/` | **App Android (Flutter).** Cách tải APK và cài: `suc_khoe/README.md` |
| `thu_ble_tren_may_tinh.py` | Thử đồng hồ bằng máy tính có Bluetooth khi chưa có app: in số đo, in cảnh báo, tự gửi xác nhận. Cài `pip install bleak` |

Đã có (25/10): kết nối đồng hồ, hiện số đo, danh bạ người thân, gửi SMS kèm GPS khi có cảnh báo, gửi xác nhận về đồng hồ.
Sau M2: đẩy dữ liệu lên Firebase và làm web cho người thân.
