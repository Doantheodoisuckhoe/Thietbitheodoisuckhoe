# Phát hiện té ngã bằng IMU

Dùng IMU LSM6DS3 có sẵn trên XIAO nRF52840 Sense, không cần nối thêm linh kiện.

| File | Việc |
|---|---|
| `firmware/ghi_imu/ghi_imu.ino` | Đọc gia tốc (±16 g) và con quay (±2000 °/s) ở 100 mẫu/giây, in CSV `t_ms,ax,ay,az,gx,gy,gz` ra Serial |
| `ghi_du_lieu.py` | Lưu dữ liệu Serial thành file CSV có nhãn trong `data/imu/` |
| `phat_hien.py` | Thuật toán ngưỡng ban đầu: rơi tự do → va chạm → nằm yên; báo kết quả cho từng file và theo từng nhãn |

## 1. Chuẩn bị

1. Nạp `firmware/ghi_imu` lên board, mở Serial Monitor 115200 xem có các dòng số chạy ra không, rồi **đóng Serial Monitor**.
2. Cài Python 3 và thư viện: `pip install pyserial`.
3. Gắn board vào cổ tay trái bằng dây chun hoặc băng dính, mặt có chữ hướng ra ngoài. Dùng cáp USB‑C dài (≥ 1,5 m) nối vào laptop.

## 2. Thu dữ liệu

Trong thư mục `algorithm/te_nga` chạy `python ghi_du_lieu.py COM5` (đổi COM5 thành cổng của board).
Mỗi lần ghi: nhập nhãn, nhập số giây, đếm ngược 3 giây rồi thực hiện động tác.

| Nhãn | Động tác | Số lần | Số giây |
|---|---|---|---|
| `dung_yen` | Đứng hoặc ngồi yên | 3 | 10 |
| `di_bo` | Đi bộ bình thường | 5 | 15 |
| `ngoi_xuong` | Ngồi mạnh xuống ghế | 10 | 10 |
| `nam_xuong` | Nằm xuống giường | 5 | 10 |
| `dap_tay` | Đập tay xuống bàn, vẫy tay mạnh | 10 | 5 |
| `nhay` | Nhảy tại chỗ | 5 | 10 |
| `nga` | Khuỵu ngã xuống **nệm dày** (về trước, sau, sang hai bên), sau đó nằm yên ~3 giây | 10–20 | 10 |
| `roi_board` | Thả rơi board từ ~1 m xuống gối | 10 | 5 |

An toàn: chỉ ngã lên nệm dày, không ngã trên nền cứng; để cáp không vướng chân.
Nhãn `roi_board` dùng để kiểm tra pha rơi tự do; ngã thật của người thường có pha rơi ngắn và yếu hơn,
nên ngưỡng phải chỉnh theo dữ liệu `nga`.

## 3. Chạy thuật toán

`python phat_hien.py` in kết quả cho mọi file trong `data/imu/` và bảng tổng hợp: file `nga` cần báo ngã,
các nhãn khác không được báo. Nếu bỏ sót hoặc báo nhầm, chỉnh các ngưỡng ở đầu file
(`NGUONG_ROI`, `NGUONG_VA_CHAM`, `DO_LECH_NAM_YEN`) rồi chạy lại.

Khi ngưỡng đã ổn trên dữ liệu thật, chuyển thuật toán vào firmware để chạy trực tiếp trên board.
