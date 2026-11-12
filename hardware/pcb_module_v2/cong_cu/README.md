# Công cụ tạo mạch tự động (bản 2.0)

Các script đã dùng để tạo sơ đồ, footprint và PCB bản 2.0 (chạy bằng Python đi kèm KiCad 10). Lấy từ
`../../pcb_module/cong_cu/` (bản 1.3) rồi sửa cho bản không dây nối.

| Script | Việc |
|---|---|
| `kich_thuoc.py` | Kích thước đo trên module thật (AD8232, GC9A01, XIAO, pin, motor, nút). Các script khác đọc từ đây |
| `gen_fp.py` | Ghi footprint riêng vào `../lib/DoAnModule.pretty/` |
| `gen_sch.py` | Ghi `../lib/DoAnModule.kicad_sym` và sơ đồ `../dong_ho_module_v2.kicad_sch` |
| `gen_pcb.py <netlist> [--giu-day <bảng cũ>]` | Đặt linh kiện (bảng `PLACE`), đi dây bằng bộ định tuyến lưới kiểu PathFinder (0,2 mm, ~20 phút), đổ GND hai lớp. `--giu-day`: không đi dây lại, chép nguyên dây/via từ bảng cũ (khi chỉ sửa chữ lụa, footprint) |
| `sua_sau_di_day.py` | Sửa nhỏ sau đi dây: nối 2 pad "1" của nút SOS, bỏ via GND lơ lửng, đưa tên U1/U3 sang lớp Fab |
| `ap_quy_tac_xuong.py` | Áp tiêu chuẩn xưởng lên mạch đã đi dây (mũi khoan, pad = lỗ + 0,6, via 0,3/0,9, phủ đồng 0,65 mm, chữ lụa 0,2 mm) |
| `kiem_tra_kich_thuoc.py` | Kiểm tra tự động: khoảng cách mọi cặp pad AD8232, bước pad và tâm màn GC9A01, hai hàng XIAO 15,24 mm, anten sát mép, pin không đè XIAO, pad AD8232 cách pin, không chân xuyên lỗ nằm dưới module mặt da / motor, màn không che nút SOS và pad RA. Thoát mã 1 nếu sai |
| `ve_chong_tang.py` | Vẽ `../xuat/pcb_chong_tang_module.png`: viền các module chồng lên mạch theo 3 tầng |
| `sexp.py` | Đọc/ghi s-expression của KiCad |

```
set PY="C:\Program Files\KiCad\10.0\bin\python.exe"
%PY% gen_fp.py
%PY% gen_sch.py
kicad-cli sch export netlist -o net.net ..\dong_ho_module_v2.kicad_sch
%PY% gen_pcb.py net.net
%PY% sua_sau_di_day.py
%PY% ap_quy_tac_xuong.py
%PY% kiem_tra_kich_thuoc.py
kicad-cli pcb drc --schematic-parity --refill-zones --save-board ..\dong_ho_module_v2.kicad_pcb
%PY% ve_chong_tang.py
```

**Chạy lại sẽ ghi đè file KiCad.** Khi đã sửa tay trong KiCad thì sửa tiếp trong KiCad, không chạy lại
`gen_*.py` (`kiem_tra_kich_thuoc.py` và `ve_chong_tang.py` chỉ đọc, chạy lúc nào cũng được).
