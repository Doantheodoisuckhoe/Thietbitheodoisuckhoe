# Vẽ ảnh PNG các tầng module chồng lên mạch (nhìn từ mặt trên) để xem bố trí 3 tầng:
#   L0: pin, XIAO, nút SOS, linh kiện dán; L1: module AD8232 (cao ~8,5 mm); L2: màn GC9A01 (trên cùng)
#   và các module mặt da (MAX30102, CJMCU-30205, điện cực, motor) vẽ nét đứt.
# Chạy: "C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\ve_chong_tang.py
import os, sys, math
import pcbnew
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kich_thuoc import *

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PRJ, 'dong_ho_module_v2.kicad_pcb'))
mm = pcbnew.ToMM
e = b.GetBoardEdgesBoundingBox()
OX, OY = mm(e.GetX()) + 0.05, mm(e.GetY()) + 0.05
BW, BH = mm(e.GetWidth()) - 0.1, mm(e.GetHeight()) - 0.1
K = 24                     # px / mm
M = 40                     # lề (px)
LEG = 430                  # cột chú thích bên phải
W, H = int(BW * K) + 2 * M + LEG, int(BH * K) + 2 * M + 60
img = Image.new('RGB', (W, H), 'white')
dr = ImageDraw.Draw(img, 'RGBA')
def font(sz):
    for f in ('arial.ttf', 'C:/Windows/Fonts/arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()
F, FS, FB = font(18), font(15), font(22)

def P(x, y):
    return (M + x * K, M + y * K)
def xy(v):
    return (mm(v.x) - OX, mm(v.y) - OY)

def dashed_rect(r, col, w=3, dash=10):
    x1, y1 = P(r[0], r[1]); x2, y2 = P(r[2], r[3])
    for (a, b_) in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        L = math.hypot(b_[0] - a[0], b_[1] - a[1]); n = max(1, int(L / dash))
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1, (i + 1) / n)
            dr.line([(a[0] + (b_[0] - a[0]) * t0, a[1] + (b_[1] - a[1]) * t0), (a[0] + (b_[0] - a[0]) * t1, a[1] + (b_[1] - a[1]) * t1)], fill=col, width=w)

def dashed_circle(c, r, col, w=3):
    n = 72
    for i in range(0, n, 2):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        dr.line([P(c[0] + r * math.cos(a0), c[1] + r * math.sin(a0)), P(c[0] + r * math.cos(a1), c[1] + r * math.sin(a1))], fill=col, width=w)

fp = {f.GetReference(): f for f in b.GetFootprints()}
def crt(ref):
    f = fp[ref]
    bb = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
    return (mm(bb.GetX()) - OX, mm(bb.GetY()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY)

# bảng
dr.rounded_rectangle([P(0, 0), P(BW, BH)], radius=2 * K, fill=(22, 110, 60, 40), outline=(0, 90, 40), width=3)

# vùng cấm anten
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        r = (mm(bb.GetX()) - OX, mm(bb.GetY()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY)
        if 'Anten' in z.GetZoneName():
            dr.rectangle([P(r[0], r[1]), P(r[2], r[3])], fill=(255, 200, 0, 70), outline=(200, 150, 0), width=2)
        else:
            bat = r

# mặt da (nét đứt xanh lá)
SKIN = (0, 140, 70)
for ref, nm in (('U2', 'MAX30102 (mặt da)'), ('U3', 'CJMCU-30205 (mặt da)'), ('E1', 'E1 LA'), ('E2', 'E2 RL')):
    r = crt(ref)
    dashed_rect(r, SKIN, 3)
    dr.text(P(r[0] + 0.4, r[3] - 1.4), nm, fill=SKIN, font=FS)
mc = None
for d_ in b.GetDrawings():
    if d_.GetLayer() == pcbnew.B_Fab and d_.GetShape() == pcbnew.SHAPE_T_CIRCLE:
        mc = xy(d_.GetCenter()); mr = mm(d_.GetRadius())
dr.ellipse([P(mc[0] - mr, mc[1] - mr), P(mc[0] + mr, mc[1] + mr)], fill=(255, 140, 0, 60), outline=(220, 110, 0), width=3)
dr.text(P(mc[0] - 3.2, mc[1] - 0.6), 'motor (mặt da)', fill=(170, 80, 0), font=FS)

# L0: pin, XIAO, nút SOS, RA
dr.rectangle([P(bat[0], bat[1]), P(bat[2], bat[3])], fill=(130, 130, 130, 90), outline=(80, 80, 80), width=3)
dr.text(P(bat[0] + 0.5, bat[1] + 0.4), 'L0 pin 502030', fill=(60, 60, 60), font=F)
p1 = [xy(p.GetPosition()) for p in fp['U1'].Pads() if p.GetNumber() in ('1', '7', '8', '14')]
xs = [q[0] for q in p1]; ys = [q[1] for q in p1]
xiao = (min(xs) - 1.28, min(ys) - 2.88, max(xs) + 1.28, min(ys) - 2.88 + XIAO_THAN[1])
dr.rectangle([P(xiao[0], xiao[1]), P(xiao[2], xiao[3])], fill=(40, 90, 220, 60), outline=(30, 60, 200), width=3)
dr.text(P(xiao[0] + 0.5, xiao[3] - 1.6), 'L0 XIAO (USB)', fill=(30, 60, 200), font=F)
r = crt('SW1')
dr.rectangle([P(r[0], r[1]), P(r[2], r[3])], fill=(60, 60, 60, 80), outline=(0, 0, 0), width=3)
dr.text(P(r[0] + 0.3, r[1] + 0.3), 'L0 SOS', fill=(0, 0, 0), font=FS)
r = crt('E3')
dr.rectangle([P(r[0], r[1]), P(r[2], r[3])], fill=(230, 180, 40, 150), outline=(160, 120, 0), width=3)
dr.text(P(r[0] + 0.4, r[1] + 0.4), 'RA (mặt trên)', fill=(110, 80, 0), font=FS)

# pad (mặt trên đỏ nhạt, xuyên lỗ vòng đen)
for f in b.GetFootprints():
    for p in f.Pads():
        x, y = xy(p.GetPosition())
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            dr.ellipse([P(x - 0.8, y - 0.8), P(x + 0.8, y + 0.8)], fill=(200, 160, 60), outline=(0, 0, 0))
        elif p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and f.GetReference()[0] in 'RCDQ':
            bb = p.GetBoundingBox()
            dr.rectangle([P(mm(bb.GetX()) - OX, mm(bb.GetY()) - OY), P(mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY)], fill=(200, 60, 60))

# L1: AD8232
o = xy(fp['U4'].GetPosition())
vx1, vy1, vx2, vy2 = AD8232_VIEN
dr.rectangle([P(o[0] + vx1, o[1] + vy1), P(o[0] + vx2, o[1] + vy2)], fill=(220, 30, 30, 35), outline=(220, 30, 30), width=4)
dr.text(P(o[0] + 2.6, o[1] + vy2 - 2.2), 'L1 AD8232 (cao 8,5 mm)', fill=(200, 20, 20), font=F)

# L2: màn tròn
c = xy(fp['U5'].GetPosition())
R = GC9A01_R
dashed_circle(c, R, (130, 0, 180), 4)
dashed_circle(c, 16.2, (130, 0, 180), 2)
tab = (c[0] - GC9A01_TAB_W / 2, c[1] + 14.0, c[0] + GC9A01_TAB_W / 2, c[1] - R + GC9A01_DAI)
dashed_rect(tab, (130, 0, 180), 3)
dr.text(P(c[0] - 6.5, c[1] - R + 1.2), 'L2 màn GC9A01 (trên cùng)', fill=(120, 0, 170), font=F)

# chú thích
lx = M + BW * K + 30
lines = [
    ('Đồng hồ sức khỏe - mạch v2.0', (0, 0, 0), FB),
    (f'Bảng {BW:.1f} x {BH:.1f} mm = {BW * BH:.0f} mm²', (0, 0, 0), F),
    ('(bản 1.3: 50 x 62 mm = 3100 mm²)', (90, 90, 90), FS),
    ('', None, F),
    ('L2  màn GC9A01 Ø38,1 (tím, nét đứt)', (120, 0, 170), F),
    ('L1  module AD8232 28 x 35 (đỏ)', (200, 20, 20), F),
    ('L0  pin 20 x 30 x 5 (xám)', (60, 60, 60), F),
    ('L0  XIAO 17,8 x 21 (xanh dương)', (30, 60, 200), F),
    ('L0  nút SOS, pad RA (vàng)', (110, 80, 0), F),
    ('Mặt da: MAX30102, CJMCU, E1, E2', SKIN, F),
    ('      (xanh lá, nét đứt)', SKIN, F),
    ('Mặt da: motor 1027 Ø10 (cam)', (170, 80, 0), F),
    ('Vàng nhạt: vùng cấm đồng anten', (160, 120, 0), F),
    ('Chấm vàng viền đen: lỗ xuyên', (0, 0, 0), F),
    ('Ô đỏ: pad linh kiện dán', (200, 60, 60), F),
    ('', None, F),
    ('Nhìn từ mặt trên (mặt màn hình).', (0, 0, 0), FS),
    ('Pad nút SOS, pogo, motor: TẠM.', (0, 0, 0), FS),
]
y = M
for s, col, f_ in lines:
    if s:
        dr.text((lx, y), s, fill=col, font=f_)
    y += 30
# thước 10 mm
dr.line([P(0, BH + 1.2), P(10, BH + 1.2)], fill=(0, 0, 0), width=3)
dr.text(P(10.5, BH + 0.6), '10 mm', fill=(0, 0, 0), font=FS)
out = os.path.join(PRJ, 'xuat', 'pcb_chong_tang_module.png')
img.save(out)
print('đã lưu', out)
