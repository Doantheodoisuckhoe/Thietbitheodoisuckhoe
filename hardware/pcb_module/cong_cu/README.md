# Công cụ tạo mạch tự động

Các script đã dùng để tạo lần đầu sơ đồ, footprint và PCB của bản module (chạy bằng Python đi kèm KiCad 10):

| Script | Việc |
|---|---|
| `gen_fp.py` | Ghi footprint riêng vào `../lib/DoAnModule.pretty/` |
| `gen_sch.py` | Ghi `../lib/DoAnModule.kicad_sym` và sơ đồ `../dong_ho_module.kicad_sch` |
| `gen_pcb.py <netlist>` | Đặt linh kiện, đi dây bằng bộ định tuyến lưới kiểu PathFinder (0,2 mm), đổ GND hai lớp |
| `sexp.py` | Đọc/ghi s-expression của KiCad |

```
"C:\Program Files\KiCad\10.0\bin\python.exe" gen_fp.py
"C:\Program Files\KiCad\10.0\bin\python.exe" gen_sch.py
kicad-cli sch export netlist -o net.net ..\dong_ho_module.kicad_sch
"C:\Program Files\KiCad\10.0\bin\python.exe" gen_pcb.py net.net
kicad-cli pcb drc --schematic-parity --refill-zones --save-board ..\dong_ho_module.kicad_pcb
```

**Chạy lại sẽ ghi đè file KiCad.** Khi đã sửa tay trong KiCad thì sửa tiếp trong KiCad, không chạy lại các script này.
