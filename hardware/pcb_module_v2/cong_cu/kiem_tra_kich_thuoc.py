# Kiểm tra tự động PCB bản 2.0 theo kích thước đo trên module thật (kich_thuoc.py).
# Chạy bằng Python của KiCad 10:
#   "C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\kiem_tra_kich_thuoc.py
# Thoát mã 1 nếu có lỗi.
import os, sys, math, itertools
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kich_thuoc import *

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, 'dong_ho_module_v2.kicad_pcb')
b = pcbnew.LoadBoard(PCB)
mm = pcbnew.ToMM

edge = b.GetBoardEdgesBoundingBox()
W_NET = 0.1   # nét vẽ Edge.Cuts
OX, OY = mm(edge.GetX()) + W_NET / 2, mm(edge.GetY()) + W_NET / 2
BW, BH = mm(edge.GetWidth()) - W_NET, mm(edge.GetHeight()) - W_NET
loi = []
dem = [0]

def ok(dk, msg):
    dem[0] += 1
    if not dk:
        loi.append(msg)

def xy(p):
    return (mm(p.x) - OX, mm(p.y) - OY)

fp = {f.GetReference(): f for f in b.GetFootprints()}
def pads(ref):
    out = {}
    for p in fp[ref].Pads():
        out.setdefault(p.GetNumber(), []).append(xy(p.GetPosition()))
    return out

def d(a, b_):
    return math.hypot(a[0] - b_[0], a[1] - b_[1])

TOL = 0.01

# 1) AD8232: mọi cặp pad đúng khoảng cách đo được, đúng hướng (không lật gương)
P = pads('U4')
for (n1, (_, x1, y1)), (n2, (_, x2, y2)) in itertools.combinations(AD8232_PADS.items(), 2):
    ok(abs(d(P[n1][0], P[n2][0]) - math.hypot(x2 - x1, y2 - y1)) < TOL, f'AD8232 pad {n1}-{n2} sai khoảng cách')
o = P['4'][0]; ra = P['1'][0]
ok(abs(ra[0] - o[0] - 19.05) < TOL and abs(ra[1] - o[1] + 10.033) < TOL, 'AD8232 bị xoay/lật: RA phải ở (+19,05; -10,033) so với GND')
ok(abs(d(P['1'][0], P['3'][0]) - 5.08) < TOL and abs(d(P['4'][0], P['9'][0]) - 12.7) < TOL, 'AD8232 bước chân sai')

# 2) GC9A01: 8 pad bước 2,54, hàng pad cách tâm màn 24,7 mm, 7 pad đầu đối xứng qua tâm
P = pads('U5')
c = xy(fp['U5'].GetPosition())
for i in range(1, 8):
    ok(abs(d(P[str(i)][0], P[str(i + 1)][0]) - 2.54) < TOL, f'GC9A01 bước pad {i}-{i + 1} sai')
for i in range(1, 9):
    ok(abs(P[str(i)][0][1] - c[1] - GC9A01_HANG) < TOL, f'GC9A01 pad {i} không cách tâm 24,7 mm')
ok(abs((P['1'][0][0] + P['7'][0][0]) / 2 - c[0]) < TOL, 'GC9A01: 7 pad không nằm giữa tâm màn')
ok(P['1'][0][0] < P['7'][0][0], 'GC9A01: pad 1 (RST) phải ở bên trái khi nhìn mặt màn')

# 3) XIAO: hai hàng cách 15,24, bước 2,54, đầu anten sát mép bảng
P = pads('U1')
for i in range(1, 7):
    ok(abs(d(P[str(i)][0], P[str(i + 1)][0]) - 2.54) < TOL, f'XIAO bước chân {i}-{i + 1} sai')
ok(abs(d(P['1'][0], P['14'][0]) - XIAO_HANG) < TOL, 'XIAO: hai hàng chân không cách 15,24 mm')
ok(abs(d(P['7'][0], P['8'][0]) - XIAO_HANG) < TOL, 'XIAO: hai hàng chân không song song')
# chân 7/8 ở đầu anten; thân XIAO vượt chân 2,88 mm về phía anten
ant_y = min(P['7'][0][1], P['8'][0][1]) - (18.12 - 15.24)
ok(P['7'][0][1] < P['1'][0][1] and ant_y <= 0.5, f'XIAO: đầu anten phải sát mép trên (cách {ant_y:.2f} mm)')
xiao = (P['14'][0][0] - 1.28, ant_y, P['1'][0][0] + 1.28, ant_y + XIAO_THAN[1])

# 4) Vùng pin (tầng 0, mặt trên) lấy từ vùng cấm của bảng
bat = None
for z in b.Zones():
    if z.GetIsRuleArea() and 'Pin' in z.GetZoneName():
        bb = z.GetBoundingBox()
        bat = (mm(bb.GetX()) - OX, mm(bb.GetY()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY)
ok(bat is not None, 'không thấy vùng pin')
ok(abs((bat[2] - bat[0]) - PIN[0]) < 0.05 and abs((bat[3] - bat[1]) - PIN[1]) < 0.05, f'vùng pin không phải {PIN[0]} x {PIN[1]} mm')

def rect_overlap(a, b_, gap=0.0):
    return not (a[2] + gap <= b_[0] or b_[2] + gap <= a[0] or a[3] + gap <= b_[1] or b_[3] + gap <= a[1])

ok(not rect_overlap(bat, xiao), 'thân XIAO đè lên pin')
P = pads('U4')
ok(bat[1] - P['1'][0][1] >= 3.0 - 1e-6, 'pin phải cách hàng pad RA/LA/RL >= 3 mm')
ok(bat[0] - P['4'][0][0] >= 2.2 - 1e-6, 'pin phải cách cột pad GND..SDN >= 2,2 mm')
for n, lst in P.items():
    for (x, y) in lst:
        ok(not rect_overlap((x - 0.8, y - 0.8, x + 0.8, y + 0.8), bat, 1.0), f'pad AD8232 {n} quá sát pin')

def crt(ref):
    f = fp[ref]
    lay = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
    bb = f.GetCourtyard(lay).BBox()
    return (mm(bb.GetX()) - OX, mm(bb.GetY()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY)

# linh kiện dán mặt trên không nằm trong vùng pin
for ref, f in fp.items():
    if f.IsFlipped() or ref[0] not in 'RCDQ':
        continue
    ok(not rect_overlap(crt(ref), bat), f'{ref} nằm trong vùng pin')
# linh kiện dán dưới thân XIAO phải thấp (chỉ 0805)
for ref, f in fp.items():
    if not f.IsFlipped() and ref[0] in 'RCDQ' and rect_overlap(crt(ref), xiao):
        ok('0805' in f.GetFPIDAsString(), f'{ref} cao quá để nằm dưới thân XIAO (hở 2,5 mm)')

# 5) Mặt da: không chân xuyên lỗ của linh kiện khác nằm dưới thân module / điện cực / motor
MOTOR_C = None
for dw in b.GetDrawings():
    if dw.GetLayer() == pcbnew.B_Fab and dw.GetShape() == pcbnew.SHAPE_T_CIRCLE:
        cc = xy(dw.GetCenter()); MOTOR_C = (cc[0], cc[1], mm(dw.GetRadius()))
ok(MOTOR_C is not None and abs(MOTOR_C[2] * 2 - MOTOR_D) < 0.05, 'không thấy vòng motor 10 mm ở B.Fab')
duoi = {}
for ref in ('U2', 'U3', 'E1', 'E2'):
    ok(fp[ref].IsFlipped(), f'{ref} phải ở mặt dưới')
    duoi[ref] = crt(ref)
for ref, f in fp.items():
    for p in f.Pads():
        if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            continue
        x, y = xy(p.GetPosition())
        for k, r in duoi.items():
            if k != ref:
                ok(not (r[0] - 0.8 < x < r[2] + 0.8 and r[1] - 0.8 < y < r[3] + 0.8), f'chân {ref}.{p.GetNumber()} nằm dưới {k} (mặt da)')
        ok(d((x, y), MOTOR_C) > MOTOR_C[2] + 0.8, f'chân {ref}.{p.GetNumber()} nằm dưới motor')
for k, r in duoi.items():
    cx = min(max(MOTOR_C[0], r[0]), r[2]); cy = min(max(MOTOR_C[1], r[1]), r[3])
    ok(d((cx, cy), MOTOR_C) >= MOTOR_C[2], f'motor đè lên {k}')
ok(MOTOR_C[0] - MOTOR_C[2] >= 0 and MOTOR_C[0] + MOTOR_C[2] <= BW and MOTOR_C[1] + MOTOR_C[2] <= BH, 'motor ra ngoài bảng')
for p in fp['M1'].Pads():
    ok(d(xy(p.GetPosition()), MOTOR_C[:2]) < MOTOR_C[2] + 6, 'pad dây motor quá xa motor')
for a_, b2 in itertools.combinations(duoi, 2):
    ok(not rect_overlap(duoi[a_], duoi[b2]), f'{a_} đè lên {b2} (mặt da)')

# 6) Màn GC9A01 nằm trong bảng và không che nút SOS, điện cực RA (mặt trên)
c = xy(fp['U5'].GetPosition())
R = GC9A01_R
ok(c[0] - R >= -0.01 and c[0] + R <= BW + 0.01 and c[1] - R >= -0.01, 'màn tròn ra ngoài bảng')
ok(c[1] - R + GC9A01_DAI <= BH + 0.01, 'đuôi chân màn ra ngoài bảng')
def circle_hits(r):
    cx = min(max(c[0], r[0]), r[2]); cy = min(max(c[1], r[1]), r[3])
    return d((cx, cy), c) < R
tab = (c[0] - GC9A01_TAB_W / 2, c[1] + 14.0, c[0] + GC9A01_TAB_W / 2, c[1] - R + GC9A01_DAI)
for ref in ('SW1', 'E3'):
    r = crt(ref)
    ok(not circle_hits(r) and not rect_overlap(r, tab), f'màn che {ref}')

# 7) Mép bảng: nút SOS, RA ở mép; pad motor gần mép
r = crt('SW1'); ok(BW - r[2] < 1.0, 'nút SOS không sát mép phải')
r = crt('E3'); ok(r[0] < 1.0, 'điện cực RA không sát mép trái')
ok(min(BW - xy(p.GetPosition())[0] for p in fp['M1'].Pads()) < 2.0, 'pad motor không gần mép')

# 8) Không còn dây pin / dây sang XIAO
nets = set(b.GetNetsByName().keys()) if hasattr(b, 'GetNetsByName') else set()
ok(not any('VBAT' in str(n) for n in nets), 'còn lưới VBAT')
for ref in ('J3', 'J4', 'J1', 'J5', 'J6', 'R4', 'C9'):
    ok(ref not in fp, f'còn {ref} của bản 1.3')

print(f'Bảng {BW:.1f} x {BH:.1f} mm = {BW * BH:.0f} mm2; kiểm {dem[0]} điều kiện, {len(loi)} lỗi')
for m in loi:
    print('  LỖI:', m)
sys.exit(1 if loi else 0)
