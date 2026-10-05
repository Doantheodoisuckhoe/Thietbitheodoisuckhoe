# Mua sắm

File chi tiết, có cột trạng thái để cập nhật: [`Danh_sach_mua_linh_kien_dot_1.xlsx`](Danh_sach_mua_linh_kien_dot_1.xlsx).
Bảng dưới là bản đọc nhanh. Giá kiểm tra trên trang của từng shop ngày 05/10/2026.

## Đợt 1 – Linh kiện thử nghiệm và máy đo đối chứng (hạn đặt 06/10/2026)

| Món | SL | Đơn giá | Nơi mua |
|---|---|---|---|
| [XIAO nRF52840 Sense](https://hshop.vn/products/mach-seeed-studio-xiao-nrf52840-sense-bluetooth-5-0-imu-microphone-supports-arduino-and-circuitpython) | 2 | 485.000đ | Hshop |
| [Module MAX30102](https://hshop.vn/products/cam-bien-nhip-tim-va-oxy-trong-mau-max30100) | 2 | 38.000đ | Hshop |
| [Màn hình tròn GC9A01 1,28"](https://hshop.vn/man-hinh-lcd-tft-ips-1-28-inch-round-gc9a01-spi-interface) | 1 | 115.000đ | Hshop |
| [Module AD8232](https://icdayroi.com/cam-bien-nhip-ecg-ad8232-heart-rate-monitor) | 1 | 210.000đ | ICDayroi |
| [Module DS18B20](https://icdayroi.com/module-ds18b20) | 1 | 16.000đ | ICDayroi |
| [Motor rung 1027](https://icdayroi.com/dong-co-rung-1027) | 2 | 7.000đ | ICDayroi |
| [Breadboard MB-102](https://icdayroi.com/de-test-board-bread-board-165x54mm) | 1 | 25.000đ | ICDayroi |
| Dây cắm, header đực, 2 nút nhấn 6×6 | 1 bộ | ~40.000đ (ước tính) | ICDayroi |
| [Pin LiPo 3,7 V 250 mAh 502030 có mạch bảo vệ](https://handphone.vn/pin-li-po-3-7v-250mah-502030-lithium-polymer-battery.html) | 2 | 35.000đ | handphone.vn / Shopee |
| Miếng dán điện cực ECG (~50 miếng) | 1 gói | ~60.000đ (ước tính) | Shopee |
| [Máy SpO2 Jumper JPD-500E](https://meta.vn/may-do-nong-do-oxy-trong-mau-jumper-spo2-jpd-500e-p79737) (±2% SpO2, ±2 bpm) | 1 | 380.000đ | Meta.vn |
| [Nhiệt kế điện tử Omron MC-246](https://meta.vn/nhiet-ke-dien-tu-omron-mc-246-p5912) (±0,1 °C) | 1 | 55.000đ | Meta.vn |

**Tổng dự kiến: 2.031.000đ** + phí ship.

Đã có sẵn, không mua: máy huyết áp bắp tay, cáp USB-C dữ liệu, thiếc, nhựa thông, kìm, mỏ hàn, máy khò,
đồng hồ vạn năng, điện thoại Android.

### Vì sao cần máy đo đối chứng

Tuần kiểm chứng (23–29/11) đo 10 người cùng lúc bằng thiết bị của nhóm và bằng máy đối chứng đã có chứng nhận
độ chính xác, rồi tính sai số (Bland–Altman). Máy SpO2 dùng để so SpO2 và nhịp tim (kể cả nhịp tim tính từ ECG),
máy huyết áp bắp tay để hiệu chuẩn và kiểm tra huyết áp ước lượng (PAT), nhiệt kế để so nhiệt độ.

### Lưu ý khi đặt

- Hỏi ICDayroi xem AD8232 có kèm dây 3 cực và miếng dán điện cực không; nếu không, mua thêm.
- Pin LiPo phải có mạch bảo vệ.
- MAX30102 mua 2 cái vì một số module cần sửa điện trở kéo lên I2C (xem `firmware/README.md`).
