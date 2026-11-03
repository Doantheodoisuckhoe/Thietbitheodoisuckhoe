# So do khoi cam breadboard 28/10 (kieu so do khoi): XIAO, AD8232, MAX30102, MAX30205, GC9A01, nut SOS
import sys
C = {'mo':'#8d5a2b','3v3':'#e0302d','gnd':'#222','sda':'#1f77b4','scl':'#e08e00','ecg':'#2e9e48','sos':'#8e5bbf','spi':'#f26b1d','blk':'#c2185b','xam':'#999'}
o = []
A = o.append
W, H = 1200, 1060
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">')
A(f'<rect width="{W}" height="{H}" fill="#fff"/>')
A('<text x="600" y="40" font-size="20" font-weight="700" text-anchor="middle" fill="#222">Sơ đồ cắm breadboard 28/10 (chân giống firmware ble_suc_khoe và mạch in 1.2)</text>')

def hop(x, y, d=7):  # o nhay qua khi day cat ngang
    return f'L{x},{y-d} A{d},{d} 0 0 1 {x},{y+d}'
def day(d, mau, w=3):
    A(f'<path d="{d}" stroke="{C[mau]}" stroke-width="{w}" fill="none" stroke-linejoin="round"/>')
def cham(x, y, r=4.5, f='#555'):
    A(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}"/>')
def the(x, y, chu, mau, w=None):  # the 3V3 / GND
    w = w or (len(chu) * 8.6 + 16)
    A(f'<rect x="{x}" y="{y-11}" width="{w}" height="22" rx="4" fill="{C[mau]}"/>')
    A(f'<text x="{x+w/2}" y="{y+4.5}" font-size="12.5" font-weight="700" fill="#fff" text-anchor="middle">{chu}</text>')
    return w
def hop_module(x, y, w, h, ten, phu, nen='#f3f4f6'):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{nen}" stroke="#555" stroke-width="1.6"/>')
    A(f'<text x="{x+w/2}" y="{y+h/2-2}" font-size="17" font-weight="700" text-anchor="middle" fill="#222">{ten}</text>')
    A(f'<text x="{x+w/2}" y="{y+h/2+18}" font-size="12" text-anchor="middle" fill="#555">{phu}</text>')
def nhan(x, y, chu, neo='end', mau='#222', co=13, dam=True):
    fw = 'font-weight="700"' if dam else ''
    A(f'<text x="{x}" y="{y+4.5}" font-size="{co}" {fw} text-anchor="{neo}" fill="{mau}">{chu}</text>')
def ghi(x, y, chu, neo='start', mau='#888', co=11.5):
    A(f'<text x="{x}" y="{y+4}" font-size="{co}" text-anchor="{neo}" fill="{mau}">{chu}</text>')

# ---------- XIAO ----------
XL, XR = 480, 690
A('<rect x="550" y="118" width="70" height="30" rx="6" fill="#9aa6b2"/>')
A('<text x="585" y="138" font-size="11.5" font-weight="700" text-anchor="middle" fill="#fff">USB-C</text>')
hop_module(XL, 145, XR-XL, 390, 'XIAO', 'nRF52840 Sense', '#dfe8f1')
trai = ['D0/A0','D1','D2','D3','D4/SDA','D5/SCL','D6']
phai = ['5V','GND','3V3','D10','D9','D8','D7']
Y = lambda i: 200 + 50*i
for i,n in enumerate(trai):
    cham(XL, Y(i)); nhan(XL+10, Y(i), n, 'start')
for i,n in enumerate(phai):
    cham(XR, Y(i)); nhan(XR-10, Y(i), n, 'end')

# ---------- AD8232 ----------
AL, AR = 110, 290
hop_module(AL, 160, AR-AL, 350, 'AD8232', 'ECG')
pa = ['OUTPUT','LO+','3.3V','LO−','GND','SDN']
for i,n in enumerate(pa):
    cham(AR, Y(i)); nhan(AR-10, Y(i), n, 'end')
day(f'M{AR},{Y(0)} L{XL},{Y(0)}', 'ecg')                 # OUTPUT -> D0
day(f'M{AR},{Y(1)} L{XL},{Y(1)}', 'ecg')                 # LO+ -> D1
day(f'M{AR},{Y(2)} L{AR+40},{Y(2)}', '3v3'); the(AR+40, Y(2), '3V3', '3v3')
ghi(AR+12, Y(3), 'để trống', mau='#c00')
day(f'M{AR},{Y(4)} L{AR+40},{Y(4)}', 'gnd'); the(AR+40, Y(4), 'GND', 'gnd')
ghi(AR+12, Y(5), 'để trống')
# dien cuc: cap cua nhom: do RA, xanh la LA, vang RL
hx, hy = 110, 300
A(f'<circle cx="{hx}" cy="{hy}" r="12" fill="#333"/>')
for (t, m, yy) in [('Đỏ: RA', '#d22', 230), ('Xanh lá: LA', '#2e9e48', 300), ('Vàng: RL', '#d4a800', 370)]:
    A(f'<path d="M{hx},{hy} C{hx-20},{hy} {hx-30},{yy} {65},{yy}" stroke="{m}" stroke-width="3" fill="none"/>')
    A(f'<circle cx="65" cy="{yy}" r="7" fill="{m}"/>')
    A(f'<text x="8" y="{yy-13}" font-size="11" font-weight="700" fill="{m}">{t}</text>')
ghi(200, 530, 'jack 3,5 mm → cáp 3 điện cực', 'middle', '#555', 11.5)

# ---------- nguon XIAO ----------
ghi(XR+15, Y(0), 'KHÔNG dùng', mau='#c00', co=12.5)
day(f'M{XR},{Y(1)} L{XR+50},{Y(1)}', 'gnd'); the(XR+50, Y(1), 'GND → thanh xanh (−)', 'gnd')
day(f'M{XR},{Y(2)} L{XR+50},{Y(2)}', '3v3'); the(XR+50, Y(2), '3V3 → thanh đỏ (+)', '3v3')

# ---------- nut SOS tren D9 ----------
day(f'M{XR},{Y(4)} L{745},{Y(4)}', 'sos')
A(f'<rect x="745" y="{Y(4)-18}" width="56" height="36" rx="6" fill="#eee" stroke="#666" stroke-width="1.5"/>')
A(f'<circle cx="773" cy="{Y(4)}" r="10" fill="#aaa"/>')
day(f'M801,{Y(4)} L815,{Y(4)}', 'gnd'); the(815, Y(4), 'GND', 'gnd')
nhan(773, Y(4)-30, 'Nút SOS (hoặc dây chạm GND)', 'middle', '#333', 11.5)

# ---------- man GC9A01 ----------
DL, DR, DT, DB = 900, 1060, 320, 600
A(f'<rect x="{DL}" y="{DT}" width="{DR-DL}" height="{DB-DT}" rx="10" fill="#e6eefb" stroke="#555" stroke-width="1.6"/>')
A(f'<circle cx="{(DL+DR)/2-8}" cy="{(DT+DB)/2-20}" r="34" fill="#1e3a5f" stroke="#555"/>')
A(f'<text x="{(DL+DR)/2+12}" y="{(DT+DB)/2+52}" font-size="16" font-weight="700" text-anchor="middle" fill="#222">GC9A01</text>')
A(f'<text x="{(DL+DR)/2+12}" y="{(DT+DB)/2+70}" font-size="11.5" text-anchor="middle" fill="#555">màn tròn 1,28" (SPI)</text>')
yDC, yBLK = 550, 580
for n, yy in [('SDA', Y(3)), ('SCL', Y(5)), ('CS', Y(6)), ('DC', yDC), ('BLK', yBLK)]:
    cham(DL, yy); nhan(DL+8, yy, n, 'start', co=11.5)
for n, yy in [('VCC', 360), ('GND', 420), ('RES', 480)]:
    cham(DR, yy); nhan(DR-8, yy, n, 'end', co=11.5)
day(f'M{DR},360 L{DR+18},360', '3v3'); the(DR+18, 360, '3V3', '3v3')
day(f'M{DR},420 L{DR+18},420', 'gnd'); the(DR+18, 420, 'GND', 'gnd')
day(f'M{DR},480 L{DR+18},480', '3v3'); the(DR+18, 480, '3V3', '3v3')
day(f'M{XR},{Y(3)} L{DL},{Y(3)}', 'spi')                 # D10 -> SDA
day(f'M{XR},{Y(5)} L{DL},{Y(5)}', 'spi')                 # D8 -> SCL
day(f'M{XR},{Y(6)} L{DL},{Y(6)}', 'spi')                 # D7 -> CS
# D6 -> DC: ra trai, vong duoi XIAO
day(f'M{XL},{Y(6)} L470,{Y(6)} L470,{yDC} L{DL},{yDC}', 'spi')
# D3 -> BLK: ra trai, nhay qua day D4, D5
day(f'M{XL},{Y(3)} L460,{Y(3)} {hop(460, Y(4))} {hop(460, Y(5))} L460,{yBLK} L{DL},{yBLK}', 'blk')

# ---------- bus I2C ----------
ySCL, ySDA = 640, 680
day(f'M{XL},{Y(4)} L415,{Y(4)} L415,{ySDA} L1160,{ySDA}', 'sda')
day(f'M{XL},{Y(5)} L445,{Y(5)} L445,{ySCL} L1160,{ySCL}', 'scl')
cham(415, ySDA, 4.5, C['sda']); cham(445, ySCL, 4.5, C['scl'])
nhan(1166, ySCL, 'SCL', 'start', C['scl']); nhan(1166, ySDA, 'SDA', 'start', C['sda'])

# ---------- MAX30102 ----------
MT = 740
A(f'<rect x="470" y="{MT}" width="300" height="110" rx="10" fill="#f3f4f6" stroke="#555" stroke-width="1.6"/>')
A(f'<text x="620" y="{MT+48}" font-size="17" font-weight="700" text-anchor="middle" fill="#222">MAX30102</text>')
A(f'<text x="620" y="{MT+66}" font-size="11.5" text-anchor="middle" fill="#555">nhịp tim / SpO2, I2C 0x57</text>')
for n, x in [('SDA', 510), ('SCL', 570)]:
    cham(x, MT); nhan(x, MT+18, n, 'middle', co=12)
for n, x in [('INT', 650), ('IRD', 700), ('RD', 745)]:
    cham(x, MT); nhan(x, MT+18, n, 'middle', co=12); ghi(x, MT-16, 'trống', 'middle')
day(f'M510,{MT} L510,{ySDA}', 'sda'); cham(510, ySDA, 4.5, C['sda'])
day(f'M570,{MT} L570,{ySDA+7} A7,7 0 0 1 570,{ySDA-7} L570,{ySCL}', 'scl'); cham(570, ySCL, 4.5, C['scl'])
for n, x, m, t in [('VIN', 530, '3v3', '3V3'), ('GND', 700, 'gnd', 'GND')]:
    cham(x, MT+110); nhan(x, MT+96, n, 'middle', co=12)
    day(f'M{x},{MT+110} L{x},{MT+138}', m); the(x-20, MT+148, t, m, 40)
ghi(620, MT+178, 'Module đen 2 hàng chân:', 'middle', '#c00', 11.5); ghi(620, MT+194, 'nối 4 dây đực–cái từ hàng có chữ VIN', 'middle', '#c00', 11.5)

# ---------- MAX30205 ----------
A(f'<rect x="810" y="{MT}" width="360" height="110" rx="10" fill="#f3f4f6" stroke="#555" stroke-width="1.6"/>')
A(f'<text x="990" y="{MT+48}" font-size="17" font-weight="700" text-anchor="middle" fill="#222">MAX30205 (CJMCU-30205)</text>')
A(f'<text x="990" y="{MT+66}" font-size="11.5" text-anchor="middle" fill="#555">nhiệt độ da, I2C 0x48</text>')
for n, x in [('SDA', 850), ('SCL', 910)]:
    cham(x, MT); nhan(x, MT+18, n, 'middle', co=12)
cham(1130, MT); nhan(1130, MT+18, 'OS', 'middle', co=12); ghi(1130, MT-16, 'trống', 'middle')
day(f'M850,{MT} L850,{ySDA}', 'sda'); cham(850, ySDA, 4.5, C['sda'])
day(f'M910,{MT} L910,{ySDA+7} A7,7 0 0 1 910,{ySDA-7} L910,{ySCL}', 'scl'); cham(910, ySCL, 4.5, C['scl'])
for n, x, m, t in [('VCC', 850, '3v3', '3V3'), ('GND', 930, 'gnd', 'GND'), ('A0', 1000, 'gnd', 'GND'), ('A1', 1060, 'gnd', 'GND'), ('A2', 1120, 'gnd', 'GND')]:
    cham(x, MT+110); nhan(x, MT+96, n, 'middle', co=12)
    day(f'M{x},{MT+110} L{x},{MT+138}', m); the(x-20, MT+148, t, m, 40)

# ---------- mach lai dong co rung (D2) ----------
def dien_tro(x1, y1, x2, y2, vach, ten, tx, ty, neo='start'):
    dung = x1 == x2
    day(f'M{x1},{y1} L{x2},{y2}', 'xam', 2.2)
    cx, cy = (x1+x2)/2, (y1+y2)/2
    w, h = (14, 40) if dung else (40, 14)
    A(f'<rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" rx="6" fill="#e9d3a6" stroke="#9c8152"/>')
    for k, m in enumerate(vach):
        o = -13 + k*7 + (4 if k == 3 else 0)
        if dung: A(f'<rect x="{cx-7}" y="{cy+o}" width="14" height="3.6" fill="{m}"/>')
        else: A(f'<rect x="{cx+o}" y="{cy-7}" width="3.6" height="14" fill="{m}"/>')
    nhan(tx, ty, ten, neo, '#333', 11.5)
NAU, DEN, DO, VANG, KIM = '#7b4a1e', '#111', '#d22', '#e8c400', '#c9a227'
A('<rect x="14" y="572" width="391" height="390" rx="10" fill="#fffaf3" stroke="#8d5a2b" stroke-width="1.5" stroke-dasharray="7 4"/>')
nhan(26, 592, 'Mạch lái động cơ rung (D2), giống mạch in', 'start', '#8d5a2b', 13)
day(f'M{XL},{Y(2)} L385,{Y(2)} L385,790', 'mo')
the(26, 640, '3V3', '3v3', 40)
day('M66,640 L190,640', '3v3'); cham(120, 640, 4, C['3v3'])
day('M120,640 L120,672', '3v3')
A('<circle cx="120" cy="700" r="28" fill="#cfd4d9" stroke="#666" stroke-width="2"/>')
A('<circle cx="120" cy="700" r="8" fill="#9aa1a8"/>')
day('M120,728 L120,760 L230,760', 'gnd')
nhan(86, 700, 'Motor', 'end', '#333', 11.5); nhan(86, 715, '1027', 'end', '#333', 11.5)
ghi(126, 663, 'đỏ', mau=DO, co=10.5); ghi(126, 745, 'đen', mau='#333', co=10.5)
day('M190,640 L190,672', 'xam', 2.2); day('M190,728 L190,760', 'xam', 2.2); cham(190, 760, 4, '#333')
A('<rect x="182" y="672" width="16" height="56" rx="4" fill="#1b1b1b"/>')
A('<rect x="182" y="676" width="16" height="8" fill="#c8c8c8"/>')
nhan(206, 690, 'Diode 1N5819', 'start', '#333', 11.5)
ghi(206, 706, 'vạch bạc về phía 3V3', mau='#c00', co=10.5)
A('<rect x="230" y="745" width="70" height="90" rx="5" fill="#2f6e8f" stroke="#1d4a61"/>')
A('<rect x="252" y="776" width="26" height="16" rx="2" fill="#111"/>')
A('<text x="265" y="812" font-size="10" font-weight="700" text-anchor="middle" fill="#fff">AO3400</text>')
for n, x, y in [('D', 230, 760), ('G', 300, 790), ('S', 265, 835)]:
    cham(x, y, 5, KIM)
ghi(237, 760, 'D', mau='#fff', co=11); ghi(293, 790, 'G', neo='end', mau='#fff', co=11); ghi(265, 825, 'S', neo='middle', mau='#fff', co=11)
ghi(222, 800, 'trên đế', neo='end', mau='#555', co=10); ghi(222, 814, 'SOT-23', neo='end', mau='#555', co=10)
day('M300,790 L330,790', 'mo'); cham(330, 790, 4, C['mo'])
dien_tro(330, 790, 385, 790, [NAU, DEN, NAU, KIM], 'R1 100 Ω', 348, 768, 'middle')
ghi(358, 810, 'nâu-đen-nâu', neo='middle', mau='#666', co=9)
dien_tro(330, 790, 330, 885, [NAU, DEN, VANG, KIM], 'R2 100 kΩ', 342, 838, 'start')
ghi(342, 854, 'nâu-đen-vàng', mau='#666', co=9)
the(310, 900, 'GND', 'gnd', 40)
day('M265,835 L265,889', 'gnd'); the(245, 900, 'GND', 'gnd', 40)
ghi(26, 930, 'Chưa có đế SOT-23: thay bằng transistor S8050:', mau='#555', co=10.5); ghi(26, 946, 'D2 qua 1 kΩ vào B, E → GND, C → dây đen motor.', mau='#555', co=10.5)

# ---------- chu thich ----------
yl = 1000
for i, (t, m) in enumerate([('3V3', '3v3'), ('GND', 'gnd'), ('SDA → D4', 'sda'), ('SCL → D5', 'scl'), ('ECG', 'ecg'), ('SOS → D9', 'sos'), ('Màn hình SPI', 'spi'), ('Đèn nền → D3', 'blk'), ('Motor → D2', 'mo')]):
    x = 30 + i * 130
    A(f'<line x1="{x}" y1="{yl}" x2="{x+30}" y2="{yl}" stroke="{C[m]}" stroke-width="4"/>')
    ghi(x + 38, yl, t, mau='#333', co=12.5)
ghi(30, 1035, 'Ô 3V3 / GND = cắm vào thanh nguồn đỏ (+) / xanh (−) của breadboard. Cắm theo TÊN chân in trên module (thứ tự chân thật có thể khác hình). Rút USB trước khi cắm/đổi dây.', mau='#555', co=11.5)
A('</svg>')
open(sys.argv[1], 'w').write('\n'.join(o))
