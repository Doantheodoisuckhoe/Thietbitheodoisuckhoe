# Sinh footprint riêng cho bản mạch module 2.0 (không dây nối)
import os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kich_thuoc import *
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib', 'DoAnModule.pretty')
NS = uuid.UUID('0b7c2f8e-3a55-4d0e-9a3b-5c1d2e3f4a5b')
n = [0]
def u():
    n[0] += 1
    return str(uuid.uuid5(NS, str(n[0])))

def q(s):
    return '"' + s.replace('"', '\\"') + '"'

# Tiêu chuẩn xưởng (bản 1.2): pad = lỗ + 0,6 mm; lụa: chữ >= 0,8 mm, nét chữ 0,2 mm, nét vẽ >= 0,15 mm
def lua_w(layer, w):
    return max(w, 0.15) if 'SilkS' in layer else w

def line(x1, y1, x2, y2, layer, w):
    w = lua_w(layer, w)
    return f'(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (layer {q(layer)}) (uuid {q(u())}))'

def rect(x1, y1, x2, y2, layer, w, fill=False):
    w = lua_w(layer, w)
    f = 'yes' if fill else 'no'
    return f'(fp_rect (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (fill {f}) (layer {q(layer)}) (uuid {q(u())}))'

def circle(cx, cy, r, layer, w):
    w = lua_w(layer, w)
    return f'(fp_circle (center {cx:.3f} {cy:.3f}) (end {cx + r:.3f} {cy:.3f}) (stroke (width {w}) (type solid)) (fill no) (layer {q(layer)}) (uuid {q(u())}))'

def text(s, x, y, layer, size=0.8, th=0.12, just=None, rot=0):
    if 'SilkS' in layer:
        size, th = max(size, 0.8), 0.2
    j = f' (justify {just})' if just else ''
    return f'(fp_text user {q(s)} (at {x:.3f} {y:.3f} {rot}) (layer {q(layer)}) (uuid {q(u())}) (effects (font (size {size} {size}) (thickness {th})){j}))'

def tht(num, x, y, d=1.6, drill=1.0, square=False):
    shp = 'rect' if square else 'circle'
    return f'(pad {q(num)} thru_hole {shp} (at {x:.3f} {y:.3f}) (size {d} {d}) (drill {drill}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid {q(u())}))'

def footprint(name, descr, tags, ref_xy, val_xy, body, attr='through_hole'):
    s = f'''(footprint {q(name)} (version 20241229) (generator "pcbnew") (generator_version "9.0") (layer "F.Cu")
 (descr {q(descr)}) (tags {q(tags)})
 (property "Reference" "REF**" (at {ref_xy[0]} {ref_xy[1]} 0) (layer "F.SilkS") (uuid {q(u())}) (effects (font (size 1 1) (thickness 0.2))))
 (property "Value" {q(name)} (at {val_xy[0]} {val_xy[1]} 0) (layer "F.Fab") (uuid {q(u())}) (effects (font (size 1 1) (thickness 0.15))))
 (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(u())}) (effects (font (size 1.27 1.27) (thickness 0.15))))
 (property "Description" {q(descr)} (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(u())}) (effects (font (size 1.27 1.27) (thickness 0.15))))
 (attr {attr})
 {chr(10).join(body)}
 (embedded_fonts no))
'''
    with open(os.path.join(OUT, name + '.kicad_mod'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)

# 1) XIAO hàn thẳng lên mạch bằng 2 hàng chân 1x7 của nó (đệm ~2,5 mm): chân 1 (D0) ở đầu USB,
#    chân 1-7 cột trái, 8-14 cột phải đi ngược lên. Courtyard chỉ bao 2 hàng chân: dưới thân XIAO
#    (hở ~2,5 mm) vẫn đặt được tụ 0805.
b = []
for i in range(7):
    b.append(tht(str(i + 1), 0, i * P, 1.6, 1.0, square=(i == 0)))
    b.append(tht(str(8 + i), XIAO_HANG, (6 - i) * P, 1.6, 1.0))
x1, x2, y1, y2 = -1.28, 16.52, -2.93, 18.12
b.append(rect(x1, y1, x2, y2, 'F.Fab', 0.1))
b.append(rect(3.4, y1 - 1.5, 11.84, y1, 'F.Fab', 0.1))
b.append(text('USB-C', 7.62, y1 + 1.2, 'F.Fab', 0.8))
b.append(text('ANTEN', 7.62, y2 - 1.2, 'F.Fab', 0.8))
b.append(text('${REFERENCE}', 7.62, 7.62, 'F.Fab', 1.0))
for x in (0, XIAO_HANG):
    b.append(rect(x - 1.05, -1.05, x + 1.05, 6 * P + 1.05, 'F.CrtYd', 0.05))
footprint('XIAO_nRF52840_DeCam_2x7_P2.54_15.24mm',
          'Seeed XIAO nRF52840 (Sense) hàn thẳng bằng 2 hàng chân 1x7 2,54 mm, hai hàng cách 15,24 mm. Chân 1 = D0 ở đầu USB-C; đầu kia là anten.',
          'XIAO nRF52840', (7.62, -5.0), (7.62, 20.0), b)

# 2) Module MAX30102 đen 2x4 (HW-605): thân 20x15 mm, 2 hàng 4 chân cách nhau 10,16 mm.
#    Gốc toạ độ = tâm cảm biến. Footprint vẽ nhìn từ mặt cảm biến (mặt trên linh kiện).
#    Mặt chữ của module (nhìn từ mặt chữ): hàng A "GND RD IRD INT", hàng B "VIN SDA SCL GND",
#    GND hàng A thẳng cột với VIN hàng B. Nhìn từ mặt cảm biến thì thứ tự trái-phải bị lật.
b = []
ROW_A = [('5', 'GND', 3.81), ('6', 'RD', 1.27), ('7', 'IRD', -1.27), ('8', 'INT', -3.81)]
ROW_B = [('1', 'VIN', 3.81), ('2', 'SDA', 1.27), ('3', 'SCL', -1.27), ('4', 'GND', -3.81)]
for num, nm, x in ROW_A:
    b.append(tht(num, x, -5.08, 1.6, 1.0))
    b.append(text(nm, x, -3.4, 'F.SilkS', 0.6, 0.1))
for num, nm, x in ROW_B:
    b.append(tht(num, x, 5.08, 1.6, 1.0, square=(num == '1')))
    b.append(text(nm, x, 3.4, 'F.SilkS', 0.6, 0.1))
x1, x2, y1, y2 = -10.0, 10.0, -7.5, 7.5
b.append(rect(x1, y1, x2, y2, 'F.Fab', 0.1))
b.append(rect(x1 - 0.12, y1 - 0.12, x2 + 0.12, y2 + 0.12, 'F.SilkS', 0.12))
b.append(rect(x1 - 0.25, y1 - 0.25, x2 + 0.25, y2 + 0.25, 'F.CrtYd', 0.05))
b.append(rect(-2.8, -1.65, 2.8, 1.65, 'F.Fab', 0.1))       # con cảm biến (vị trí ước lượng: giữa module)
b.append(text('${REFERENCE}', 0, 6.4, 'F.Fab', 0.8))
footprint('Module_MAX30102_2x4',
          'Module MAX30102 đen 2 hàng chân (HW-605), thân 20x15 mm, 2x4 chân 2,54 mm, hai hàng cách 10,16 mm. Gắn mặt cảm biến hướng ra da, mặt chữ áp vào mạch. Chân: 1 VIN, 2 SDA, 3 SCL, 4 GND, 5 GND, 6 RD, 7 IRD, 8 INT. Gốc = tâm cảm biến.',
          'MAX30102 module', (0, -9.0), (0, 9.0), b)

# 3) Module CJMCU-30205: 1x8, thân ~22x13 mm (kiểm tra lại)
b = []
for i in range(8):
    b.append(tht(str(i + 1), i * P, 0, 1.6, 1.0, square=(i == 0)))
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

# 4) Module AD8232 cắm thẳng vào mạch qua 9 lỗ (toạ độ đo trên module thật, xem kich_thuoc.py).
#    Module nằm cao ~8,5 mm phía trên pin và XIAO nên courtyard chỉ bao các lỗ chân; viền module vẽ ở F.Fab.
b = []
for num, (nm, x, y) in AD8232_PADS.items():
    b.append(tht(num, x, y, 1.6, 1.0, square=(num == '4')))
    if y == 0:
        b.append(text(nm, x, 1.7, 'F.SilkS', 0.8))
    else:
        b.append(text(nm, 1.2, y, 'F.SilkS', 0.8, just='left'))
b.append(rect(13.97 - 1.05, -1.05, 19.05 + 1.05, 1.05, 'F.CrtYd', 0.05))
b.append(rect(-1.05, 10.033 - 1.05, 1.05, 22.733 + 1.05, 'F.CrtYd', 0.05))
vx1, vy1, vx2, vy2 = AD8232_VIEN
b.append(rect(vx1, vy1, vx2, vy2, 'F.Fab', 0.1))
for (x, y) in AD8232_LO_VIT:
    b.append(circle(x, y, 1.1, 'F.Fab', 0.1))
b.append(text('AD8232 (cao 8,5 mm)', 12.13, 28.0, 'F.Fab', 1.0))
b.append(text('${REFERENCE}', 12.13, 26.0, 'F.Fab', 1.0))
footprint('Module_AD8232_9chan',
          'Module AD8232 đỏ 28x35 mm cắm thẳng vào mạch (header cái/chân đực ~8,5 mm). Gốc = lỗ vít trên-trái. '
          '1 RA, 2 LA, 3 RL (hàng trên); 4 GND, 5 3V3, 6 OUTPUT, 7 LO-, 8 LO+, 9 SDN (cột trái). Tháo giắc 3,5 mm.',
          'AD8232 module', (8.0, -3.4), (12.13, 30.0), b)

# 5) Màn tròn GC9A01 1,28" hàn thẳng vào mạch. Gốc = tâm hình tròn, hàng pad cách tâm 24,7 mm.
#    Pad 1..7: RST CS DC SDA SCL GND VCC (theo bản vẽ, CẦN KIỂM TRA); pad 8 BLK cho module 8 chân.
b = []
for num, (nm, x, y) in GC9A01_PADS.items():
    b.append(tht(num, x, y, 1.6, 1.0, square=(num == '1')))
    b.append(text(nm, x, y - 1.6, 'F.Fab', 0.8, rot=90, just='left'))
b.append(rect(-3 * P - 1.05, GC9A01_HANG - 1.05, 4 * P + 1.05, GC9A01_HANG + 1.05, 'F.CrtYd', 0.05))
b.append(circle(0, 0, GC9A01_R, 'F.Fab', 0.1))
b.append(circle(0, 0, 16.2, 'F.Fab', 0.1))
ytab = GC9A01_DAI - GC9A01_R
b.append(rect(-GC9A01_TAB_W / 2, 14.0, GC9A01_TAB_W / 2, ytab, 'F.Fab', 0.1))
b.append(text('GC9A01 (tầng trên cùng)', 0, -4.0, 'F.Fab', 1.0))
b.append(text('${REFERENCE}', 0, -2.0, 'F.Fab', 1.0))
footprint('Display_GC9A01_8chan',
          'Màn tròn GC9A01 1,28" hàn thẳng vào mạch, 7 chân bước 2,54 + pad 8 (BLK, cho module 8 chân). Gốc = tâm màn; '
          'hàng chân cách tâm 24,7 mm. Thứ tự 1..7: RST CS DC SDA SCL GND VCC (KIỂM TRA LẠI TRÊN MODULE THẬT).',
          'GC9A01 round display', (0, -6.0), (0, 2.0), b)

# 6) Nút SOS 6x6x7,5 góc vuông, hàn mép mạch (TẠM: 4 chân 6,5 x 4,5 mm, chờ đo nút thật).
#    Pad cùng số nối thông bên trong nút. Nút bấm hướng về phía -y (đặt sát mép mạch).
b = []
for (num, x, y) in (('1', 0, 0), ('1', SOS_DOC, 0), ('2', 0, SOS_NGANG), ('2', SOS_DOC, SOS_NGANG)):
    b.append(tht(num, x, y, 1.6, 1.0))
cx, cy = SOS_DOC / 2, SOS_NGANG / 2
b.append(rect(cx - 3, cy - 3, cx + 3, cy + 3, 'F.Fab', 0.1))
b.append(rect(cx - 1.75, cy - 3 - 1.5, cx + 1.75, cy - 3, 'F.Fab', 0.1))     # núm bấm nhô ra mép
b.append(rect(cx - 3.25, cy - 3.25, cx + 3.25, cy + 3.25, 'F.CrtYd', 0.05))
b.append(text('${REFERENCE}', cx, cy, 'F.Fab', 1.0))
footprint('SW_SOS_6x6_GocVuong_TAM',
          'Nút nhấn 6x6x7,5 mm góc vuông hàn mép mạch. TẠM: 4 chân lỗ 1,0 mm xếp 6,5 x 4,5 mm, đo lại nút thật. 1-1 và 2-2 nối thông.',
          'tactile switch right angle', (cx, cy - 5.6), (cx, cy + 4.5), b)

# 7) Hai pad xuyên lỗ cho dây motor / chân pogo
def hai_pad(name, descr, buoc, nhan, ref_dy=-2.2):
    b = []
    b.append(tht('1', 0, 0, 1.6, 1.0, square=True))
    b.append(tht('2', buoc, 0, 1.6, 1.0))
    b.append(rect(-1.05, -1.05, buoc + 1.05, 1.05, 'F.CrtYd', 0.05))
    b.append(rect(-1.0, -1.0, buoc + 1.0, 1.0, 'F.Fab', 0.1))
    b.append(text(nhan, buoc / 2, 0, 'F.Fab', 0.6))
    footprint(name, descr, name, (buoc / 2, ref_dy), (buoc / 2, 2.2), b)

hai_pad('Motor_1027_2pad_P4.0_TAM', 'Hai pad hàn thẳng 2 dây của motor rung 1027 (lỗ 1,0 mm). TẠM: bước 4,0 mm. 1 = +3V3 (dây đỏ), 2 = MOTOR_N',
        MOTOR_BUOC, '+  -')
hai_pad('Pogo_2pad_P2.54_TAM', 'Chân sạc pogo nam châm 2 chân hàn thẳng vào mạch (mặt dưới). TẠM: bước 2,54 mm, lỗ 1,0 mm. 1 = +5V, 2 = GND',
        POGO_BUOC, '+  -')

# 8) Pad RA ở mặt trên (ngón tay chạm qua cửa sổ của vỏ): pad đồng lộ, nên mạ ENIG
def dien_cuc(name, W, H, descr):
    b = []
    b.append(f'(pad "1" smd roundrect (at 0 0) (size {W} {H}) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.15) (zone_connect 2) (uuid {q(u())}))')
    b.append(rect(-W / 2 - 0.25, -H / 2 - 0.25, W / 2 + 0.25, H / 2 + 0.25, 'F.CrtYd', 0.05))
    b.append(rect(-W / 2, -H / 2, W / 2, H / 2, 'F.Fab', 0.1))
    b.append(text('${REFERENCE}', 0, 0, 'F.Fab', 1.0))
    footprint(name, descr, 'ECG electrode', (0, -H / 2 - 1.5), (0, H / 2 + 1.5), b, attr='smd exclude_from_pos_files exclude_from_bom')

dien_cuc('DienCuc_RA_8x9.6mm', 8.0, 9.6, 'Điện cực RA ở mặt trên, sát mép mạch: pad đồng lộ 8x9,6 mm (ENIG), ngón tay phải chạm qua cửa sổ vỏ.')

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
