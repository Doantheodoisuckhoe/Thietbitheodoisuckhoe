# Mạch in đồng hồ – bản ghép module (KiCad)

Bản 1.2 (28/10/2026). Mạch 2 lớp **50 × 62 mm** ghép các module có sẵn, toàn bộ linh kiện hàn tay được
(điện trở, tụ 0805; SOT-23; SOD-323; SMA; header 2,54 mm). Thay cho bản chip rời 40 × 40 mm
trong [`../pcb/`](../pcb/README.md) (bản đó giữ lại làm hướng phát triển).

Kiểm tra bằng KiCad 10.0.7 (bản 1.2): **ERC 0 lỗi, 0 cảnh báo; DRC 0 lỗi, 0 chỗ chưa nối, khớp sơ đồ (schematic parity) 0 lỗi.**
DRC còn 6 cảnh báo `lib_footprint_mismatch` (J1–J6 khác footprint chuẩn của KiCad vì đã nới pad theo xưởng, cố ý).

Thay đổi bản 1.2: theo bảng tiêu chuẩn của xưởng mạch trong nước. Via lỗ 0,3 / pad 0,9 mm; pad xuyên lỗ = lỗ + 0,6 mm
(header 1,0 / 1,6 mm, JST 0,8 / 1,4 mm); phủ đồng GND cách dây 0,65 mm (≥ 25 mil); chữ lụa nét 0,2 mm. Vị trí linh kiện và
đường dây giữ như bản 1.1 (xem mục Quy tắc thiết kế).

Thay đổi bản 1.1: footprint MAX30102 đổi sang module đen 2 × 4 chân (đo thật); D2/D3 đổi sang 1N4148WS SOD-323,
D4 đổi sang TVS SMAJ5.0A SMA (đúng loại icdayroi bán).

## Mở bằng KiCad

Mở `dong_ho_module.kicad_pro` (KiCad 9 trở lên). Ký hiệu và footprint riêng nằm trong `lib/` và đã khai
báo trong `sym-lib-table`, `fp-lib-table` của project.

| File | Nội dung |
|---|---|
| `dong_ho_module.kicad_sch` | Sơ đồ nguyên lý 1 trang A3, chia khối A–H |
| `dong_ho_module.kicad_pcb` | PCB 2 lớp, đã đi dây và đổ GND hai mặt |
| `lib/DoAnModule.kicad_sym` | Ký hiệu: XIAO cắm header, module MAX30102, CJMCU-30205, AD8232, màn GC9A01 |
| `lib/DoAnModule.pretty/` | Footprint: đế XIAO, module cảm biến gắn mặt dưới, pad hàn dây, điện cực ECG |
| `xuat/so_do_nguyen_ly.pdf` | Bản in sơ đồ |
| `xuat/bom.csv` | Danh sách linh kiện |
| `xuat/gerber_dong_ho_module.zip` | Gerber + file khoan, gửi xưởng mạch |
| `xuat/pcb_mat_tren.png`, `xuat/pcb_mat_duoi.png` | Ảnh 3D hai mặt (module không có mô hình 3D, chỉ thấy pad) |
| `cong_cu/` | Script đã dùng để tạo sơ đồ, footprint, đi dây (chỉ để tham khảo) |

Sửa sơ đồ hoặc PCB xong thì chạy lại ERC/DRC và xuất lại các file trong `xuat/` (lệnh ở cuối trang).

## Gán chân XIAO nRF52840 Sense

| Chân | Tín hiệu | Nối tới |
|---|---|---|
| D0 (A0) | ECG_OUT | OUTPUT của AD8232 |
| D1 | ECG_LOD | LO+ và LO- gộp qua 2 diode 1N4148WS, R3 100k kéo xuống. **D1 = 1 khi tuột điện cực** |
| D2 | MOTOR_EN | Cổng AO3400A qua R1 100 Ω, R2 100k kéo xuống |
| D3 | TFT_BLK | Đèn nền màn hình (mới, trước đây D3 là LO-) |
| D4 / D5 | I2C SDA / SCL | MAX30102 (0x57) và MAX30205 (0x48). Không thêm điện trở kéo lên: hai module đã có |
| D6 / D7 | TFT_DC / TFT_CS | Màn GC9A01 |
| D8 / D10 | TFT_SCK / TFT_MOSI | Màn GC9A01 (SPI) |
| D9 | SOS_BTN | Nút nối GND, firmware bật `INPUT_PULLUP` |
| 3V3 | +3V3 | Cấp cho cả 4 module, mỗi module có 100 nF + 10 µF |
| 5V | +5V | Từ chân sạc pogo qua SS14 |
| BAT+ / BAT- (mặt dưới XIAO) | VBAT+ / VBAT- | Dây ngắn từ pad J4 |

RES của màn hình không có chân GPIO riêng: R4 10k kéo lên 3V3 + C9 100 nF xuống GND (reset khi cấp nguồn).
Firmware khởi tạo màn với chân RST = -1.

## Đấu nối các module (pad hàn dây)

| Pad | Thứ tự | Ghi chú |
|---|---|---|
| U4 – AD8232 (lưới 3 × 3, bước 3 mm) | 1 GND, 2 3V3, 3 OUT / 4 LO-, 5 LO+, 6 SDN / 7 RA, 8 LA, 9 RL | SDN bỏ trống (module tự kéo lên). RA/LA/RL: hàn dây từ pad điện cực trên module, tháo giắc 3,5 mm |
| U5 – GC9A01 (lưới 2 × 4, bước 3 mm) | 1 VCC, 2 GND / 3 SCL, 4 SDA / 5 RES, 6 DC / 7 CS, 8 BLK | Chữ in cạnh pad |
| J1 – motor 1027 | 1 VBAT+ (dây đỏ), 2 MOTOR_N | Diode SS14 dập xung ngược nằm ngay cạnh |
| J2 – chân sạc pogo (cái, nam châm) | 1 +5V vào, 2 GND | Qua TVS SMAJ5.0A rồi SS14 tới chân 5V của XIAO |
| J3 – JST PH2.0 | 1 VBAT+, 2 VBAT- | Pin 603040 có mạch bảo vệ |
| J4 – dây sang XIAO | 1 VBAT+, 2 VBAT- | Hàn 2 dây ngắn lên pad BAT+ / BAT- ở mặt dưới XIAO |
| J5 – nút SOS | 1 SOS_BTN, 2 GND | |
| J6 – RA | 1 pad | Dây tới vít thép ở mép vỏ (ngón tay phải chạm) |
| E1 (LA), E2 (RL) | pad đồng 9 × 16 mm lộ đồng ở mặt da | Chạm cổ tay trái |

## Bố trí

**Mặt trên** (nhìn từ trên, gốc ở góc trên-trái):
- XIAO cắm trên 2 hàng header cái 1x7 ở giữa mép trên, **đầu anten sát mép trên**, cổng USB-C quay vào
  trong. Vùng dưới anten (18,6–31,4 × 0–4,6 mm) cấm đồng và via cả hai lớp.
- Vùng pin LiPo 40 × 30 mm (x 5–45, y 24,5–54,5) không đặt linh kiện; có dây mạch và đồng GND, phủ
  mask. Dán băng keo Kapton trước khi đặt pin.
- Góc trái trên: pad màn hình, R4/C9/C7/C8, nút SOS. Góc phải trên: pad AD8232, D2/D3/R3, C5/C6, pad RA.
- Dưới thân XIAO (giữa 2 hàng header): pad J4 và C1/C2 của MAX30102 (linh kiện thấp; XIAO cắm trên header
  cái cao ~8,5 mm nên không vướng).
- Dải trái cạnh pin: SS14 (D5), TVS (D4), pad sạc J2. Dải phải: SS14 (D1), AO3400A (Q1), R2, pad motor J1, R1.
- Mép dưới: JST pin J3, tụ C3/C4 của MAX30205.

**Mặt dưới (mặt da):**
- Module MAX30102 đen 2 × 4 chân (20 × 15 mm) ở giữa, tâm cảm biến (25; 30) mm, mặt cảm biến hướng ra da,
  mặt chữ áp vào mạch. Hàng VIN SDA SCL GND nằm phía XIAO (y 24,9 mm), hàng GND RD IRD INT phía pin (y 35,1 mm);
  pad vuông = VIN (có chữ VIN ở mặt trên). 8 mối hàn của module nằm trong vùng pin: cắt sát chân, dán Kapton
  và 1 lớp mút mỏng trước khi đặt pin.
- Module CJMCU-30205 phía dưới (tâm ~ (25; 50,5) mm), cách LED MAX30102 khoảng 21 mm.
- Hai điện cực E2 (RL) và E1 (LA) hai bên MAX30102, mỗi cái 9 × 16 mm, mở mask lộ đồng.
- Lớp dưới gần như là mặt GND liền; mọi chân GND còn được nối bằng dây 0,5 mm nên không phụ thuộc vào đổ đồng.

**Module AD8232 không gắn trên mạch:** nó nằm phía trên pin (36 × 30 mm vừa với pin 40 × 30 mm), lót
băng keo cách điện, nối bằng 9 sợi dây ngắn vào lưới pad U4. Màn hình cũng nối bằng dây (8 sợi).

## Quy tắc thiết kế (theo bảng tiêu chuẩn của xưởng mạch, bản 1.2)

Bản 1.2 giữ nguyên vị trí linh kiện và đường dây của bản 1.1; script `cong_cu/ap_quy_tac_xuong.py`
chỉ đổi lỗ khoan, pad, via, phủ đồng và chữ lụa cho khớp bảng tiêu chuẩn của xưởng.

| Thông số | Bản 1.2 | Xưởng yêu cầu |
|---|---|---|
| Số lớp, độ dày | 2 lớp, FR4 1,6 mm, đồng 1 oz | |
| Dây tín hiệu / dây nguồn | 0,3 mm / 0,5 mm | ≥ 0,2 mm |
| Khoảng cách dây-dây, pad-pad, dây-pad, dây-via | ≥ 0,25 mm | ≥ 0,23 mm |
| Phủ đồng GND cách dây/pad khác lưới | 0,65 mm (≥ 25 mil) | ≥ 0,5 mm |
| Đồng tới mép bảng | 0,4 mm | ≥ 0,25 mm |
| Via xuyên lỗ | lỗ 0,3 mm, pad 0,9 mm | lỗ có trong bảng mũi khoan, pad = lỗ + 0,6 |
| Pad xuyên lỗ (header, module) | lỗ 1,0 mm, pad 1,6 mm | pad = lỗ + 0,6 |
| Pad JST PH (J3) | lỗ 0,8 mm, pad 1,4 × 1,75 mm | |
| Mũi khoan dùng | 0,3 / 0,8 / 1,0 mm (+ lỗ vít 2,2 mm không mạ) | 0,3 0,6 0,8 0,9 1,0 1,1 1,2 1,5 1,8 2,0… |
| Chữ lụa | cao ≥ 0,8 mm, nét 0,2 mm | nét 0,2 mm |
| Lỗ bắt vít | 4 × M2 (lỗ 2,2 mm) ở 4 góc, cách mép 3,5 mm | hỏi xưởng có mũi 2,2 không |
| Bề mặt | ENIG hoặc HASL (điện cực ECG lộ đồng, nên ENIG) | |

## Cần kiểm tra trên module thật trước khi đặt mạch

1. **Khoảng cách hai hàng chân XIAO = 15,24 mm** (đo bằng thước kẹp, hoặc cắm thử XIAO lên breadboard:
   hai hàng cách nhau đúng 6 lỗ). Chân D0 phải ở đầu USB-C, anten ở đầu D6/D7.
2. **Module MAX30102 đen 2 × 4** (đo 27/10/2026: 20 × 15 mm, hai hàng cách 10 mm). Nhìn từ mặt chữ: hàng
   "GND RD IRD INT" và hàng "VIN SDA SCL GND", GND hàng trên thẳng cột với VIN hàng dưới; hai chân GND nằm
   chéo góc (đo thông mạch phải kêu). Trước khi hàn: úp mặt chữ vào mặt dưới mạch, chân VIN phải vào pad vuông.
3. **Điện trở kéo lên I2C của module MAX30102**: đã chạy tốt trên breadboard ở 3,3 V (0x57, 24/10/2026).
4. **Thứ tự chân CJMCU-30205**: VCC, GND, SDA, SCL, OS, A0, A1, A2 (1x8), đã khớp ảnh module thật; dài 21 mm. VCC chỉ cấp 3,3 V.
5. **Module AD8232** (30 × 27 mm): thứ tự header GND, 3.3V, OUTPUT, LO-, LO+, SDN và 3 pad RL, LA, RA ở mép trên, đã khớp.
6. **Vị trí anten XIAO**: mạch giả định anten ở đầu đối diện USB-C.
7. **Độ cao**: nên hàn MAX30102 áp sát mạch (rút bỏ đệm nhựa của header, lót Kapton), module chỉ cao ~3 mm.
   Nếu dùng header có đệm thì cao 5–6 mm, điện cực E1/E2 trên mạch lùi vào
   so với mặt cảm biến. Vỏ cần lỗ/gờ để điện cực chạm da, hoặc gắn thêm nút kim loại/lò xo hàn lên E1, E2.
8. Motor rung lấy nguồn từ VBAT+ (3,0–4,2 V). Motor 1027 loại 3 V chạy được; nếu rung quá mạnh, thêm
   điện trở 10–22 Ω nối tiếp hoặc chỉnh PWM ở D2.

## Xuất lại file

```
kicad-cli sch erc dong_ho_module.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones --save-board dong_ho_module.kicad_pcb
kicad-cli sch export pdf -o xuat/so_do_nguyen_ly.pdf dong_ho_module.kicad_sch
kicad-cli sch export bom -o xuat/bom.csv --fields "Reference,Value,Footprint,${QUANTITY},Description" --group-by Value,Footprint dong_ho_module.kicad_sch
kicad-cli pcb export gerbers -l "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" -o xuat/gerber/ dong_ho_module.kicad_pcb
kicad-cli pcb export drill --excellon-separate-th --generate-map --map-format gerberx2 -o xuat/gerber/ dong_ho_module.kicad_pcb
kicad-cli pcb render --side top --width 1568 --height 1176 -o xuat/pcb_mat_tren.png dong_ho_module.kicad_pcb
kicad-cli pcb render --side bottom --width 1568 --height 1176 -o xuat/pcb_mat_duoi.png dong_ho_module.kicad_pcb
```
Sau đó nén thư mục `xuat/gerber/` thành `xuat/gerber_dong_ho_module.zip`
(PowerShell: `Compress-Archive -Path xuat\gerber\* -DestinationPath xuat\gerber_dong_ho_module.zip -Force`).
