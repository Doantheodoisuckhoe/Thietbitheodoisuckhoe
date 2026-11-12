# Mạch in đồng hồ – bản 2.0 "không dây nối" (KiCad)

Bản 2.0 (12/11/2026). Mạch 2 lớp **42,2 × 45,8 mm = 1933 mm²** (bản 1.3: 50 × 62 mm = 3100 mm², **nhỏ hơn 38 %**).
Mọi module hàn/cắm thẳng vào mạch. Dây còn lại: **2 dây pin** (hàn thẳng vào pad BAT+/BAT- mặt dưới XIAO)
và **2 dây của motor** (hàn thẳng vào 2 pad trên mạch).

Bản 1.3 (`../pcb_module/`, đã gửi xưởng 01/11/2026) giữ nguyên, không sửa.

Kiểm tra bằng KiCad 10.0.7: ****ERC 0 lỗi, 0 cảnh báo; DRC (có `--schematic-parity`) 0 lỗi, 0 cảnh báo, 0 chỗ chưa nối, 0 lỗi footprint/khớp sơ đồ.** Script `cong_cu/kiem_tra_kich_thuoc.py`: 384 điều kiện, 0 lỗi.**

## Mở bằng KiCad

Mở `dong_ho_module_v2.kicad_pro`. Ký hiệu và footprint riêng nằm trong `lib/`.

| File | Nội dung |
|---|---|
| `dong_ho_module_v2.kicad_sch` | Sơ đồ nguyên lý 1 trang A3, khối A–H |
| `dong_ho_module_v2.kicad_pcb` | PCB 2 lớp, đã đi dây và đổ GND hai mặt |
| `lib/` | Ký hiệu và footprint riêng (XIAO, AD8232 9 lỗ, màn GC9A01 8 pad, MAX30102, CJMCU-30205, điện cực, nút SOS, pogo, motor) |
| `xuat/so_do_nguyen_ly.pdf` | Bản in sơ đồ |
| `xuat/bom.csv` | Danh sách linh kiện |
| `xuat/gerber_dong_ho_module_v2.zip` | Gerber + file khoan (cũng có trong `xuat/gerber/`) |
| `xuat/pcb_mat_tren.png`, `xuat/pcb_mat_duoi.png` | Ảnh 3D hai mặt (module không có mô hình 3D, chỉ thấy pad) |
| `xuat/pcb_chong_tang_module.png` | Viền các module chồng lên mạch theo 3 tầng (pin, XIAO, AD8232, màn, motor) |
| `cong_cu/` | Script tạo sơ đồ, footprint, đi dây, kiểm tra kích thước (xem `cong_cu/README.md`) |

## Thay đổi so với bản 1.3

| Bản 1.3 | Bản 2.0 |
|---|---|
| 50 × 62 mm, 4 lỗ M2 | 42,2 × 45,8 mm, **không lỗ vít** (xem mục Cơ khí) |
| XIAO cắm trên 2 header cái | XIAO hàn thẳng bằng 2 hàng chân của nó, đệm ~2,5 mm |
| Pin 603040 + J3 (JST) + J4 (dây sang XIAO), lưới VBAT trên mạch | Pin **502030** (5 × 20 × 30 mm) hàn thẳng vào BAT+/BAT- của XIAO. **Bỏ J3, J4 và lưới VBAT** |
| AD8232 nằm rời, 9 dây vào lưới pad U4 | AD8232 **cắm thẳng qua 9 lỗ** đúng toạ độ đo trên module, nằm cao 8,5 mm trên pin và XIAO |
| Màn GC9A01 nối 8 dây, RES qua R4 + C9 | Màn **hàn thẳng 7 pad** (+ pad 8 BLK cho module 8 chân). **RST nối thẳng 3V3, bỏ R4, C9** |
| RA: dây J6 tới vít ở mép vỏ | RA: **pad đồng lộ 8 × 9,6 mm mặt trên** (E3), góc trái dưới, ngón tay chạm qua cửa sổ vỏ |
| Motor lấy VBAT, J1 header | Motor lấy **+3V3**, 2 pad M1 (TẠM bước 4,0 mm) + tụ C3 10 µF cạnh motor |
| Nút SOS nối 2 dây vào J5 | Nút **6×6×7,5 góc vuông hàn ở mép phải** (SW1, footprint TẠM) |
| 5 tụ 100 nF + 4 tụ 10 µF | C1 10 µF + C2 100 nF cạnh chân 3V3 của XIAO, C3 10 µF cạnh motor (module đã có tụ riêng) |
| J2 pogo (header) | J2 pogo 2 pad mặt dưới (TẠM bước 2,54) – mạch TVS + SS14 giữ nguyên |

Giữ nguyên: MAX30102 (đen 2 × 4, HW-605) và CJMCU-30205 ở mặt da với footprint cũ, I2C D4/D5,
ECG_OUT D0, ECG_LOD D1 (LO+/LO- gộp qua 2 × 1N4148WS, R3 100k), MOTOR_EN D2 (AO3400A, R1 100 Ω, R2 100k,
SS14 dập xung), SOS D9, quy tắc xưởng của bản 1.2.

## Gán chân XIAO nRF52840 Sense

| Chân | Tín hiệu | Nối tới |
|---|---|---|
| D0 (A0) | ECG_OUT | OUTPUT của AD8232 (lỗ 6) |
| D1 | ECG_LOD | LO+ và LO- gộp qua D2, D3 (1N4148WS), R3 100k kéo xuống. **D1 = 1 khi tuột điện cực** |
| D2 | MOTOR_EN | Cổng Q1 AO3400A qua R1 100 Ω, R2 100k kéo xuống |
| D3 | TFT_BLK | Pad 8 của màn (chỉ module 8 chân có BLK; module 7 chân: bỏ trống, đèn nền luôn sáng) |
| D4 / D5 | I2C SDA / SCL | MAX30102 (0x57) và MAX30205 (0x48). Không thêm điện trở kéo lên |
| D6 / D7 | TFT_DC / TFT_CS | Màn GC9A01 |
| D8 / D10 | TFT_SCK / TFT_MOSI | Màn GC9A01 (SCL / SDA của màn) |
| D9 | SOS_BTN | Nút SW1 nối GND, firmware bật `INPUT_PULLUP` |
| 3V3 | +3V3 | 4 module, motor (qua Q1), RST của màn |
| 5V | +5V | Từ chân sạc pogo qua SS14 |
| BAT+ / BAT- (mặt dưới XIAO) | pin | 2 dây pin 502030 hàn thẳng, không đi qua mạch |

Firmware: màn khởi tạo với chân RST = -1 (RST nối cứng 3V3). Không đổi gì khác so với bản 1.3.

## Lỗ chân các module (đúng toạ độ đo)

| Module | Chân | Ghi chú |
|---|---|---|
| U4 AD8232 (28 × 35 mm) | Hàng trên: 1 RA, 2 LA, 3 RL (x = 19,05 / 16,51 / 13,97; y = 0). Cột trái: 4 GND, 5 3V3, 6 OUTPUT, 7 LO-, 8 LO+, 9 SDN (x = 0; y = 10,033 … 22,733, bước 2,54) | Gốc = tâm lỗ vít trên-trái của module, nhìn từ mặt linh kiện. SDN bỏ trống. Không dùng 4 lỗ vít của module |
| U5 GC9A01 1,28" | 1 RST, 2 CS, 3 DC, 4 SDA, 5 SCL, 6 GND, 7 VCC, 8 BLK (bước 2,54, trái → phải nhìn từ mặt màn) | Hàng pad cách tâm màn 24,7 mm, 7 pad đầu nằm giữa tâm. **⚠ THỨ TỰ CẦN KIỂM TRA TRÊN MODULE THẬT** (xem mục TODO) |
| U1 XIAO | 2 × 7, hai hàng cách 15,24 mm | Chân 1 (D0) ở đầu USB-C, đầu anten sát mép trên |
| U2 MAX30102 | 2 × 4, như bản 1.3 | Mặt da, pad vuông = VIN |
| U3 CJMCU-30205 | 1 × 8, như bản 1.3 | Mặt da, xoay dọc |

Script `cong_cu/kiem_tra_kich_thuoc.py` đọc PCB và kiểm tự động: khoảng cách cả 36 cặp pad của AD8232, bước
pad và khoảng cách tới tâm màn, hai hàng XIAO, anten sát mép, pin không đè XIAO, pad AD8232 cách pin, không chân
xuyên lỗ nào nằm dưới module mặt da / motor, màn không che nút SOS và pad RA.

## Bố trí (nhìn từ mặt trên, gốc góc trên-trái, mm)

Xem `xuat/pcb_chong_tang_module.png`. Ba tầng ở mặt trên:

- **L0 (sát mạch)**
  - Pin 502030 nằm dọc ở vùng x 4,1–24,1, y 4,5–34,5 (viền lụa, chữ "PIN 502030"). **Đầu PCM quay xuống**
    (mũi tên "PCM" trên lụa); 2 dây pin luồn sang phải, vào dưới thân XIAO, hàn vào BAT+/BAT-.
  - XIAO ở mép phải (x 24,1–41,9; y 0,2–21,2), **đầu anten sát mép trên**, USB-C quay xuống trong mạch.
    Vùng cấm đồng dưới anten: x 26,6–39,4, y 0–4,0 (cả hai lớp).
  - C1 10 µF, C2 100 nF nằm **dưới thân XIAO** (khe 2,5 mm), sát chân 3V3.
  - Dưới XIAO (y 21,8–34): D5 SS14, D4 SMAJ5.0A (sạc), D1 SS14, C3 10 µF, Q1, R1, R2 (motor), pad M1 ở mép phải.
  - Dải dưới pin: D2, D3, R3 (LO+/LO-), chữ phiên bản.
  - Góc trái dưới: **E3 – pad RA 8 × 9,6 mm** (lộ đồng, ENIG). Góc phải dưới: **SW1 nút SOS**, núm bấm nhô ra mép phải.
- **L1 – module AD8232** cắm trên header cái/chân đực ~8,5 mm ở góc trên-trái; thân module (28 × 35) nằm trên pin
  và một phần XIAO. Cột lỗ GND…SDN ở mép trái (x 1,9), hàng RA/LA/RL ở mép trên (y 1,5).
- **L2 – màn GC9A01** trên cùng, tâm (21,1; 19,25), hàng chân ở y 43,95. Màn không che SW1 và E3.

**Mặt dưới (mặt da):**
- MAX30102 (U2) góc trên-trái, tâm cảm biến (14,1; 10,6), hàng VIN SDA SCL GND ở phía trên.
- CJMCU-30205 (U3) xoay dọc, bên trái phía dưới, chân ở x 15,0.
- E1 (LA) 9 × 16 mm **giữa 2 hàng chân XIAO**; E2 (RL) 9 × 16 mm giữa U3 và motor.
- Motor 1027 (Ø10 mm, dày 2,7 mm) dán ở vùng trống tâm (31,6; 28,2) – vòng tròn và chữ "MOTOR" trên lụa mặt dưới.
- J2 pogo sạc (2 pad) dưới motor, chữ "SẠC +".
- Không có chân xuyên lỗ nào nằm dưới module mặt da, điện cực hay motor (script kiểm tra).

## Thứ tự lắp ráp

1. Hàn linh kiện dán mặt trên: C1, C2 (dưới chỗ XIAO) trước, rồi D1, D4, D5, Q1, R1, R2, R3, C3, D2, D3.
2. Hàn module mặt da: MAX30102 (U2, áp sát, pad vuông = VIN) và CJMCU-30205 (U3). **Cắt sát chân ở mặt trên**
   (nằm trong vùng pin), dán Kapton phủ mối hàn.
3. Hàn XIAO bằng 2 hàng chân của nó, kê đệm ~2,5 mm (để tụ C1/C2 và dây pin lọt bên dưới). Cắt sát chân mặt da.
4. Hàn 2 dây pin 502030 vào BAT+ (đỏ) / BAT- (đen) mặt dưới XIAO **trước khi** đặt pin; đặt pin (PCM quay
   xuống), lót mút mỏng, dán băng keo 2 mặt.
5. Hàn J2 pogo (mặt dưới), SW1 nút SOS (mép phải), dây motor vào M1 (+ = dây đỏ, pad vuông), dán motor mặt dưới.
6. Hàn header cái 9 chân (hoặc chân đực dài) cho AD8232, tháo giắc 3,5 mm của module rồi cắm/hàn module.
   Cắt sát chân mặt da.
7. Hàn màn GC9A01 cuối cùng (sau khi đã kiểm tra thứ tự chân và nạp thử firmware).

## TODO / chỗ TẠM – phải kiểm tra trước khi đặt mạch

1. **Thứ tự chân màn GC9A01.** Footprint theo bản vẽ: 1 RST, 2 CS, 3 DC, 4 SDA, 5 SCL, 6 GND, 7 VCC (trái → phải
   nhìn từ mặt màn). MINH đã ghi module thật là **VCC GND SCL SDA RES DC CS** – hai thứ tự này KHÁC nhau.
   Đọc chữ in trên module thật; nếu khác footprint thì sửa `GC9A01_TEN` trong `cong_cu/kich_thuoc.py`
   và gán lưới U5 trong `gen_sch.py`, chạy lại. Đo lại 24,7 mm (tâm màn → hàng chân).
2. **Nút SOS SW1**: footprint TẠM 4 chân 6,5 × 4,5 mm, lỗ 1,0 mm. Đo nút góc vuông thật (khoảng cách chân, chân
   nào nối nhau, vị trí núm so với chân).
3. **Pogo J2**: TẠM 2 pad bước 2,54, lỗ 1,0 mm, mặt dưới. Đo chân sạc nam châm thật.
4. **Motor M1**: TẠM 2 pad bước 4,0 mm. Chiều dài dây motor phải ≥ ~10 mm (từ mép motor tới pad).
5. **Dây pin 502030**: chiều dài chưa biết; cần ~15–25 mm từ đầu PCM tới BAT+/BAT- dưới XIAO.
   Kiểm tra vị trí pad BAT+/BAT- trên XIAO thật.
6. **Độ cao**: AD8232 phải nằm trên pin (5 mm) và XIAO (đệm 2,5 + XIAO ~3,5 mm): header ~8,5 mm. Màn ở trên
   AD8232 (cần đệm/khung trong vỏ).
7. **Vùng cấm anten** thu lại còn 4,0 mm từ mép (bản 1.3: 4,6 mm) để chân D6 thoát dây; đầu XIAO cách mép 0,2 mm.
8. **Cơ khí**: không còn chỗ cho 4 lỗ M2 (góc trên là AD8232/MAX30102/XIAO, góc dưới là RA/SOS). Vỏ giữ mạch bằng
   gờ đỡ quanh mép + rãnh, hoặc keo nóng/băng keo 2 mặt; có thể dùng 4 gờ ép ở 4 góc (cấm đồng sát mép 0,4 mm).
9. Bề mặt nên **ENIG** (E1, E2, E3 là đồng lộ chạm da).

## Quy tắc thiết kế (theo bảng tiêu chuẩn của xưởng, như bản 1.2)

| Thông số | Bản 2.0 |
|---|---|
| Số lớp, độ dày | 2 lớp, FR4 1,6 mm, đồng 1 oz |
| Dây tín hiệu / dây nguồn | 0,3 mm / 0,5 mm |
| Khoảng cách dây-dây, pad-pad, dây-pad | ≥ 0,25 mm |
| Phủ đồng GND cách dây/pad khác lưới | 0,65 mm |
| Đồng tới mép bảng | 0,4 mm |
| Via | lỗ 0,3 mm, pad 0,9 mm |
| Pad xuyên lỗ | lỗ 1,0 mm, pad 1,6 mm |
| Mũi khoan dùng | 0,3 / 1,0 mm (không có lỗ 2,2 mm vì bỏ lỗ vít) |
| Chữ lụa | cao ≥ 0,8 mm, nét 0,2 mm |

## Số liệu so với bản 1.3

| | Bản 1.3 | Bản 2.0 |
|---|---|---|
| Kích thước | 50 × 62 mm | 42,2 × 45,8 mm |
| Diện tích | 3100 mm² | **1933 mm² (−38 %)** |
| Tổng chiều dài dây đồng | 943 mm | 1054 mm |
| Số via | 97 | 73 |
| Dây điện rời | 17 sợi (9 AD8232 + 8 màn) + pin, motor, nút, RA | **chỉ 2 dây pin + 2 dây motor** |

Dây đồng dài hơn bản 1.3 khoảng 12 % vì 17 đường trước đây là dây điện rời (AD8232, màn) nay thành đường
mạch trên bảng, và chân các module nằm đúng chỗ của module thật (không gom về một góc được).

## Xuất lại file

```
kicad-cli sch erc dong_ho_module_v2.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones --save-board dong_ho_module_v2.kicad_pcb
kicad-cli sch export pdf -o xuat/so_do_nguyen_ly.pdf dong_ho_module_v2.kicad_sch
kicad-cli sch export bom -o xuat/bom.csv --fields "Reference,Value,Footprint,${QUANTITY},Description" --group-by Value,Footprint dong_ho_module_v2.kicad_sch
kicad-cli pcb export gerbers -l "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" -o xuat/gerber/ dong_ho_module_v2.kicad_pcb
kicad-cli pcb export drill --excellon-separate-th --generate-map --map-format gerberx2 -o xuat/gerber/ dong_ho_module_v2.kicad_pcb
kicad-cli pcb render --side top --width 1568 --height 1176 -o xuat/pcb_mat_tren.png dong_ho_module_v2.kicad_pcb
kicad-cli pcb render --side bottom --width 1568 --height 1176 -o xuat/pcb_mat_duoi.png dong_ho_module_v2.kicad_pcb
"C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\kiem_tra_kich_thuoc.py
"C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\ve_chong_tang.py
```
Sau đó nén `xuat/gerber/` thành `xuat/gerber_dong_ho_module_v2.zip`
(PowerShell: `Compress-Archive -Path xuat\gerber\* -DestinationPath xuat\gerber_dong_ho_module_v2.zip -Force`).
