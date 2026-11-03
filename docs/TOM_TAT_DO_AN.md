# TÓM TẮT TOÀN BỘ ĐỒ ÁN TỐT NGHIỆP (cập nhật 03/11/2026)

> **Cách dùng file này:** khi mở một cuộc trò chuyện mới với Claude (hoặc AI khác), dán toàn bộ file này vào
> tin nhắn đầu tiên và viết: *"Đây là tóm tắt đồ án của tôi, hãy đọc và tiếp tục giúp tôi từ đây."*
> Mọi thông tin dưới đây đúng đến ngày 03/11/2026. Những gì làm sau ngày đó cần bổ sung thêm.

---

## 1. Đề tài và nhóm

- **Đề tài:** Thiết bị đeo tay giám sát sức khỏe người cao tuổi (hệ thống giám sát sinh hiệu IoT).
  Đo nhịp tim, SpO2, nhiệt độ da, ECG 1 chuyển đạo, phát hiện té ngã, nút SOS; cảnh báo người thân qua
  app Android, SMS (kèm vị trí GPS) và web. Huyết áp (PAT) chỉ là **hướng phát triển**.
- **Đối tượng chính:** người cao tuổi sống một mình. Nguyên mẫu nghiên cứu, **không phải thiết bị y tế**.
- **Ngành:** Điện tử – Viễn thông. Nhóm 2 người:
  - **SV1 = MINH:** phần cứng + firmware (đang làm phần lớn việc).
  - **SV2:** phần mềm (app, web, thuật toán Python).
- Ngân sách dự kiến 5–8 triệu VND. Nhóm có mỏ hàn, máy khò, đồng hồ vạn năng, điện thoại Android.
- Máy tính MINH: Windows, thư mục code `C:\DoAnTotNghiep`, Arduino IDE 2, KiCad 10.

## 2. Hạn chót và mốc

| Mốc | Hạn | Nội dung | Trạng thái |
|---|---|---|---|
| M1 | 11/10/2026 | Đề cương, đặt linh kiện | Trễ, đã xong |
| M2 | 01/11/2026 | Breadboard đo đủ qua BLE, đặt mạch | Gần xong (đã gửi Gerber 01/11) |
| M3 | 22/11/2026 | Thiết bị đeo tay chạy ổn định 24 giờ | Chưa |
| M4 | 06/12/2026 | Gửi bản thảo báo cáo đầy đủ cho GVHD | Chưa |
| **NỘP** | **Thứ Hai 14/12/2026** | Nộp báo cáo | Ngày bảo vệ **chưa công bố** |

## 3. Kiến trúc hệ thống (đã chốt 21/10)

```
Đồng hồ (XIAO nRF52840 Sense + MAX30102 + AD8232 + MAX30205 + màn GC9A01 + motor + nút SOS)
   │ BLE (tên "DoAn-SucKhoe")
   ▼
App Android Flutter trên điện thoại người già ──► gửi SMS (kèm link Google Maps) cho người thân
   │ Internet
   ▼
Firebase Realtime Database (project "dong-ho-suc-khoe", asia-southeast1)
   ▼
Web cho người thân (React, GitHub Pages)
```

- **Không dùng module SIM/4G** (A7670C tốn pin, SIM800L 2G sắp tắt ở VN).
- **Không dùng server FastAPI** (README cũ còn ghi, đã thay bằng Firebase).
- **Giới hạn phải ghi trong báo cáo:** điện thoại phải ở gần (~10 m) và app phải chạy nền thì mới cảnh báo được.

## 4. Phần cứng (phương án cuối, chốt 19/10)

Mạch PCB 2 lớp **ghép module**, làm ở xưởng trong nước (không đặt JLCPCB). Bản mạch chip rời 40×40 mm cũ
giữ trong repo (`hardware/pcb/`) làm "hướng phát triển".

| Khối | Linh kiện | Ghi chú |
|---|---|---|
| Vi điều khiển + BLE + IMU | Seeed XIAO nRF52840 Sense | IMU LSM6DS3 ở Wire1 (bên trong) |
| PPG (nhịp tim, SpO2) | Module MAX30102 **đen 2×4 (HW-605)**, I2C 0x57 | Không có LED xanh lá, đo ở cổ tay nhiễu hơn |
| ECG | Module AD8232 + cáp 3 điện cực | **Màu dây không chuẩn: đỏ = RA, XANH LÁ = LA, VÀNG = RL** |
| Nhiệt độ da | Module MAX30205 (CJMCU-30205), I2C 0x48 | Chỉ cấp 3,3 V; A0–A2 phải nối GND |
| Màn hình | GC9A01 tròn 1,28" | Bản MINH có là **loại 7 chân, không có BLK** (đèn nền luôn sáng) |
| Rung | Motor 1027 qua MOSFET AO3400A | Lấy nguồn VBAT |
| Nút | Nút SOS (6×6×7,5 mm, chân vuông góc) | |
| Pin | LiPo 603040, 600 mAh, có mạch bảo vệ | Đo thật: **45 × 30 × 5,5 mm** tính cả PCM, dây đỏ/đen trần (hàn vào J3) |
| Sạc | Cặp đầu pogo nam châm 2 chân (mặt phẳng phía đồng hồ → J2) | Qua diode SS14 vào chân 5V |

TMP117 và DS18B20 **đã bỏ**.

### Gán chân XIAO (mạch 1.3 và firmware)

| Chân | Chức năng |
|---|---|
| D0 (A0) | ECG OUTPUT của AD8232 |
| D1 | ECG_LOD: LO+ và LO- gộp qua 2 diode 1N4148WS (D1 = 1 khi tuột điện cực) |
| D2 | MOTOR_EN (cổng AO3400A qua 100 Ω, 100k kéo xuống) |
| D3 | TFT_BLK đèn nền (bỏ trống với màn 7 chân) |
| D4 / D5 | I2C SDA / SCL (MAX30102 + MAX30205) |
| D6 / D7 | TFT DC / CS |
| D8 / D10 | TFT SCK / MOSI |
| D9 | Nút SOS (nối GND, INPUT_PULLUP) |
| RES màn | Không dùng GPIO: R 10k kéo lên + tụ 100 nF; firmware RST = -1 |

**Lưu ý quan trọng:** `SPI.begin()` đặt D9 thành pull-down, nên firmware phải bật lại `INPUT_PULLUP` cho D9 sau `tft.begin()` (đã làm).

### Đấu breadboard hiện tại (28/10)
AD8232: OUTPUT→D0, LO+→D1, LO- và SDN để trống. GC9A01: SCL→D8, SDA→D10, CS→D7, DC→D6, RES→3V3.
MAX30102 và MAX30205: SDA D4, SCL D5, tất cả cấp **3V3 (không bao giờ 5V)**. SOS D9→GND.
Motor chỉ qua mạch lái AO3400 ở D2, không nối thẳng GPIO.

## 5. Mạch PCB

- **Bản cuối: v1.3** (PR #21, #22 đã merge). 2 lớp, 50 × 62 mm, 4 lỗ M2 (2,2 mm không mạ), ERC/DRC 0 lỗi.
  Vùng pin 45 × 30, đầu PCM pin ở bên TRÁI gần J3. Theo quy tắc xưởng (mũi khoan 0,3/0,8/1,0; pad = lỗ + 0,6).
- File: KiCad `hardware/pcb_module/dong_ho_module.kicad_pro` (giữ nguyên thư mục `lib/`), xuất trong
  `hardware/pcb_module/xuat/`. Gerber cuối: `C:\DoAnTotNghiep\gerber_dong_ho_module.zip` (106 136 byte),
  bản sao trong thư mục `pcb-module-v1.3/` của dự án và thư mục Drive "05".
- **01/11: MINH đã gửi Gerber cho xưởng.** Báo giá 450k (chọn 5 tấm / 14 ngày), dự kiến về khoảng **13–15/11**.
  Yêu cầu xưởng: thiếc không chì (HASL) hoặc ENIG.
- Khi hàn: cắt chân MAX30102 sát mặt mạch, dán Kapton + mút trước khi đặt pin (U2 nằm trong vùng pin).
- Hướng dẫn hàn Bước 1 (hàn thẳng XIAO, tháo giắc AD8232): thư mục `huong-dan/han-xiao-thang/` của dự án.

## 6. Vỏ đồng hồ (in 3D, CadQuery)

- Script `hardware/enclosure/cong_cu/vo_dong_ho.py`, nhánh git `claude/vo-dong-ho-v1` (**chưa có PR, chưa vào main**).
- **v3 là bản mới nhất (02/11):** 54,9 × 66,9 × **17,8 mm**, màn ở giữa mặt, vít M2 × 14 mm.
  Chỉ lắp vừa khi đã **hàn XIAO thẳng vào mạch (không header cái) và tháo giắc 3,5 mm + chân của AD8232**.
  Cửa sổ MAX30102 dùng tấm trong 0,5–0,7 mm. File: thư mục `vo-dong-ho-v3/` của dự án, Desktop `vo_dong_ho_v3`.
- v2 (26,1 mm, giữ header) vẫn còn nếu không hàn thẳng.
- Còn mở: kích thước đầu pogo (đang là ô giữ chỗ), thử lại BLE sau khi lắp (màn gần anten).
  Pin mỏng hơn (vd. 403040) sẽ làm vỏ mỏng gần 1:1, nhưng pin phải ≤ 30 rộng và ≤ 45 dài tính cả PCM.

## 7. Firmware (`firmware/` trong repo)

- **Sketch chính: `firmware/ble_suc_khoe`**. Gửi số đo mỗi giây qua BLE; SOS giữ 1 giây; té ngã có 15 giây để huỷ;
  cảnh báo chỉ số bất thường sau 15 giây; cảnh báo gửi lại đến khi app xác nhận; màn GC9A01 (chỉ số, giờ HH:MM,
  đếm ngược té ngã, SOS, "DA BAO"), tắt màn sau 10 giây, bấm nhanh SOS để bật lại; ECG 30 giây 250 Hz theo lệnh app;
  đồng bộ giờ từ app (lệnh 05). Biên dịch trên máy MINH: Flash 21%, RAM 10%.
- Giao thức BLE chi tiết: `docs/giao-thuc-ble.md` (service `4b3a0001-8f6e-4c2a-9d1b-3e5f7a9c0b1d`, ECG char `4b3a0005`).
- Sketch phụ: `test_breadboard` (kiểm tra từng module), `kiem_tra_chan` (kiểm tra chập chân D0–D10),
  `ghi_imu` (ghi IMU 100 Hz cho té ngã), `doc_max30102`, `doc_ad8232`, `kiem_tra_xiao_sense`. Xem sóng ECG: `huong-dan/xem-song-ecg/`.
- Gói board: **Seeed nRF52 Boards 1.1.13** (không dùng bản mbed). Thư viện: SparkFun MAX3010x, Adafruit GC9A01A + GFX,
  Seeed Arduino LSM6DS3 (đã cài trên máy MINH).
- **Lỗi nhịp tim = 0 đã sửa xong** (PR #25, #26, #27 đều đã merge 01/11): đọc thẳng FIFO MAX30102, tự giải phóng I2C bị treo,
  sửa phép trừ thời gian bị tràn. Thử thật: HR 82–90 sau ~9 giây, SpO2 93–97. Ngón tay phải để yên 10–15 giây.
- Thuật toán té ngã (`algorithm/te_nga/`): va chạm > 2,5 g, có lúc < 0,75 g trong 1 s trước, nằm yên 1–3 s sau,
  đổi tư thế > 30°. Mới dựa trên ít dữ liệu ngã thật. Thả sách lên đệm thì báo, lắc tay thì không (đúng thiết kế).
- **SpO2 dùng công thức 110 − 25R chưa hiệu chuẩn.** Dòng sạc pin vẫn mặc định 50 mA.

## 8. App Android và web

- **App Flutter** `app/suc_khoe/` (PR #14): kết nối BLE, hiện chỉ số, trang người thân, gửi SMS kèm GPS, tab Web,
  màn ECG 30 giây, tải ECG lên Firebase (PR #24), gửi giờ cho đồng hồ.
  **APK build tự động trên GitHub Actions** (artifact "app-suc-khoe-apk"). Mỗi bản APK có chữ ký khác nên phải
  **gỡ app cũ trước khi cài bản mới**.
- **Web người thân** `web/` (React + Vite + Firebase): https://doantheodoisuckhoe.github.io/Thietbitheodoisuckhoe/
  (cần đăng nhập; xem dữ liệu mẫu bằng `?demo`, té ngã mẫu `?demo=nga`). Có mục ECG và nút "Tải CSV cho bác sĩ".
  Cấu hình Firebase ở `web/src/cauHinhFirebase.js`. Quy tắc DB ở `web/database.rules.json` (phải dán vào Firebase
  Console > Realtime Database > Rules > Publish khi thay đổi). App và web dùng chung 1 tài khoản email/mật khẩu của gia đình.
- **01/11: SMS đầu-cuối chạy được** (điện thoại 2 SIM, phải chọn SIM mặc định có tiền).
- Lỗi còn biết: app vẫn xác nhận cảnh báo với đồng hồ kể cả khi gửi SMS thất bại (đề xuất sửa, nhắn "sửa SMS").

## 9. Kết quả thử trên bàn (đã kiểm chứng)

- 17/10: XIAO qua toàn bộ test (nạp code, Serial, IMU, mic, LED, BLE).
- 24/10: cả 4 module chạy trên breadboard với người thật: MAX30102 nhận ngón tay, MAX30205 đọc nhiệt độ,
  AD8232 ra sóng ECG thật (~75–88 bpm), IMU OK.
- 01/11: màn 7 chân hiện đủ trên breadboard; té ngã kích hoạt; SMS gửi được; nhịp tim hoạt động sau PR #27.
- Chưa làm: đo dòng tiêu thụ thật (ước tính màn 7 chân ~1 ngày pin, màn có BLK 2–3 ngày), thử ECG 30 s trên người,
  kiểm tra điện áp pin, thử trên mạch PCB thật.

## 10. Việc còn lại (theo kế hoạch 7 tuần)

Kế hoạch đầy đủ có tick: `ke-hoach/Viec_con_lai_de_hoan_tat_do_an.md` và các checklist trên Trello.

- **Tuần 5 (02–08/11):** mua máy SpO2 Jumper JPD-500E, nhiệt kế Omron MC-246, điện cực ECG; thử cảnh báo thật
  và Firebase/web; hiệu chuẩn SpO2; chuẩn bị hàn mạch.
- **Khi mạch về (~13–15/11):** đo chập 3V3–GND, VBAT–GND; hàn linh kiện nhỏ → XIAO (thẳng) → module → màn,
  motor, SOS, pogo; chạy `kiem_tra_chan` và `test_breadboard` trên mạch; in vỏ v3.
- **Tuần 6:** đo pin thật, thêm chế độ ngủ; thu thêm dữ liệu té ngã; chỉnh ngưỡng sốt (da cổ tay thấp hơn thân nhiệt 3–4 °C);
  mời ~10 người tình nguyện.
- **Tuần 7 (M3, 22/11):** lắp vào vỏ, đeo thử 24 giờ, quay video demo dự phòng; viết chương 4.
- **Tuần 8:** đo trên ~10 người so với máy đối chứng (Bland-Altman), độ trễ cảnh báo, tầm BLE; viết chương 5.
- **Tuần 9 (M4, 06/12):** chương 6, rà chương 1–3 cho khớp phương án cuối, thay số ước lượng bằng số đo, điền bìa, gửi GVHD.
- **Tuần 10:** sửa theo góp ý, in nộp **14/12**, làm slide 15–20 trang, tập bảo vệ.
- Phương án dự phòng: nếu mạch lỗi/về trễ thì demo và kiểm chứng bằng bản breadboard.
- Cần xin GVHD đồng ý các thay đổi: mạch module ở xưởng trong nước, MAX30205 thay TMP117, Firebase thay FastAPI,
  huyết áp thành hướng phát triển.

### Còn phải mua (~1,56 triệu, cập nhật 27/10)
Tiền mạch (đã đặt), in 3D ×3, máy SpO2 Jumper, nhiệt kế Omron, 50 miếng điện cực ECG, ốc M2 × 14 mm, dây 30AWG,
dây đeo 22 mm, tấm trong 0,5–0,7 mm, Kapton/băng keo 2 mặt, thước kẹp (tuỳ chọn).
Danh sách: `mua-linh-kien/Danh_sach_linh_kien_phuong_an_cuoi.xlsx`.

## 11. Báo cáo

- Bản viết lại: `bao-cao/KLTN_He_thong_giam_sat_sinh_hieu_IoT_viet_lai.docx` (71 trang, chương 1–3, tóm tắt, mục lục,
  25 hình, 25 bảng, 28 tài liệu tham khảo). **Chưa có chương 4–6.** Số liệu pin và SpO2 trong đó là ước tính.
  Bìa còn để trống (họ tên, MSSV, GVHD, ngày). Trường không có mẫu báo cáo.
- Ý cho "hướng phát triển": mạch chip rời, màn cảm ứng, huyết áp PAT, module 4G.

## 12. Đường link quan trọng

| Nội dung | Link |
|---|---|
| Code (GitHub) | https://github.com/Doantheodoisuckhoe/Thietbitheodoisuckhoe |
| Web người thân | https://doantheodoisuckhoe.github.io/Thietbitheodoisuckhoe/ |
| Trello: thẻ tổng hợp link | https://trello.com/c/VCfNPa8S |
| Trello: báo cáo tiến độ tuần | https://trello.com/c/aRlWOzxR |
| Drive: tài liệu tham khảo | https://drive.google.com/drive/folders/1KZiBtmnpmvr8I5NB946miolWTgPeUy9S |
| Drive Doc kế hoạch 7 tuần | https://docs.google.com/document/d/1fNbqSEm2sRJk4BUnvS5IAONoEhMS-WrxbYqwmsHTncg |
| Firebase | project "dong-ho-suc-khoe" (console.firebase.google.com) |

Drive có 6 thư mục: 01 Tài liệu tham khảo, 02 Dữ liệu đo, 03 Báo cáo và slide, 04 Hình ảnh video,
05 Mạch và vỏ, 06 Hành chính. Gerber zip và file báo cáo docx cần tự kéo thả lên Drive (nếu chưa).

## 13. Pull request trên GitHub

Đã merge: #3 test XIAO, #4–#5 té ngã, #7 mạch module, #8 test breadboard, #9–#10 kiểm tra chân, #11 BLE sức khỏe,
#13 nhịp tim, #14 app, #15 web, #16 mạch 1.1, #17 mạch 1.2, #18 màn GC9A01, #19 ECG 30 s, #21–#22 mạch 1.3,
#23 xem giờ, #24 ECG từ xa, #25–#27 sửa nhịp tim.
**Còn mở:** #20 sơ đồ breadboard 28/10. **Chưa có PR:** nhánh `claude/vo-dong-ho-v1` (vỏ v1–v3).

## 14. Quy ước làm việc

- MINH làm trên nhánh `main`. Sau khi làm trên nhánh khác (claude/...) phải chuyển thư mục `C:\DoAnTotNghiep` về `main`
  (`git checkout main` rồi `git pull`), nếu không `git pull` sẽ không thấy file mới.
- Tên file, biến, thư mục viết tiếng Việt không dấu (vd. `ble_suc_khoe`, `man_hinh.h`).
- MINH thích sơ đồ breadboard **kiểu khối**, không phải kiểu đánh số từng lỗ.
- Báo cáo tiến độ đăng tối Chủ Nhật lên Trello; đánh giá theo kế hoạch hiện tại, không theo tên thẻ cũ (JLCPCB, TMP117, FastAPI đã bỏ).
- Máy đối chứng: máy SpO2 kẹp ngón (đồng hồ thông minh không đủ tin cậy), nhiệt kế Omron, máy huyết áp bắp tay đã có.
