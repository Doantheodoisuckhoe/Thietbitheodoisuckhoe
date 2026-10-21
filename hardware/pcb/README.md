# Mạch in đồng hồ (KiCad) – bản chip rời 40 × 40 mm (lưu trữ)

> **Lưu trữ – hướng phát triển.** Từ 21/10/2026 nhóm làm mạch theo phương án **ghép module**
> (XIAO cắm header, module MAX30102, AD8232, MAX30205), xem [`../pcb_module/`](../pcb_module/README.md).
> Bản chip rời dưới đây (MAX30101, AD8232, TMP117 hàn sẵn ở JLCPCB, 40 × 40 mm) giữ lại làm
> hướng phát triển khi thu nhỏ thiết bị; chưa có layout và không cần sửa cùng bản module.

Bản 0.1 (15/10/2026): **mới có sơ đồ nguyên lý**, chưa có layout PCB. ERC: 0 lỗi, 0 cảnh báo (KiCad 10.0.7).

## Mở bằng KiCad

Mở `dong_ho_suc_khoe.kicad_pro` bằng KiCad 9 trở lên, rồi bấm đúp vào sơ đồ nguyên lý.
Ký hiệu và footprint riêng nằm trong `lib/` và đã khai báo trong `sym-lib-table`, `fp-lib-table`
của project, nên mở trên máy khác không cần cài thêm thư viện.

Không có KiCad thì xem bản in: [`xuat/so_do_nguyen_ly.pdf`](xuat/so_do_nguyen_ly.pdf).

| File | Nội dung |
|---|---|
| `dong_ho_suc_khoe.kicad_sch` | Sơ đồ nguyên lý, 1 trang A3, chia 6 khối A–F |
| `lib/DoAn.kicad_sym` | Ký hiệu AD8232, MAX30101, XIAO nRF52840 |
| `lib/DoAn.pretty/` | Footprint XIAO nRF52840 hàn phẳng |
| `xuat/bom_jlcpcb.csv` | BOM theo mẫu JLCPCB (Comment, Designator, Footprint, LCSC), chỉ gồm linh kiện JLCPCB hàn |
| `xuat/so_do_nguyen_ly.pdf` | Bản in sơ đồ |

Sửa sơ đồ xong thì xuất lại PDF và BOM (Eeschema: File → Plot, Tools → Generate BOM).

## Các khối trong sơ đồ

| Khối | Nội dung | Nguồn tham khảo |
|---|---|---|
| A. XIAO | XIAO nRF52840 Sense hàn phẳng, test pad SWD | Footprint/ký hiệu của Seeed |
| B. Nguồn | Pin LiPo, chân sạc pogo 5 V + TVS, LDO 1,8 V, jumper chọn nguồn LED | Datasheet ME6211, MAX30101 |
| C. PPG | MAX30101 + tụ lọc + điện trở kéo lên I2C | Mạch mẫu "Typical Application" trong datasheet MAX30101 |
| D. Nhiệt độ | TMP117, ADD0 = GND (địa chỉ 0x48) | Datasheet TMP117 |
| E. ECG | AD8232, lọc 0,5–40 Hz, 3 điện cực có diode ESD | Cấu hình "cardiac monitor" trong datasheet AD8232 (giá trị giống board SparkFun AD8232) |
| F. Giao diện | Đầu nối màn hình GC9A01, motor rung qua MOSFET, nút SOS | |

### Gán chân XIAO

Giữ nguyên các chân firmware đang dùng, chỉ đổi D2.

| Chân | Tín hiệu | Ghi chú |
|---|---|---|
| D0 (A0) | ECG_OUT | Ngõ ra AD8232 |
| D1 | ECG_LO+ | |
| D2 | MOTOR_EN | **Mới.** Trước dùng cho DS18B20; bản mạch dùng TMP117 qua I2C |
| D3 | ECG_LO- | |
| D4 / D5 | I2C SDA / SCL | MAX30101 (0x57) và TMP117 (0x48) dùng chung |
| D6 / D7 / D8 / D10 | TFT DC / CS / SCK / MOSI | Như `kiem_tra_thu_vien` |
| D9 | SOS_BTN | **Mới.** Nút nối GND, bật `INPUT_PULLUP` |
| 5V (VBUS) | Chân pogo sạc | |
| BAT+ / BAT- | Pin LiPo | Pad mặt dưới XIAO |

## Linh kiện chọn thêm (tra kho JLCPCB ngày 15/10/2026)

| Vai trò | Linh kiện | LCSC | Loại |
|---|---|---|---|
| Ổn áp 1,8 V cho VDD MAX30101 | ME6211C18M5G-N, SOT-23-5 | C236671 | Extended |
| ESD cho 3 điện cực ECG | ESD9B5.0ST5G, SOD-923, hai chiều | C111566 | Extended |
| TVS chân sạc pogo 5 V | SMF5.0A, SOD-123FL | C151296 | Extended |
| MOSFET motor | AO3400A | C20917 | Basic |
| Diode dập motor | B5819W | C8598 | Basic |

Cảm biến (cùng ngày): MAX30101 C2859066 còn 132 con, AD8232 C43216 còn 446, TMP117 C2803242 còn 306.
Điện trở, tụ đều là 0603; phần lớn là Basic, riêng 10 MΩ (C7250) là Basic còn 180k, 360k, 1,4M,
330 nF, 1,5 nF là Extended (mỗi loại Extended JLCPCB tính thêm khoảng 3 USD phí lắp).

## Những điểm cần biết

- **VLED+ của MAX30101 cần 3,1–5 V.** Mặc định lấy 3V3 qua jumper JP1 (cầu 1-2 đã nối sẵn).
  Đèn đỏ và hồng ngoại (dùng cho nhịp tim, SpO2) chạy tốt ở 3,3 V; đèn xanh lá có thể yếu.
  Nếu cần, cắt cầu 1-2 và nối 2-3 để lấy thẳng từ pin.
- **AD8232 luôn bật** (SDN kéo lên 3V3). XIAO hết chân trống nên SDN chỉ ra test pad TP5;
  muốn tắt AD8232 để tiết kiệm pin thì sau này nối TP5 vào một chân GPIO.
- **INT của MAX30101 và ALERT của TMP117** chỉ ra test pad; firmware hiện đọc theo chu kỳ nên không cần.
- **Điện cực ECG:** E1 (LA) và E3 (RL) ở mặt đáy, chạm cổ tay trái; E2 (RA) trên vỏ, chạm bằng ngón
  tay phải. Không có E3 vẫn đo được nhưng nhiễu 50 Hz nhiều hơn.
- **XIAO, pin, motor, nút, màn hình** không nằm trong BOM JLCPCB: nhóm tự hàn.
- Footprint MAX30101 dùng `OptoDevice:Maxim_OLGA-14_3.3x5.6mm_P0.8mm` của KiCad, đúng land pattern
  90-0602 ghi trong datasheet MAX30101.
- Footprint AD8232 là LFCSP-20 pad giữa 2,1 mm, theo gói CP-20-8 của mã AD8232ACPZ-R7.

## Việc tiếp theo

1. SV1, SV2 xem lại sơ đồ (đặc biệt bảng gán chân và khối ECG).
2. Cập nhật firmware: D2 điều khiển motor, D9 đọc nút SOS, thay DS18B20 bằng TMP117.
3. Vẽ layout 40 × 40 mm theo bố trí đã thống nhất: XIAO và pin mặt trên, cảm biến mặt dưới,
   MAX30101 cần cửa sổ quang không bị che.

Ký hiệu và footprint XIAO lấy từ [Seeed Studio OPL_Kicad_Library](https://github.com/Seeed-Studio/OPL_Kicad_Library)
(giấy phép CC-BY-SA-4.0).
