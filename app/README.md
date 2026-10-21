# App điện thoại

App Android nhận dữ liệu từ đồng hồ qua BLE và gửi SMS / gọi cho người thân khi có cảnh báo
(phương án 1, chốt 21/10/2026). Giao thức BLE: [`docs/giao-thuc-ble.md`](../docs/giao-thuc-ble.md).

| File | Mục đích |
|---|---|
| `thu_ble_tren_may_tinh.py` | Thử đồng hồ bằng máy tính có Bluetooth khi chưa có app: in số đo, in cảnh báo, tự gửi xác nhận. Cài `pip install bleak` |

Việc cần làm cho M2 (01/11): app kết nối đồng hồ, hiện số đo, lưu danh sách số người thân,
khi có cảnh báo thì gửi SMS kèm vị trí GPS và gửi lệnh xác nhận về đồng hồ.
