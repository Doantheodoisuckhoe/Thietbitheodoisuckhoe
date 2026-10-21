# Kiểm tra mối hàn chân XIAO

Dùng sau khi hàn header vào XIAO, để biết có chân nào bị chạm thiếc xuống GND, lên 3V3, hoặc dính vào nhau.

## Chạy sketch (11 chân D0-D10)

1. **Rút hết dây và module ra khỏi XIAO.** XIAO có thể cắm trên breadboard nhưng không nối dây gì.
2. Nạp `kiem_tra_chan.ino`, mở Serial Monitor ở 115200.
3. Kết quả lặp lại mỗi 3 giây:
   - `TAT CA 11 CHAN TOT ...` và LED xanh trên XIAO sáng: mối hàn ổn.
   - Dòng `LOI: D4 chap voi D5` hoặc `LOI: D2 chap xuong GND` và LED đỏ sáng: soi đúng chân đó, dùng mỏ hàn kéo bớt thiếc.

Sketch dùng điện trở kéo lên/kéo xuống bên trong chip (khoảng 13 kΩ), dòng rất nhỏ nên không hại board dù có chập.

## Ba chân nguồn: đo bằng đồng hồ

Code không kiểm tra được 5V, GND, 3V3. **Rút USB**, để đồng hồ ở chế độ kêu bíp:

| Đo giữa | Đúng là |
|---|---|
| 3V3 và GND | Không kêu (có thể kêu một tiếng rất ngắn lúc đầu do tụ đang nạp, rồi tắt) |
| 5V và GND | Không kêu |
| 5V và 3V3 | Không kêu |

Kêu liên tục là chập nguồn: **không cắm USB** cho tới khi sửa xong.
