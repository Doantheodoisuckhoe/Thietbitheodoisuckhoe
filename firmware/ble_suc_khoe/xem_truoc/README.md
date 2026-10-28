# Xem trước màn hình GC9A01 trên máy tính

Thư mục này vẽ thử các màn của đồng hồ ra ảnh PNG bằng **đúng code** `../man_hinh.h` mà firmware dùng,
nên xem được bố cục trước khi có màn thật. Arduino IDE không biên dịch thư mục con này (chỉ dùng trên máy tính).

Ảnh đã vẽ sẵn: [`anh/tong_hop_man_hinh.png`](anh/tong_hop_man_hinh.png) (màn tròn 240 × 240, phóng to 2 lần).

| Ảnh | Khi nào hiện |
|---|---|
| `1_man_chinh` | Đang đeo, có số đo, điện thoại đang kết nối |
| `2_man_chinh_mat_ket_noi` | Mất kết nối điện thoại, pin yếu (biểu tượng Bluetooth xám, pin đỏ) |
| `3_chua_deo` | Cảm biến không thấy cổ tay |
| `4_te_nga_dem_nguoc` | Vừa phát hiện té ngã: đếm ngược 15 giây, bấm nút để hủy |
| `5_sos` | Đã giữ nút 1 giây, đang chờ app xác nhận |
| `6_nhip_tim_cao`, `7_sot` | Cảnh báo chỉ số bất thường (nền cam) |
| `8_da_bao` | App đã xác nhận và gửi tin cho người thân (hiện 5 giây) |

Màn chính tắt sau 10 giây; bấm nhanh nút SOS để bật lại. Màn té ngã và cảnh báo luôn sáng.

## Vẽ lại sau khi sửa `man_hinh.h`

Cần g++ và Python có Pillow, cùng thư viện Adafruit GFX (thư mục `Documents\Arduino\libraries\Adafruit_GFX_Library`
trên Windows, hoặc `git clone https://github.com/adafruit/Adafruit-GFX-Library`).

```
g++ -std=c++11 -w -DARDUINO=100 -Igia_lap -I<thư mục Adafruit GFX> xem_truoc.cpp <thư mục Adafruit GFX>/Adafruit_GFX.cpp -o xem_truoc
./xem_truoc
python ghep_anh.py .
```

`gia_lap/` là bản giả lập tối thiểu của `Arduino.h` để Adafruit GFX chạy được trên máy tính.
