# Sinh footprint riêng cho bản mạch module
import os, uuid
OUT = r'C:\DoAnTotNghiep\hardware\pcb_module\lib\DoAnModule.pretty'
NS = uuid.UUID('0b7c2f8e-3a55-4d0e-9a3b-5c1d2e3f4a5b')
n = [0]
def u():
    n[0] += 1
    return str(uuid.uuid5(NS, str(n[0])))

def q(s):
    return '"' + s.replace('"', '\\"') + '"'

def line(x1, y1, x2, y2, layer, w):
    return f'(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (layer {q(layer)}) (uuid {q(u())}))'

def rect(x1, y1, x2, y2, layer, w, fill=False):
    f = 'yes' if fill else 'no'
    return f'(fp_rect (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (fill {f}) (layer {q(layer)}) (uuid {q(u())}))'

def circle(cx, cy, r, layer, w):
    return f'(fp_circle (center {cx:.3f} {cy:.3f}) (end {cx + r:.3f} {cy:.3f}) (stroke (width {w}) (type solid)) (fill no) (layer {q(layer)}) (uuid {q(u())}))'

def text(s, x, y, layer, size=0.8, th=0.12, just=None, rot=0):
    j = f' (justify {just})' if just else ''
    return f'(fp_text user {q(s)} (at {x:.3f} {y:.3f} {rot}) (layer {q(layer)}) (uuid {q(u())}) (effects (font (size {size} {size}) (thickness {th})){j}))'

def tht(num, x, y, d=1.8, drill=1.0, square=False):
    shp = 'rect' if square else 'circle'
    return f'(pad {q(num)} thru_hole {shp} (at {x:.3f} {y:.3f}) (size {d} {d}) (drill {drill}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid {q(u())}))'

def footprint(name, descr, tags, ref_xy, val_xy, body, attr='through_hole'):
    s = f'''(footprint {q(name)} (version 20241229) (generator "pcbnew") (generator_version "9.0") (layer "F.Cu")
 (descr {q(descr)}) (tags {q(tags)})
 (property "Reference" "REF**" (at {ref_xy[0]} {ref_xy[1]} 0) (layer "F.SilkS") (uuid {q(u())}) (effects (font (size 1 1) (thickness 0.15))))
 (property "Value" {q(name)} (at {val_xy[0]} {val_xy[1]} 0) (layer "F.Fab") (uuid {q(u())}) (effects (font (size 1 1) (thickness 0.15))))
 (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(u())}) (effects (font (size 1.27 1.27) (thickness 0.15))))
 (property "Description" {q(descr)} (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(u())}) (effects (font (size 1.27 1.27) (thickness 0.15))))
 (attr {attr})
 {chr(10).join(body)}
 (embedded_fonts no))
'''
    with open(os.path.join(OUT, name + '.kicad_mod'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)

P = 2.54

# 1) Đế cắm XIAO: chân 1 (D0) ở đầu USB, chân 1-7 cột trái, 8-14 cột phải đi ngược lên
b = []
for i in range(7):
    b.append(tht(str(i + 1), 0, i * P, 1.7, 1.0, square=(i == 0)))
    b.append(tht(str(8 + i), 15.24, (6 - i) * P, 1.7, 1.0))
x1, x2, y1, y2 = -1.28, 16.52, -2.93, 18.12
b.append(rect(x1, y1, x2, y2, 'F.Fab', 0.1))
b.append(rect(3.4, y1 - 1.5, 11.84, y1, 'F.Fab', 0.1))
b.append(text('USB-C', 7.62, y1 + 1.2, 'F.Fab', 0.8))
b.append(text('ANTEN', 7.62, y2 - 1.2, 'F.Fab', 0.8))
b.append(text('${REFERENCE}', 7.62, 7.62, 'F.Fab', 1.0))
# lụa: chỉ hai cạnh dọc (đầu anten nằm sát mép bảng, đầu USB có tụ nằm dưới thân XIAO)
b.append(line(x1 + 0.2, y1 + 0.2, x1 + 0.2, y2 - 0.2, 'F.SilkS', 0.12))
b.append(line(x2 - 0.2, y1 + 0.2, x2 - 0.2, y2 - 0.2, 'F.SilkS', 0.12))
for x in (0, 15.24):
    b.append(rect(x - 1.52, -1.52, x + 1.52, 6 * P + 1.52, 'F.CrtYd', 0.05))
footprint('XIAO_nRF52840_DeCam_2x7_P2.54_15.24mm',
          'Seeed XIAO nRF52840 (Sense) cắm trên 2 header cái 1x7 2,54 mm, hai hàng cách 15,24 mm. Chân 1 = D0 ở đầu USB-C; đầu kia là anten.',
          'XIAO nRF52840 socket', (7.62, -5.0), (7.62, 20.0), b)

# 2) Module MAX30102 tím: 1x7 dọc mép, thân ~21x16 mm (kiểm tra lại)
b = []
for i in range(7):
    b.append(tht(str(i + 1), i * P, 0, 1.8, 1.0, square=(i == 0)))
x1, x2, y1, y2 = -2.88, 18.12, -1.5, 14.5
b.append(rect(x1, y1, x2, y2, 'F.Fab', 0.1))
b.append(rect(x1 - 0.12, y1 - 0.12, x2 + 0.12, y2 + 0.12, 'F.SilkS', 0.12))
b.append(rect(x1 - 0.25, y1 - 0.25, x2 + 0.25, y2 + 0.25, 'F.CrtYd', 0.05))
b.append(rect(7.62 - 2.8, 7 - 1.65, 7.62 + 2.8, 7 + 1.65, 'F.Fab', 0.1))
b.append(circle(7.62, 7, 3.5, 'F.SilkS', 0.12))
for i, nm in enumerate(['VIN', 'SCL', 'SDA', 'INT', 'IRD', 'RD', 'GND']):
    b.append(text(nm, i * P, 1.9, 'F.Fab', 0.6, 0.09))
b.append(text('${REFERENCE}', 7.62, 11.5, 'F.Fab', 1.0))
footprint('Module_MAX30102_1x7',
          'Module MAX30102 (tím) gắn mặt cảm biến hướng ra ngoài, header 1x7 2,54 mm: VIN SCL SDA INT IRD RD GND. Kích thước thân 21x16 mm là ước lượng, đo lại module thật.',
          'MAX30102 module', (7.62, -3.0), (7.62, 16.0), b)

# 3) Module CJMCU-30205: 1x8, thân ~22x13 mm (kiểm tra lại)
b = []
for i in range(8):
    b.append(tht(str(i + 1), i * P, 0, 1.8, 1.0, square=(i == 0)))
x1, x2, y1, y2 = -2.11, 19.89, -1.5, 11.5
b.append(rect(x1, y1, x2, y2, 'F.Fab', 0.1))
b.append(rect(x1 - 0.12, y1 - 0.12, x2 + 0.12, y2 + 0.12, 'F.SilkS', 0.12))
b.append(rect(x1 - 0.25, y1 - 0.25, x2 + 0.25, y2 + 0.25, 'F.CrtYd', 0.05))
b.append(rect(8.89 - 1.5, 6 - 1.5, 8.89 + 1.5, 6 + 1.5, 'F.Fab', 0.1))
b.append(circle(8.89, 6, 2.5, 'F.SilkS', 0.12))
for i, nm in enumerate(['VCC', 'GND', 'SDA', 'SCL', 'OS', 'A0', 'A1', 'A2']):
    b.append(text(nm, i * P, 1.9, 'F.Fab', 0.6, 0.09))
b.append(text('${REFERENCE}', 8.89, 9.8, 'F.Fab', 1.0))
footprint('Module_CJMCU-30205_1x8',
          'Module CJMCU-30205 (MAX30205) gắn mặt cảm biến hướng ra da, header 1x8 2,54 mm: VCC GND SDA SCL OS A0 A1 A2. Kích thước thân 22x13 mm là ước lượng, đo lại module thật.',
          'MAX30205 CJMCU-30205 module', (8.89, -3.0), (8.89, 13.0), b)

# 4) Pad hàn dây module AD8232: lưới 3x3
def grid(name, descr, tags, cols, labels, rows_lbl, lbl_size):
    b = []
    nrow = (len(labels) + cols - 1) // cols
    for k in range(len(labels)):
        c, r = k % cols, k // cols
        b.append(tht(str(k + 1), c * P, r * P, 1.8, 1.0, square=(k == 0)))
    w = (cols - 1) * P
    h = (nrow - 1) * P
    b.append(rect(-1.2, -1.2, w + 1.2, h + 1.2, 'F.CrtYd', 0.05))
    b.append(rect(-1.1, -1.1, w + 1.1, h + 1.1, 'F.Fab', 0.1))
    for r, s in enumerate(rows_lbl):
        b.append(text(s, w + 1.4, r * P, 'F.SilkS', lbl_size, 0.12, 'left'))
    b.append(text('${REFERENCE}', w / 2, h / 2, 'F.Fab', 0.8))
    footprint(name, descr, tags, (w / 2, -2.2), (w / 2, h + 2.2), b)

# Pad hàn dây: lưới bước 3,0 mm để dây mạch đi lọt giữa các pad (dây điện không cần bước 2,54)
def wiregrid(name, descr, cols, labels, label_mode):
    b = []
    PP = 3.0
    nrow = (len(labels) + cols - 1) // cols
    for k, nm in enumerate(labels):
        c, r = k % cols, k // cols
        b.append(tht(str(k + 1), c * PP, r * PP, 1.8, 1.0, square=(k == 0)))
        if label_mode == 'below':
            b.append(text(nm, c * PP, r * PP + 1.55, 'F.SilkS', 0.6, 0.1))
    w, h = (cols - 1) * PP, (nrow - 1) * PP
    if label_mode == 'right':
        for r in range(nrow):
            b.append(text(' '.join(labels[r * cols:(r + 1) * cols]), w + 1.3, r * PP, 'F.SilkS', 0.8, 0.12, 'left'))
    b.append(rect(-1.2, -1.2, w + 1.2, h + 1.2, 'F.CrtYd', 0.05))
    b.append(rect(-1.1, -1.1, w + 1.1, h + 1.1, 'F.Fab', 0.1))
    b.append(text('${REFERENCE}', w / 2, h / 2, 'F.Fab', 0.8))
    footprint(name, descr, name, (w / 2, -2.2), (w / 2, h + 2.4), b)

wiregrid('DayNoi_AD8232_3x3_P3.0', 'Pad hàn dây sang module AD8232, bước 3 mm: 1 GND, 2 3V3, 3 OUTPUT, 4 LO-, 5 LO+, 6 SDN, 7 RA, 8 LA, 9 RL',
         3, ['GND', '3V3', 'OUT', 'LO-', 'LO+', 'SDN', 'RA', 'LA', 'RL'], 'below')
wiregrid('DayNoi_GC9A01_2x4_P3.0', 'Pad hàn dây sang màn GC9A01, bước 3 mm: 1 VCC, 2 GND, 3 SCL, 4 SDA, 5 RES, 6 DC, 7 CS, 8 BLK',
         2, ['VCC', 'GND', 'SCL', 'SDA', 'RES', 'DC', 'CS', 'BLK'], 'right')

# 5) Điện cực ECG: pad đồng lộ (không phủ mask, không kem hàn), đặt ở mặt dưới
b = []
W, H = 9, 16
b.append(f'(pad "1" smd roundrect (at 0 0) (size {W} {H}) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.15) (zone_connect 2) (uuid {q(u())}))')
b.append(rect(-W / 2 - 0.25, -H / 2 - 0.25, W / 2 + 0.25, H / 2 + 0.25, 'F.CrtYd', 0.05))
b.append(rect(-W / 2, -H / 2, W / 2, H / 2, 'F.Fab', 0.1))
b.append(text('${REFERENCE}', 0, 0, 'F.Fab', 1.0))
footprint('DienCuc_ECG_9x16mm',
          'Điện cực ECG: pad đồng 9x16 mm lộ đồng (mở mask), đặt ở mặt da. Nên mạ ENIG hoặc HASL.',
          'ECG electrode', (0, -H / 2 - 1.5), (0, H / 2 + 1.5), b, attr='smd exclude_from_pos_files exclude_from_bom')
print('ok')
