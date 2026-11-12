# Sinh thư viện ký hiệu riêng + sơ đồ nguyên lý cho bản mạch module 2.0 (không dây nối)
import os, sys, uuid, math
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, dump, Q, q, find, findall

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = 'dong_ho_module_v2'
KSYM = r'C:\Program Files\KiCad\10.0\share\kicad\symbols'
NS = uuid.UUID('6c1f3a52-9d0e-4b8a-8a51-2d6d1c0e7a11')
_cnt = [0]
def uid(tag=None):
    _cnt[0] += 1
    return str(uuid.uuid5(NS, f'{tag}-{_cnt[0]}'))
ROOT = str(uuid.uuid5(NS, 'root'))

# ---------------------------------------------------------------- ký hiệu riêng
def font(sz=1.27):
    return f'(effects (font (size {sz} {sz})))'

def prop(name, val, x, y, hide=False, just=None):
    h = ' (hide yes)' if hide else ''
    j = f' (justify {just})' if just else ''
    return f'(property {q(name)} {q(val)} (at {x} {y} 0){h} (effects (font (size 1.27 1.27)){j}))'

def box_symbol(name, ref, value, fp, desc, W, left=(), right=(), top=(), bottom=(), H=None):
    """left/right: list of (num, name, type) từ trên xuống; top/bottom: list (num,name,type,x)."""
    n = max(len(left), len(right), 1)
    extra = (2 if top else 0) + (2 if bottom else 0)
    if H is None:
        H = (n + 1 + extra) * 2.54
    hw = W / 2
    yt = H / 2
    yt = round(yt / 2.54) * 2.54
    yb = -yt
    pins = []
    def pin(num, nm, typ, x, y, a):
        pins.append(f'(pin {typ} line (at {x:.2f} {y:.2f} {a}) (length 2.54) (name {q(nm)} {font()}) (number {q(num)} {font()}))')
    y0 = yt - 2.54 - (5.08 if top else 0)
    for i, (num, nm, typ) in enumerate(left):
        pin(num, nm, typ, -hw - 2.54, y0 - i * 2.54, 0)
    for i, (num, nm, typ) in enumerate(right):
        pin(num, nm, typ, hw + 2.54, y0 - i * 2.54, 180)
    for (num, nm, typ, x) in top:
        pin(num, nm, typ, x, yt + 2.54, 270)
    for (num, nm, typ, x) in bottom:
        pin(num, nm, typ, x, yb - 2.54, 90)
    s = f'''(symbol {q(name)} (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
  {prop("Reference", ref, 0, yt + (12.7 if top else 1.27))}
  {prop("Value", value, 0, yb - (12.7 if bottom else 1.27))}
  {prop("Footprint", fp, 0, 0, hide=True)}
  {prop("Datasheet", "", 0, 0, hide=True)}
  {prop("Description", desc, 0, 0, hide=True)}
  (symbol {q(name + "_0_1")} (rectangle (start {-hw} {yt}) (end {hw} {yb}) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol {q(name + "_1_1")} {" ".join(pins)})
  (embedded_fonts no))'''
    return s

LIBSYMS = [
 box_symbol('XIAO_nRF52840_Sense_DeCam', 'U', 'XIAO nRF52840 Sense', 'DoAnModule:XIAO_nRF52840_DeCam_2x7_P2.54_15.24mm',
   'Seeed XIAO nRF52840 Sense hàn thẳng lên mạch bằng 2 hàng chân 1x7 (2,54 mm, hai hàng cách 15,24 mm)', 20.32,
   left=[('1','D0/A0','bidirectional'),('2','D1','bidirectional'),('3','D2','bidirectional'),('4','D3','bidirectional'),
         ('5','D4/SDA','bidirectional'),('6','D5/SCL','bidirectional'),('7','D6/TX','bidirectional')],
   right=[('8','D7/RX','bidirectional'),('9','D8/SCK','bidirectional'),('10','D9/MISO','bidirectional'),('11','D10/MOSI','bidirectional')],
   top=[('14','5V','power_in',-2.54),('12','3V3','power_out',2.54)],
   bottom=[('13','GND','power_in',0)]),
 box_symbol('Module_MAX30102', 'U', 'Module MAX30102', 'DoAnModule:Module_MAX30102_2x4',
   'Module MAX30102 đen 2x4 chân (HW-605, I2C 0x57): 1 VIN, 2 SDA, 3 SCL, 4 GND, 5 GND, 6 RD, 7 IRD, 8 INT', 15.24,
   left=[('3','SCL','input'),('2','SDA','bidirectional')],
   right=[('8','INT','output'),('7','IRD','passive'),('6','RD','passive')],
   top=[('1','VIN','power_in',0)], bottom=[('4','GND','power_in',-2.54),('5','GND','passive',2.54)]),
 box_symbol('Module_MAX30205_CJMCU', 'U', 'CJMCU-30205', 'DoAnModule:Module_CJMCU-30205_1x8',
   'Module CJMCU-30205 (MAX30205, I2C 0x48 khi A0=A1=A2=GND), header 1x8: VCC GND SDA SCL OS A0 A1 A2. VCC chỉ 3,3 V', 20.32,
   left=[('3','SDA','bidirectional'),('4','SCL','input')],
   right=[('5','OS','output')],
   top=[('1','VCC','power_in',0)],
   bottom=[('2','GND','power_in',-7.62),('6','A0','input',-2.54),('7','A1','input',2.54),('8','A2','input',7.62)]),
 box_symbol('Module_AD8232', 'U', 'Module AD8232', 'DoAnModule:Module_AD8232_9chan',
   'Module AD8232 (ECG) cắm thẳng vào mạch qua 9 lỗ: 1 RA, 2 LA, 3 RL, 4 GND, 5 3V3, 6 OUTPUT, 7 LO-, 8 LO+, 9 SDN', 17.78,
   left=[('1','RA','passive'),('2','LA','passive'),('3','RL','passive')],
   right=[('6','OUTPUT','output'),('7','LO-','output'),('8','LO+','output'),('9','SDN','input')],
   top=[('5','3.3V','power_in',0)], bottom=[('4','GND','power_in',0)]),
 box_symbol('Display_GC9A01', 'U', 'GC9A01 1.28in', 'DoAnModule:Display_GC9A01_8chan',
   'Màn tròn 1,28" GC9A01 (SPI) hàn thẳng vào mạch: 1 RST, 2 CS, 3 DC, 4 SDA, 5 SCL, 6 GND, 7 VCC, 8 BLK (pad 8 chỉ dùng với module 8 chân)', 15.24,
   left=[('1','RST','input'),('2','CS','input'),('3','DC','input'),('4','SDA','input'),('5','SCL','input'),('8','BLK','input')],
   top=[('7','VCC','power_in',0)], bottom=[('6','GND','power_in',0)]),
]

def write_custom_lib():
    s = '(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") (generator_version "10.0")\n'
    s += '\n'.join(LIBSYMS) + ')\n'
    tree = parse(s)[0]
    with open(os.path.join(PRJ, 'lib', 'DoAnModule.kicad_sym'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(dump(tree) + '\n')
    return tree

write_custom_lib()

# ---------------------------------------------------------------- lấy ký hiệu chuẩn
_libcache = {}
def stdlib(lib):
    if lib not in _libcache:
        if lib == 'DoAnModule':
            path = os.path.join(PRJ, 'lib', 'DoAnModule.kicad_sym')
        else:
            path = os.path.join(KSYM, lib + '.kicad_sym')
        t = parse(open(path, encoding='utf-8').read())[0]
        _libcache[lib] = {e[1]: e for e in findall(t, 'symbol')}
    return _libcache[lib]

def flat_symbol(libid):
    lib, nm = libid.split(':')
    syms = stdlib(lib)
    s = syms[nm]
    ext = find(s, 'extends')
    if ext is None:
        out = [x for x in s]
        out[1] = Q(libid)
        return out
    parent = flat_symbol(lib + ':' + ext[1])
    pname = ext[1]
    out = ['symbol', Q(libid)]
    cprops = {p[1]: p for p in findall(s, 'property')}
    for e in parent[2:]:
        if isinstance(e, list) and e[0] == 'property':
            out.append(cprops.pop(e[1], e))
        elif isinstance(e, list) and e[0] == 'symbol':
            sub = list(e)
            sub[1] = Q(str(sub[1]).replace(pname + '_', nm + '_', 1))
            out.append(sub)
        else:
            out.append(e)
    # thuộc tính chỉ có ở con
    idx = max(i for i, e in enumerate(out) if isinstance(e, list) and e[0] == 'property') + 1
    for p in cprops.values():
        out.insert(idx, p); idx += 1
    return out

def sym_pins(symtree):
    pins = {}
    for sub in findall(symtree, 'symbol'):
        parts = str(sub[1]).rsplit('_', 2)
        unit, style = int(parts[1]), int(parts[2])
        if unit not in (0, 1) or style not in (0, 1):
            continue
        for p in findall(sub, 'pin'):
            at = find(p, 'at')
            num = str(find(p, 'number')[1])
            pins[num] = (float(at[1]), float(at[2]), float(at[3]), str(p[1]), str(find(p, 'name')[1]))
    return pins

# ---------------------------------------------------------------- dựng sơ đồ
items = []       # chuỗi s-expr
used_libs = {}   # libid -> tree
pwr_n = [0]
flg_n = [0]
G = 1.27
def snap(v):
    return round(v / G) * G

def place(libid, ref, value, x, y, fp=None, props=None, pinnets=None, dnp=False, in_bom=True, on_board=True, refpos=None, valpos=None, hide_val=False, desc=None):
    """pinnets: {pin_number: netname | 'NC' | None}"""
    if libid not in used_libs:
        used_libs[libid] = flat_symbol(libid)
    tree = used_libs[libid]
    pins = sym_pins(tree)
    lp = {str(p[1]): p for p in findall(tree, 'property')}
    if fp is None:
        fp = str(lp['Footprint'][2]) if 'Footprint' in lp else ''
    jl = ' (justify left)'
    if refpos is None and libid.startswith('DoAnModule'):
        a = find(lp['Reference'], 'at'); refpos = (x + float(a[1]), y - float(a[2]))
        a = find(lp['Value'], 'at'); valpos = (x + float(a[1]), y - float(a[2]))
        jl = ''
    rx, ry = refpos if refpos else (x + 6.35, y - 2.54)
    vx, vy = valpos if valpos else (x + 6.35, y)
    is_power = ref.startswith('#')
    ps = []
    ps.append(f'(property "Reference" {q(ref)} (at {rx:.2f} {ry:.2f} 0){" (hide yes)" if is_power else ""} (effects (font (size 1.27 1.27)){jl}))')
    ps.append(f'(property "Value" {q(value)} (at {vx:.2f} {vy:.2f} 0){" (hide yes)" if hide_val else ""} (effects (font (size 1.27 1.27)){jl}))')
    ps.append(f'(property "Footprint" {q(fp)} (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))')
    ps.append(f'(property "Datasheet" "" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))')
    if desc is None:
        desc = str(lp['Description'][2]) if 'Description' in lp else ''
    ps.append(f'(property "Description" {q(desc)} (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))')
    for k, v in (props or {}).items():
        ps.append(f'(property {q(k)} {q(v)} (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27))))')
    pinu = ' '.join(f'(pin {q(n)} (uuid {q(uid(ref + n))}))' for n in pins)
    items.append(f'''(symbol (lib_id {q(libid)}) (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board {"yes" if on_board else "no"}) (dnp {"yes" if dnp else "no"})
 (uuid {q(uid(ref))}) {" ".join(ps)} {pinu}
 (instances (project {q(NAME)} (path {q("/" + ROOT)} (reference {q(ref)}) (unit 1)))))''')
    # nối chân
    for num, net in (pinnets or {}).items():
        px, py, a, typ, nm = pins[num]
        P = (x + px, y - py)
        d = (-round(math.cos(math.radians(a))), round(math.sin(math.radians(a))))
        connect(P, d, net)

def wire(a, b):
    items.append(f'(wire (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f})) (stroke (width 0) (type default)) (uuid {q(uid("w"))}))')

def power(libid, at):
    pwr_n[0] += 1
    nm = libid.split(':')[1]
    if nm == 'PWR_FLAG':
        flg_n[0] += 1
        ref = f'#FLG{flg_n[0]:02d}'
    else:
        ref = f'#PWR{pwr_n[0]:02d}'
    x, y = at
    vy = y + 3.81 if nm == 'GND' else y - 3.81
    if nm == 'PWR_FLAG':
        vy = y - 5.08
    place(libid, ref, nm, round(x, 2), round(y, 2), fp='', refpos=(x, y), valpos=(x - 1.27 * len(nm) * 0.45, vy))

def label(at, d, net):
    ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]
    just = 'left bottom' if ang in (0, 90) else 'right bottom'
    items.append(f'(label {q(net)} (at {at[0]:.2f} {at[1]:.2f} {ang}) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid("l"))}))')

POWER = {'GND': 'power:GND', '+3V3': 'power:+3V3', '+5V': 'power:+5V'}

def connect(P, d, net, L=2.54):
    if net is None:
        return
    if net == 'NC':
        items.append(f'(no_connect (at {P[0]:.2f} {P[1]:.2f}) (uuid {q(uid("nc"))}))')
        return
    S = (P[0] + d[0] * L, P[1] + d[1] * L)
    wire(P, S)
    if net in POWER:
        want = (0, 1) if net == 'GND' else (0, -1)
        if d != want:
            if d[0] == 0:
                raise RuntimeError(f'nguồn {net} ngược hướng tại {P}')
            T = (S[0], S[1] + want[1] * 2.54)
            wire(S, T)
            S = T
        power(POWER[net], S)
    else:
        label(S, d, net)

def text(s, x, y, size=1.27, bold=False):
    b = ' (bold yes)' if bold else ''
    items.append(f'(text {q(s)} (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {size} {size}){b}) (justify left top)) (uuid {q(uid("t"))}))')

def frame(x1, y1, x2, y2, title):
    items.append(f'(rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.2) (type dash)) (fill (type none)) (uuid {q(uid("r"))}))')
    text(title, x1 + 1.27, y1 + 1.27, 2.0, True)

def pwrflag(at, net):
    x, y = at
    power('power:PWR_FLAG', (x, y))
    T = (x + 7.62, y)
    wire((x, y), T)
    if net in POWER:
        power(POWER[net], T)
    else:
        label(T, (1, 0), net)

R0805 = 'Resistor_SMD:R_0805_2012Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
HDR = 'Connector_PinHeader_2.54mm:PinHeader_1x0{}_P2.54mm_Vertical'

def R(ref, val, x, y, n1, n2):
    place('Device:R', ref, val, x, y, fp=R0805, desc='Điện trở 0805, 1%', pinnets={'1': n1, '2': n2}, refpos=(x + 2.54, y - 1.27), valpos=(x + 2.54, y + 1.27))
def C(ref, val, x, y, n1='+3V3', n2='GND'):
    place('Device:C', ref, val, x, y, fp=C0805, desc='Tụ gốm 0805 X5R/X7R, 10 V trở lên', pinnets={'1': n1, '2': n2}, refpos=(x + 2.54, y - 1.27), valpos=(x + 2.54, y + 1.27))

# ===== Khối A: XIAO
frame(15, 20, 125, 120, 'A. Vi điều khiển XIAO nRF52840 Sense (hàn thẳng lên mạch)')
place('DoAnModule:XIAO_nRF52840_Sense_DeCam', 'U1', 'XIAO nRF52840 Sense', 69.85, 60.96,
      pinnets={'1': 'ECG_OUT', '2': 'ECG_LOD', '3': 'MOTOR_EN', '4': 'TFT_BLK', '5': 'I2C_SDA', '6': 'I2C_SCL',
               '7': 'TFT_DC', '8': 'TFT_CS', '9': 'TFT_SCK', '10': 'SOS_BTN', '11': 'TFT_MOSI',
               '12': '+3V3', '13': 'GND', '14': '+5V'})
C('C1', '10uF', 100.33, 35.56)
C('C2', '100nF', 111.76, 35.56)
text('Gán chân: D0=ECG_OUT, D1=ECG_LOD (LO+ hoặc LO-), D2=motor, D3=đèn nền TFT (pad 8),\n'
     'D4/D5=I2C (MAX30102 0x57, MAX30205 0x48), D6=TFT_DC, D7=TFT_CS,\n'
     'D8=TFT_SCK, D9=nút SOS (INPUT_PULLUP), D10=TFT_MOSI.\n'
     'I2C không thêm điện trở kéo lên: hai module đã có sẵn.\n'
     'Pin LiPo 502030 hàn thẳng 2 dây vào pad BAT+/BAT- mặt dưới XIAO (không đi qua mạch).\n'
     'C1, C2 nằm dưới thân XIAO, sát chân 3V3. Đầu anten sát mép mạch, không đồng bên dưới.', 20.32, 96.52)

# ===== Khối B: Nguồn
frame(15, 125, 125, 230, 'B. Nguồn: sạc pogo 5 V (pin nối thẳng vào XIAO)')
place('Connector_Generic:Conn_01x02', 'J2', 'Pogo sạc (nam châm)', 30.48, 148.59, fp='DoAnModule:Pogo_2pad_P2.54_TAM',
      desc='Chân sạc pogo nam châm 2 chân hàn thẳng mặt dưới (TẠM, bước 2,54): 1 = +5V, 2 = GND', pinnets={'1': 'VCHG', '2': 'GND'}, refpos=(29.21, 144.78), valpos=(33.02, 149.86))
place('Diode:SMAJ5.0A', 'D4', 'SMAJ5.0A', 55.88, 160.02, fp='Diode_SMD:D_SMA',
      desc='TVS một chiều 5 V, 400 W, SMA (bảo vệ chân sạc)', pinnets={'1': 'VCHG', '2': 'GND'}, refpos=(52.07, 156.21), valpos=(45.72, 165.1))
place('Diode:SS14', 'D5', 'SS14', 93.98, 148.59, fp='Diode_SMD:D_SMA',
      desc='Diode Schottky 40 V 1 A, SMA (D5: chặn dòng ngược về pogo; D1: dập xung ngược motor)', pinnets={'1': '+5V', '2': 'VCHG'}, refpos=(90.17, 144.78), valpos=(90.17, 153.67))
pwrflag((97.79, 170.18), '+5V')
pwrflag((97.79, 185.42), 'GND')
text('Chân sạc pogo -> TVS SMAJ5.0A về GND -> SS14 nối tiếp -> chân 5V của XIAO.\n'
     'SS14 chặn dòng ngược từ USB-C ra chân pogo khi cắm cả hai.\n'
     'Mạch sạc LiPo nằm sẵn trên XIAO (BQ25101).\n'
     'Pin 502030 (5 x 20 x 30 mm, có PCM): 2 dây đỏ/đen hàn thẳng vào\n'
     'pad BAT+ / BAT- ở mặt dưới XIAO, luồn ra cạnh thân XIAO.\n'
     'Bỏ J3 (JST pin), J4 (dây sang XIAO) và lưới VBAT của bản 1.3.', 20.32, 198.12)

# ===== Khối C: PPG MAX30102
frame(130, 20, 235, 95, 'C. PPG: module MAX30102 (mặt da)')
place('DoAnModule:Module_MAX30102', 'U2', 'MAX30102 (module 2x4)', 165.1, 55.88,
      pinnets={'1': '+3V3', '4': 'GND', '5': 'GND', '3': 'I2C_SCL', '2': 'I2C_SDA', '6': 'NC', '7': 'NC', '8': 'NC'})
text('Module đen 2x4: VIN SDA SCL GND / GND RD IRD INT (đã đo 27/10/2026).\n'
     'INT, IRD, RD bỏ trống. Module có LDO 1,8 V, tụ và điện trở kéo lên riêng.', 135.89, 83.82)

# ===== Khối D: Nhiệt độ MAX30205
frame(130, 100, 235, 180, 'D. Nhiệt độ da: module CJMCU-30205 (mặt da)')
place('DoAnModule:Module_MAX30205_CJMCU', 'U3', 'CJMCU-30205', 167.64, 133.35,
      pinnets={'1': '+3V3', '2': 'GND', '3': 'I2C_SDA', '4': 'I2C_SCL', '5': 'NC', '6': 'GND', '7': 'GND', '8': 'GND'})
text('VCC chỉ cấp 3,3 V (không bao giờ 5 V). A0=A1=A2=GND -> địa chỉ 0x48.\n'
     'OS bỏ trống. Đặt cách đèn LED MAX30102 tối thiểu 10 mm.', 135.89, 162.56)

# ===== Khối E: ECG AD8232
frame(240, 20, 405, 125, 'E. ECG: module AD8232 (cắm thẳng) và điện cực')
place('DoAnModule:Module_AD8232', 'U4', 'AD8232 (module)', 294.64, 64.77,
      pinnets={'5': '+3V3', '4': 'GND', '1': 'ECG_RA', '2': 'ECG_LA', '3': 'ECG_RL',
               '6': 'ECG_OUT', '7': 'LO_N', '8': 'LO_P', '9': 'NC'})
place('Diode:1N4148WS', 'D2', '1N4148WS', 342.9, 50.8, fp='Diode_SMD:D_SOD-323',
      desc='Diode tín hiệu 75 V 150 mA, SOD-323 (cổng OR LO+ / LO-)', pinnets={'2': 'LO_P', '1': 'ECG_LOD'}, refpos=(339.09, 46.99), valpos=(339.09, 55.88))
place('Diode:1N4148WS', 'D3', '1N4148WS', 342.9, 66.04, fp='Diode_SMD:D_SOD-323',
      desc='Diode tín hiệu 75 V 150 mA, SOD-323 (cổng OR LO+ / LO-)', pinnets={'2': 'LO_N', '1': 'ECG_LOD'}, refpos=(339.09, 62.23), valpos=(339.09, 71.12))
R('R3', '100k', 381.0, 58.42, 'ECG_LOD', 'GND')
place('Connector_Generic:Conn_01x01', 'E1', 'Điện cực LA (cổ tay)', 335.28, 92.71, fp='DoAnModule:DienCuc_ECG_9x16mm', in_bom=False,
      desc='Điện cực ECG LA: pad đồng lộ 9x16 mm ở mặt da', pinnets={'1': 'ECG_LA'}, refpos=(337.82, 90.17), valpos=(337.82, 95.25))
place('Connector_Generic:Conn_01x01', 'E2', 'Điện cực RL (cổ tay)', 335.28, 102.87, fp='DoAnModule:DienCuc_ECG_9x16mm', in_bom=False,
      desc='Điện cực ECG RL: pad đồng lộ 9x16 mm ở mặt da', pinnets={'1': 'ECG_RL'}, refpos=(337.82, 100.33), valpos=(337.82, 105.41))
place('Connector_Generic:Conn_01x01', 'E3', 'Điện cực RA (ngón tay)', 335.28, 113.03, fp='DoAnModule:DienCuc_RA_8x9.6mm', in_bom=False,
      desc='Điện cực ECG RA: pad đồng lộ 8x9,6 mm ở mặt trên, mép mạch (ngón tay phải chạm qua cửa sổ vỏ)', pinnets={'1': 'ECG_RA'}, refpos=(337.82, 110.49), valpos=(337.82, 115.57))
text('LO+ và LO- gộp bằng 2 diode (OR) vào D1, R3 kéo xuống: D1 = 1 khi tuột điện cực.\n'
     'Module cắm thẳng qua 9 lỗ (tháo giắc 3,5 mm). RA/LA/RL nối điện cực bằng đường mạch.\n'
     'SDN bỏ trống (module tự kéo lên, AD8232 luôn chạy). Module có tụ riêng.', 245.11, 116.84)

# ===== Khối F: Màn hình
frame(240, 130, 405, 205, 'F. Màn hình tròn GC9A01 1,28" (hàn thẳng)')
place('DoAnModule:Display_GC9A01', 'U5', 'GC9A01 1.28in', 278.13, 166.37,
      pinnets={'7': '+3V3', '6': 'GND', '5': 'TFT_SCK', '4': 'TFT_MOSI', '1': '+3V3', '3': 'TFT_DC', '2': 'TFT_CS', '8': 'TFT_BLK'})
text('RST nối thẳng 3V3 (bỏ R4, C9): màn tự reset khi cấp nguồn, firmware RST = -1.\n'
     'Pad 8 (BLK -> D3) chỉ dùng khi module có 8 chân; module 7 chân bỏ trống pad 8.\n'
     'THỨ TỰ CHÂN CẦN KIỂM TRA TRÊN MODULE THẬT.', 302.26, 182.88)

# ===== Khối G: Motor rung, nút SOS
frame(130, 185, 235, 280, 'G. Motor rung 1027 (nguồn 3V3) và nút SOS')
place('Motor:Motor_DC', 'M1', 'Motor rung 1027', 213.36, 201.93, fp='DoAnModule:Motor_1027_2pad_P4.0_TAM',
      desc='Motor rung đồng xu 1027 (10 mm, 3 V), 2 dây hàn thẳng vào pad (TẠM bước 4,0 mm): 1 = +3V3, 2 = MOTOR_N',
      pinnets={'1': '+3V3', '2': 'MOTOR_N'}, refpos=(218.44, 199.39), valpos=(218.44, 204.47))
place('Diode:SS14', 'D1', 'SS14', 172.72, 203.2, fp='Diode_SMD:D_SMA',
      desc='Diode Schottky 40 V 1 A, SMA (D5: chặn dòng ngược về pogo; D1: dập xung ngược motor)', pinnets={'1': '+3V3', '2': 'MOTOR_N'}, refpos=(168.91, 199.39), valpos=(168.91, 208.28))
C('C3', '10uF', 193.04, 203.2)
place('Transistor_FET:AO3400A', 'Q1', 'AO3400A', 175.26, 228.6, fp='Package_TO_SOT_SMD:SOT-23',
      desc='MOSFET kênh N 30 V 5,7 A, SOT-23 (đóng cắt motor)', pinnets={'1': 'MOTOR_G', '2': 'GND', '3': 'MOTOR_N'}, refpos=(180.34, 226.06), valpos=(180.34, 231.14))
R('R1', '100R', 147.32, 218.44, 'MOTOR_EN', 'MOTOR_G')
R('R2', '100k', 152.4, 241.3, 'MOTOR_G', 'GND')
place('Switch:SW_Push', 'SW1', 'SOS 6x6x7.5 góc vuông', 208.28, 243.84, fp='DoAnModule:SW_SOS_6x6_GocVuong_TAM',
      desc='Nút nhấn 6x6x7,5 mm góc vuông hàn mép mạch (TẠM footprint 6,5 x 4,5 mm): 1 = D9, 2 = GND',
      pinnets={'1': 'SOS_BTN', '2': 'GND'}, refpos=(205.74, 238.76), valpos=(205.74, 248.92))
text('Motor lấy nguồn 3V3 (không lấy VBAT). C3 10 uF đặt sát motor.\n'
     'Q1 đóng cắt phía thấp, R2 giữ motor tắt khi XIAO khởi động.\n'
     'Nút SOS nối D9 xuống GND, firmware bật INPUT_PULLUP.', 135.89, 260.35)

# ===== Khối H: cơ khí
frame(240, 210, 330, 280, 'H. Cơ khí (không lỗ vít)')
text('Bản 2.0 không còn chỗ cho 4 lỗ M2.\n'
     'Mạch kẹp trong vỏ bằng gờ/rãnh ở mép,\n'
     'giữ thêm bằng keo nóng hoặc băng keo 2 mặt.\n'
     'Pin 502030: vùng 20 x 30 mm mặt trên.\n'
     'Motor 1027: dán mặt dưới (mặt da).', 245.11, 220.98)

# ---------------------------------------------------------------- ghi file
def build():
    libs = '\n'.join(dump(t, 2) for t in used_libs.values())
    out = f'''(kicad_sch
	(version 20250114)
	(generator "eeschema")
	(generator_version "9.0")
	(uuid {q(ROOT)})
	(paper "A3")
	(title_block
		(title "Thiết bị đeo tay giám sát sức khỏe - Mạch ghép module v2.0 (không dây nối)")
		(date "2026-11-12")
		(rev "2.1")
		(comment 1 "XIAO nRF52840 Sense + MAX30102 + AD8232 + MAX30205 (dạng module), màn GC9A01")
		(comment 2 "Mạch 2 lớp, mọi module hàn/cắm thẳng, chỉ còn 2 dây pin và 2 dây motor")
	)
	(lib_symbols
{libs}
	)
{chr(10).join(items)}
	(sheet_instances (path "/" (page "1")))
	(embedded_fonts no)
)
'''
    tree = parse(out)[0]
    with open(os.path.join(PRJ, NAME + '.kicad_sch'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(dump(tree) + '\n')

build()
print('ok', len(items))
