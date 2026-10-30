# App Android "Sức khỏe"

App Flutter chạy trên điện thoại của người đeo đồng hồ. Nhận số đo qua BLE và khi đồng hồ báo cảnh báo
thì tự gửi SMS kèm vị trí GPS cho người thân (phương án 1). Giao thức: [`docs/giao-thuc-ble.md`](../../docs/giao-thuc-ble.md).

## Cài lên điện thoại (không cần cài Flutter)

1. Trên GitHub, mở tab **Actions** → **Build app Android** → lần chạy mới nhất có dấu ✓ xanh.
2. Kéo xuống mục **Artifacts**, tải `app-suc-khoe-apk` (file zip), giải nén ra `app-release.apk`.
3. Chép file APK vào điện thoại Android rồi mở nó. Nếu máy hỏi, cho phép "cài ứng dụng không rõ nguồn gốc".
   Google Play Protect có thể cảnh báo vì app gửi SMS và không lấy từ Play: chọn **Vẫn cài đặt**.
4. Mở app, **cho phép tất cả quyền** (Bluetooth, vị trí, SMS, gọi điện, thông báo) và cho phép
   "không tối ưu hóa pin" để app không bị tắt khi chạy nền.

## Dùng app

- **Số đo**: trạng thái kết nối, nhịp tim, SpO2, nhiệt độ da, pin đồng hồ. App tự tìm đồng hồ tên
  `DoAn-SucKhoe`, nhớ nó và tự kết nối lại khi đồng hồ vào lại tầm. Nút "Tìm đồng hồ" làm đồng hồ rung.
- **Đồng bộ giờ:** mỗi lần kết nối, app gửi giờ điện thoại xuống để màn đồng hồ hiện giờ.
- **Đo điện tim (ECG) 30 giây** (nút ở trang Số đo): bấm Đo, đồng hồ gửi sóng AD8232 250 mẫu/giây; app vẽ sóng
  chạy 5 giây gần nhất, báo khi tuột điện cực, xong thì tính nhịp tim (trung bình, thấp nhất, cao nhất) và vẽ
  6 dải sóng 5 giây trên nền giấy ECG có đánh dấu đỉnh R. App lưu 10 lần đo gần nhất trên điện thoại.
  Nếu đã đăng nhập ở tab Web, mỗi lần đo còn được tải lên Firebase để người thân, bác sĩ xem trên web.
  Cần nạp firmware `ble_suc_khoe` từ 28/10/2026 trở đi.
- **Người thân**: nhập tên người đeo (ghi trong SMS) và số điện thoại người thân. Thêm số xong, bấm
  "Gửi thử SMS" ở trang Số đo để kiểm tra.
- **Lịch sử**: các cảnh báo đã nhận, đã gửi SMS cho bao nhiêu người.
- **Web**: đăng nhập Firebase để gửi số đo và cảnh báo lên web cho người thân xem. Cách tạo Firebase: [`web/README.md`](../../web/README.md).

Khi có cảnh báo, app: lấy vị trí → gửi SMS cho từng người thân → báo đồng hồ "đã gửi" (đồng hồ rung dài 1 giây)
→ hiện màn hình cảnh báo có nút gọi. Với SOS và té ngã, app gọi luôn người thân đầu tiên nếu app đang mở trên
màn hình (Android không cho app chạy nền tự mở cuộc gọi). Gửi SMS thất bại thì không báo đồng hồ, đồng hồ gửi lại
sau 5 giây và app thử lại.

Ví dụ SMS: `[Dong ho suc khoe] Ba Nguyen Thi Hang: TE NGA luc 14:32 21/10. Vi tri: https://maps.google.com/?q=21.02850,105.85420`

## Giới hạn (ghi vào báo cáo)

- Điện thoại phải ở gần đồng hồ (~10 m) và app phải đang chạy (có thông báo "Đang theo dõi đồng hồ").
- Một số máy (Xiaomi, Oppo, Vivo...) tự tắt app chạy nền: vào Cài đặt → Pin → cho app "Không giới hạn",
  và bật "Tự khởi động".
- Gửi SMS tốn tiền theo gói của SIM. Máy không có SIM thì không gửi được.

## Sửa code

Cần Flutter 3.47.6 và Android Studio (để có Android SDK).

```
cd app/suc_khoe
flutter pub get
flutter test          # 43 test: đọc gói BLE, xử lý cảnh báo, Firebase, ECG
flutter run           # cắm điện thoại bật USB debugging
```

| File | Nội dung |
|---|---|
| `lib/giao_thuc.dart` | UUID, đọc gói Số đo / Cảnh báo, tạo nội dung SMS không dấu |
| `lib/xu_ly_canh_bao.dart` | Bỏ gói gửi lại, gửi SMS cho từng người, gửi xác nhận về đồng hồ |
| `lib/dong_ho.dart` | Tìm, kết nối, tự kết nối lại, nhận dữ liệu BLE (flutter_blue_plus) |
| `lib/dich_vu_dien_thoai.dart` | Gửi SMS, gọi điện, GPS, xin quyền |
| `lib/dam_may.dart` | Gửi số đo (10 giây/lần, lịch sử 1 phút/lần) và cảnh báo lên Firebase qua REST |
| `lib/luu_tru.dart` | Lưu danh bạ, tên người đeo, lịch sử, các lần đo ECG trên điện thoại |
| `lib/ecg.dart` | Lọc sóng ECG, tìm đỉnh R, tính nhịp tim (bản Python: `algorithm/ecg/phan_tich_ecg.py`) |
| `lib/do_ecg.dart` | Một lần đo ECG: gửi lệnh, gom gói, bù gói mất, phân tích, lưu |
| `lib/man_hinh_ecg.dart` | Màn hình ECG: hướng dẫn, sóng chạy, kết quả, dải sóng trên giấy ECG |
| `lib/main.dart` | Giao diện 4 trang + màn hình cảnh báo, chạy nền (flutter_foreground_task) |
| `android/app/src/main/kotlin/.../MainActivity.kt` | Code Android gửi SMS (SmsManager) và gọi điện |

Thư viện BLE `flutter_blue_plus` miễn phí cho cá nhân và trường học (`License.nonprofit` trong code);
dùng thương mại phải mua giấy phép.
