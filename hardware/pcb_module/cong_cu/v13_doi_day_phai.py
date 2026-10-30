# Bản 1.2 -> 1.3: pin thật dài 45 mm (45 x 30 x 5,5 mm) nên vùng pin mặt trên nới tới mép phải (x 105-150).
# Bốn linh kiện dán ở dải mép phải (D1, Q1, R1, R2) chuyển xuống mặt dưới, vào khoảng trống
# dưới điện cực E1 và bên trái J1 (x 139-147, y 141-155). J1 (motor, xuyên lỗ) và J6 giữ nguyên chỗ.
# Chạy 1 lần trên bản 1.2 bằng Python của KiCad 10, rồi chạy ap_quy_tac_xuong.py:
#   "C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\v13_doi_day_phai.py
import os, pcbnew

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PRJ, 'dong_ho_module.kicad_pcb')
MM = lambda v: pcbnew.FromMM(round(v, 4))
mm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
b = pcbnew.LoadBoard(PCB)
fp = {f.GetReference(): f for f in b.GetFootprints()}
net = lambda n: b.FindNet(n)
def k(p): return (round(mm(p.x), 2), round(mm(p.y), 2))

# 1) Gỡ dây/via cũ quanh dải phải và vùng đặt mới
xoa = []
for t in b.GetTracks():
    n = t.GetNetname()
    if t.Type() == pcbnew.PCB_VIA_T:
        p = k(t.GetPosition())
        if n in ('/VBAT+', '/MOTOR_N', '/MOTOR_G', '/MOTOR_EN', 'GND') and (
                (p[0] >= 146 and 124 <= p[1] <= 140) or p in ((144.0, 151.0), (140.4, 151.0), (140.4, 147.6), (147.6, 154.4))):
            xoa.append(t)
        continue
    a, c = k(t.GetStart()), k(t.GetEnd())
    if n in ('/MOTOR_N', '/MOTOR_G'):
        xoa.append(t)                                   # hai lưới này chỉ nằm ở mạch motor: đi lại toàn bộ
    elif n == '/MOTOR_EN' and {a, c} == {(144.0, 148.0), (147.0, 151.0)}:
        xoa.append(t)
    elif n == '/VBAT+' and (min(a[0], c[0]) >= 146.5 or {a, c} == {(140.4, 130.4), (146.8, 130.4)}):
        xoa.append(t)
    elif n == 'GND' and max(a[0], c[0]) >= 146 and 124 <= min(a[1], c[1]) and max(a[1], c[1]) <= 140:
        xoa.append(t)
    elif n == 'GND' and {a, c} in ({(146.6, 128.0), (142.0, 123.4)}, {(142.0, 123.4), (142.0, 123.2)}):
        xoa.append(t)
xoa = list({t.m_Uuid.AsString(): t for t in xoa}.values())
for t in xoa:
    b.Remove(t)
print('Đã gỡ', len(xoa), 'dây/via')

# 2) Lật xuống mặt dưới, thử 4 góc xoay và chọn góc cho chân gần vị trí mong muốn nhất
def dat(ref, cx, cy, muon):
    f = fp[ref]
    if f.GetLayer() == pcbnew.F_Cu:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetPosition(V(cx, cy))
    tot = None
    for g in (0, 90, 180, 270):
        f.SetOrientationDegrees(g)
        sai = sum((mm(p.GetPosition().x) - muon[p.GetNumber()][0]) ** 2 + (mm(p.GetPosition().y) - muon[p.GetNumber()][1]) ** 2
                  for p in f.Pads() if p.GetNumber() in muon)
        if tot is None or sai < tot[0]:
            tot = (sai, g)
    f.SetOrientationDegrees(tot[1])
    return {p.GetNumber(): (round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)) for p in f.Pads()}

d1 = dat('D1', 144.4, 144.27, {'1': (144.4, 142.3), '2': (144.4, 146.3)})     # 1 VBAT+ trên, 2 MOTOR_N dưới
q1 = dat('Q1', 144.4, 150.1, {'3': (144.4, 149.2)})                           # D lên phía D1
g_trai = q1['1'][0] < q1['2'][0]                                              # chân G (1) bên trái?
xg, xs = q1['1'][0], q1['2'][0]
yg = q1['1'][1]
# R1 (G - EN) nằm ngang cạnh chân G, đầu EN ra ngoài; R2 (G - GND) nằm ngang ngay dưới R1
huong = -1 if g_trai else 1
r2 = dat('R2', xg + huong * 2.55, yg + 2.45, {'1': (xg + huong * 1.64, yg + 2.45), '2': (xg + huong * 3.46, yg + 2.45)})
r1 = dat('R1', xg + huong * 2.55, yg, {'2': (xg + huong * 1.64, yg), '1': (xg + huong * 3.46, yg)})
for n, p in (('D1', d1), ('Q1', q1), ('R2', r2), ('R1', r1)):
    print(n, p)

# 3) Via và dây mới
def via(x, y, n):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y)); v.SetDrill(MM(0.3))
    for lop in (pcbnew.F_Cu, pcbnew.B_Cu):
        v.SetWidth(lop, MM(0.9))
    v.SetNet(net(n)); b.Add(v)

def day(pts, n, w, lop):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(MM(w))
        t.SetLayer(lop); t.SetNet(net(n)); b.Add(t)

B, F = pcbnew.B_Cu, pcbnew.F_Cu
J1_1, J1_2 = (147.6, 142.6), (147.6, 145.14)
en = r1['1']
VE = (en[0], en[1] - 1.75)                      # via MOTOR_EN ngay trên chân EN của R1
VS = (xs + huong * -1.3 if False else (xs + (1.25 if g_trai else -1.25)), q1['2'][1] + 0.7)   # via GND cạnh chân S
via(*VE, '/MOTOR_EN'); via(*VS, 'GND')

# Mặt dưới
day([d1['1'], (146.5, 142.6), J1_1], '/VBAT+', 0.5, B)
day([d1['2'], (146.3, 145.14), J1_2], '/MOTOR_N', 0.5, B)
day([d1['2'], q1['3']], '/MOTOR_N', 0.5, B)
day([r1['2'], r2['1']], '/MOTOR_G', 0.3, B)
day([q1['1'], r1['2']], '/MOTOR_G', 0.3, B)
day([VE, en], '/MOTOR_EN', 0.3, B)
day([q1['2'], VS], 'GND', 0.5, B)
VR = (r2['2'][0], r2['2'][1] + 1.6); via(*VR, 'GND')
day([r2['2'], VR], 'GND', 0.5, B)
# Mặt trên: VBAT+ từ XIAO xuống J1 chân 1 (dải phải mặt trên giờ trống, nằm dưới pin)
day([(140.4, 130.4), (146.8, 130.4), (147.6, 131.2), (147.6, 141.8)], '/VBAT+', 0.5, F)
# MOTOR_EN: từ dây dọc x = 144 xuống via cạnh R1
day([(144.0, 148.0), (VE[0] + 0.6, 148.0), VE], '/MOTOR_EN', 0.3, F)

# 4) Khung pin 45 x 30 mm và chữ lụa
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_SHAPE' and d.GetShapeStr() == 'Rect' and abs(mm(d.GetEnd().x) - 145) < 0.2 and abs(mm(d.GetStart().x) - 105) < 0.2:
        d.SetEnd(V(150.0, mm(d.GetEnd().y)))
    if d.GetClass() == 'PCB_TEXT':
        s = d.GetText()
        if s == '40 x 30 x 6 mm': d.SetText('45 x 30 x 5.5 mm  (PCM →)')
        if s.startswith('v1.2'): d.SetText(s.replace('v1.2', 'v1.3', 1))
pcbnew.SaveBoard(PCB, b)
print('Đã lưu')
