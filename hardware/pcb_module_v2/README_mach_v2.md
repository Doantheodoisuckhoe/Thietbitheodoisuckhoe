# Mạch in đồng hồ – bản 2.1 "không dây nối" (KiCad)

Bản 2.1 (12/11/2026). Mạch 2 lớp **43,7 × 45,8 mm = 2001 mm²** (bản 1.3: 50 × 62 mm = 3100 mm², **nhỏ hơn 35 %**).
Mọi module hàn/cắm thẳng vào mạch. Dây còn lại: **2 dây pin** (hàn thẳng vào pad BAT+/BAT- mặt dưới XIAO)
và **2 dây của motor** (hàn thẳng vào 2 pad trên mạch).

Bản 1.3 (`../pcb_module/`, đã gửi xưởng 01/11/2026) giữ nguyên, không sửa.

Kiểm tra bằng KiCad 10.0.7: **ERC 0 lỗi, 0 cảnh báo; DRC (có `--schematic-parity`) 0 lỗi, 0 cảnh báo, 0 chỗ chưa nối, 0 lỗi footprint/khớp sơ đồ. Script `cong_cu/kiem_tra_kich_thuoc.py`: 2565 điều kiện, 0 lỗi**

Bản 2.1 sửa bản 2.0 sau khi soát chéo: bảng rộng thêm 1,5 mm để pin (thật 20,5 mm) cách thân XIAO ≥ 1 mm;
SS14/SMAJ dời khỏi chỗ đầu cắm USB-C; vùng cấm anten sâu lại 4,6 mm, E1 ra khỏi vùng đó; mặt dưới chỗ dán motor
không còn dây/via, E2 cách motor ≥ 1 mm; nét lụa 0,2 mm, chữ nhỏ không dấu; sửa thứ tự lắp ráp và BOM.

## Mở bằng KiCad

Mở `dong_ho_module_v2.kicad_pro`. Ký hiệu và footprint riêng nằm trong `lib/`.

| File | Nội dung |
|---|---|
| `dong_ho_module_v2.kicad_sch` | Sơ đồ nguyên lý 1 trang A3, khối A–H |
| `dong_ho_module_v2.kicad_pcb` | PCB 2 lớp, đã đi dây và đổ GND hai mặt |
| `lib/` | Ký hiệu và footprint riêng (XIAO, AD8232 9 lỗ, màn GC9A01 8 pad, MAX30102, CJMCU-30205, điện cực, nút SOS, pogo, motor) |
| `xuat/so_do_nguyen_ly.pdf` | Bản in sơ đồ |
| `xuat/bom.csv` | Linh kiện trên mạch (xuất từ sơ đồ) |
| `xuat/bom_ngoai_mach.csv` | Vật tư ngoài mạch: pin, header/chân dài, motor, Kapton… (xem mục BOM) |
| `xuat/gerber_dong_ho_module_v2.zip` | Gerber + file khoan (cũng có trong `xuat/gerber/`) |
| `xuat/pcb_mat_tren.png`, `xuat/pcb_mat_duoi.png` | Ảnh 3D hai mặt (module không có mô hình 3D, chỉ thấy pad) |
| `xuat/pcb_chong_tang_module.png` | Viền các module chồng lên mạch theo 3 tầng (pin, XIAO, AD8232, màn, motor) |
| `cong_cu/` | Script tạo sơ đồ, footprint, đi dây, kiểm tra kích thước (xem `cong_cu/README.md`) |

## Đặt mạch ở xưởng

- Gửi `xuat/gerber_dong_ho_module_v2.zip`. 2 lớp, FR4 1,6 mm, đồng 1 oz, đặt **từng mạch rời, không ghép panel**.
- **Bề mặt ENIG phải ghi trong đơn đặt hàng** (Gerber không chứa thông tin này). E1, E2, E3 là đồng lộ chạm da.
- File `…-NPTH.drl` **rỗng là đúng**: bản 2.x không có lỗ không mạ (bỏ lỗ vít). Chỉ có lỗ mạ 0,3 mm (via) và 1,0 mm.

## Thay đổi so với bản 1.3

| Bản 1.3 | Bản 2.1 |
|---|---|
| 50 × 62 mm, 4 lỗ M2 | 43,7 × 45,8 mm, **không lỗ vít** (xem mục Cơ khí) |
| XIAO cắm trên 2 header cái | XIAO hàn thẳng bằng 2 hàng chân của nó, đệm ~2,5 mm |
| Pin 603040 + J3 (JST) + J4 (dây sang XIAO), lưới VBAT trên mạch | Pin **502030** (~5,5 × 20,5 × 30 mm) hàn thẳng vào BAT+/BAT- của XIAO. **Bỏ J3, J4 và lưới VBAT** |
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
| D4 / D5 | I2C SDA / SCL | MAX30102 (0x57) và MAX30205 (0x48). **Không có điện trở kéo lên trên mạch**: dùng điện trở có sẵn trên module MAX30102/CJMCU (đo lại trên bàn thử) |
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
| U1 XIAO | 2 × 7, hai hàng cách 15,24 mm | Chân 1 (D0) ở đầu USB-C, đầu anten cách mép trên 0,8 mm |
| U2 MAX30102 | 2 × 4, như bản 1.3 | Mặt da, pad vuông = VIN |
| U3 CJMCU-30205 | 1 × 8, như bản 1.3 | Mặt da, xoay dọc |

Script `cong_cu/kiem_tra_kich_thuoc.py` đọc PCB và kiểm tự động (2565 điều kiện): khoảng cách cả 36 cặp pad của
AD8232, bước pad và khoảng cách tới tâm màn, hai hàng XIAO, anten gần mép và vùng cấm sâu ≥ 4,6 mm không có E1/dây/via,
pin cách thân XIAO ≥ 1 mm, pad AD8232 cách pin, không linh kiện dán trong 3 mm dưới đầu USB-C, không chân xuyên lỗ nằm dưới
module mặt da / motor, không dây/via mặt dưới dưới motor, motor cách module/điện cực ≥ 1 mm, màn không che nút SOS và pad RA.

## Bố trí (nhìn từ mặt trên, gốc góc trên-trái, mm)

Xem `xuat/pcb_chong_tang_module.png`. Ba tầng ở mặt trên:

- **L0 (sát mạch)**
  - Pin 502030 nằm dọc ở vùng x 4,1–24,6, y 4,5–34,5 (viền lụa, chữ "PIN 502030"). **Đầu PCM quay xuống**
    (mũi tên "PCM" trên lụa); 2 dây pin luồn sang phải, vào dưới thân XIAO, hàn vào BAT+/BAT-.
  - XIAO ở mép phải (x 25,6–43,4; y 0,8–21,8), cách pin 1 mm, **đầu anten ở mép trên**, USB-C quay xuống trong mạch.
    Vùng cấm đồng dưới anten: x 28,1–40,9, y 0–4,6 (cả hai lớp, không dây, không via).
  - C1 10 µF, C2 100 nF nằm **dưới thân XIAO** (khe 2,5 mm), sát chân 3V3.
  - Dưới XIAO: chừa trống 3 mm dưới đầu USB-C (rộng 9 mm) cho phích cắm. D5 SS14 đứng dọc ở bên trái chỗ đó;
    D4 SMAJ5.0A, D1 SS14, C3 10 µF, Q1, R1, R2 (motor) từ y ≥ 25; pad M1 ở mép phải.
  - Dải dưới pin: D2, D3, R3 (LO+/LO-), chữ phiên bản.
  - Góc trái dưới: **E3 – pad RA 8 × 9,6 mm** (lộ đồng, ENIG), cách đầu PCM của pin chỉ ~0,8 mm: dán Kapton lên đầu PCM.
    Góc phải dưới: **SW1 nút SOS**, núm bấm nhô ra mép phải.
- **L1 – module AD8232** cắm trên header cái/chân đực ~8,5 mm ở góc trên-trái; thân module (28 × 35) nằm trên pin
  và một phần XIAO. Cột lỗ GND…SDN ở mép trái (x 1,9), hàng RA/LA/RL ở mép trên (y 1,5).
- **L2 – màn GC9A01** trên cùng, tâm (21,1; 19,25), hàng chân ở y 43,95. Màn không che SW1 và E3.
  Màn phải cao ~11–12 mm so với mạch (trên AD8232): dùng chân đực dài hoặc header.

**Mặt dưới (mặt da):**
- MAX30102 (U2) góc trên-trái, tâm cảm biến (14,1; 10,6), hàng VIN SDA SCL GND ở phía trên.
- CJMCU-30205 (U3) xoay dọc, bên trái phía dưới, chân ở x 15,0.
- E1 (LA) 9 × 16 mm **giữa 2 hàng chân XIAO**, ngoài vùng cấm anten; E2 (RL) 9 × 16 mm giữa U3 và motor.
- Motor 1027 (Ø10 mm, dày 2,7 mm) dán ở tâm (33,6; 29,5) – chữ "MOTOR" trên lụa mặt dưới. Vùng dưới motor
  ở lớp đồng dưới không có dây và via (chỉ đồng GND phủ mask).
- J2 pogo sạc (2 pad) dưới motor, chữ "SAC +".
- Không có chân xuyên lỗ nào nằm dưới module mặt da, điện cực hay motor (script kiểm tra).
- **Điện cực E1/E2 phẳng với mạch, còn U2/U3/motor nhô ra 1,5–3 mm**: vỏ cần gờ nhô hoặc lò xo/nút kim loại để
  E1, E2 chạm da.

## Thứ tự lắp ráp

Chân của U2, U3 (mặt da) được hàn từ mặt trên và nằm sát chân XIAO/AD8232, nên hàn XIAO và đế AD8232 trước.

1. Hàn linh kiện dán mặt trên: C1, C2 (dưới chỗ XIAO) trước, rồi D1, D4, D5, Q1, R1, R2, R3, C3, D2, D3.
2. **Hàn sẵn 2 dây pin** 502030 vào BAT+ (đỏ) / BAT- (đen) ở mặt dưới XIAO (chưa nối pin vào, hoặc nối pin nhưng
   cách điện kỹ đầu dây). Phải làm trước vì sau khi XIAO nằm trên mạch thì không với tới pad này.
3. Hàn XIAO bằng 2 hàng chân của nó, kê đệm ~2,5 mm (để tụ C1/C2 và dây pin lọt bên dưới), dây pin luồn ra phía pin.
   Cắt sát chân ở mặt da.
4. Hàn đế header 9 chân (hoặc chân đực dài) cho AD8232 (chưa cắm module). Cắt sát chân ở mặt da.
5. Hàn module mặt da: MAX30102 (U2, áp sát, pad vuông = VIN) và CJMCU-30205 (U3), hàn từ mặt trên.
   **Cắt sát chân ở mặt trên** (nằm trong vùng pin), dán Kapton phủ mối hàn.
6. Hàn J2 pogo (mặt dưới), SW1 nút SOS (mép phải), dây motor vào M1 (+ = dây đỏ, pad vuông), dán motor mặt dưới.
7. Đặt pin (PCM quay xuống, dán Kapton lên đầu PCM vì sát pad RA), lót mút mỏng, dán băng keo 2 mặt.
8. Tháo giắc 3,5 mm của module AD8232 rồi cắm/hàn module lên đế.
9. Hàn màn GC9A01 cuối cùng (chân dài ~11–12 mm, sau khi đã kiểm tra thứ tự chân và nạp thử firmware).

## BOM

- `xuat/bom.csv`: linh kiện trên mạch, xuất từ sơ đồ (E1, E2, E3 là pad đồng, không mua).
- `xuat/bom_ngoai_mach.csv`: vật tư không có trên sơ đồ – pin 502030, header cái 1×9 (hoặc 1×3 + 1×6) cao ~8,5 mm
  hoặc chân đực dài cho AD8232, chân dài 1×7/1×8 cho màn, motor 1027, nút 6×6×7,5 góc vuông, pogo nam châm,
  Kapton, mút, băng keo 2 mặt, dây mảnh.

## TODO / chỗ TẠM – phải kiểm tra trước khi đặt mạch

1. **Thứ tự chân màn GC9A01.** Footprint theo bản vẽ: 1 RST, 2 CS, 3 DC, 4 SDA, 5 SCL, 6 GND, 7 VCC (trái → phải
   nhìn từ mặt màn). MINH đã ghi module thật là **VCC GND SCL SDA RES DC CS** – hai thứ tự này KHÁC nhau.
   Đọc chữ in trên module thật; nếu khác footprint thì sửa `GC9A01_TEN` trong `cong_cu/kich_thuoc.py`
   và gán lưới U5 trong `gen_sch.py`, chạy lại. Đo lại 24,7 mm (tâm màn → hàng chân).
2. **Nút SOS SW1**: footprint TẠM 4 chân 6,5 × 4,5 mm, lỗ 1,0 mm. Đo nút góc vuông thật (khoảng cách chân, chân
   nào nối nhau, vị trí núm so với chân).
3. **Pogo J2**: TẠM 2 pad bước 2,54, lỗ 1,0 mm, mặt dưới. Đo chân sạc nam châm thật.
4. **Motor M1**: TẠM 2 pad bước 4,0 mm. Dây motor phải dài ≥ ~5 mm từ mép motor tới pad.
5. **Dây pin 502030**: chiều dài chưa biết; cần ~15–25 mm từ đầu PCM tới BAT+/BAT- dưới XIAO.
   Kiểm tra vị trí pad BAT+/BAT- trên XIAO thật.
6. **Độ cao**: AD8232 phải nằm trên pin (5,5 mm) và XIAO (đệm 2,5 + XIAO ~3,5 mm): header ~8,5 mm. Màn ở trên
   AD8232, chân ~11–12 mm.
7. **Anten BLE**: vùng cấm sâu 4,6 mm từ mép (đầu XIAO lùi vào 0,8 mm để chân D6 vẫn thoát dây giữa chân 6 và 7,
   nên vùng cấm phủ 3,8 mm đầu XIAO). Anten còn bị **màn và module AD8232 che một phần** từ phía trên: thử lại tầm
   phát BLE khi đã lắp đủ.
8. **Cơ khí**: không còn chỗ cho 4 lỗ M2 (góc trên là AD8232/MAX30102/XIAO, góc dưới là RA/SOS). Vỏ giữ mạch bằng
   gờ đỡ quanh mép + rãnh, hoặc keo nóng/băng keo 2 mặt (đồng cách mép 0,4 mm).
9. **Điện trở kéo lên I2C** lấy từ module MAX30102/CJMCU: đo trên bàn thử (đã chạy tốt ở 3,3 V với MAX30102).

## Quy tắc thiết kế (theo bảng tiêu chuẩn của xưởng, như bản 1.2)

| Thông số | Bản 2.1 |
|---|---|
| Số lớp, độ dày | 2 lớp, FR4 1,6 mm, đồng 1 oz |
| Dây tín hiệu / dây nguồn | 0,3 mm / 0,5 mm |
| Khoảng cách dây-dây, pad-pad, dây-pad | ≥ 0,25 mm |
| Phủ đồng GND cách dây/pad khác lưới | 0,65 mm |
| Đồng tới mép bảng | 0,4 mm |
| Via | lỗ 0,3 mm, pad 0,9 mm |
| Pad xuyên lỗ | lỗ 1,0 mm, pad 1,6 mm |
| Mũi khoan dùng | 0,3 / 1,0 mm (không có lỗ 2,2 mm vì bỏ lỗ vít) |
| Chữ lụa | cao ≥ 0,8 mm, nét chữ và nét vẽ 0,2 mm; chữ nhỏ viết không dấu |

## Số liệu so với bản 1.3

| | Bản 1.3 | Bản 2.1 |
|---|---|---|
| Kích thước | 50 × 62 mm | 43,7 × 45,8 mm |
| Diện tích | 3100 mm² | **2001 mm² (−35 %)** |
| Tổng chiều dài dây đồng | 943 mm | 1063 mm |
| Số via | 97 | 77 |
| Dây điện rời | 17 sợi (9 AD8232 + 8 màn) + pin, motor, nút, RA | **chỉ 2 dây pin + 2 dây motor** |

Dây đồng dài hơn bản 1.3 vì 17 đường trước đây là dây điện rời (AD8232, màn) nay thành đường mạch trên bảng,
và chân các module nằm đúng chỗ của module thật (không gom về một góc được).

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
