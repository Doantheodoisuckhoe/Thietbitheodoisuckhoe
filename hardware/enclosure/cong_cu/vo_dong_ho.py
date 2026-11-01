# Vo dong ho v1 cho mach module 1.3 (50,1 x 62,1 mm). CadQuery, don vi mm.
# He toa do: x sang phai, y len tren (y = 62 - y_kicad), z tu mat da (day vo) len tren.
import sys, os
import cadquery as cq

# Chay: python cong_cu/vo_dong_ho.py v1 [duong_dan_file_step_mach]
# File STEP mach: KiCad PCB Editor -> File -> Export -> STEP (hardware/pcb_module/dong_ho_module.step)
OUT = sys.argv[1]
PCB_STEP = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'pcb_module', 'dong_ho_module.step')

# ---------------- Thong so ----------------
BW, BH, BR = 50.1, 62.1, 3.0          # mach
CX, CY = BW / 2, BH / 2
HO = 0.4                               # khe ho quanh mach
TUONG = 2.0                            # be day thanh vo
OW, OH = BW + 2 * (HO + TUONG), BH + 2 * (HO + TUONG)
OR = BR + HO + TUONG
DAY = 1.5                              # be day day vo
CHAN = 3.5                             # cot do mach (khoang cho MAX30102, MAX30205, D1/Q1 o mat duoi)
Z_PCB = DAY + CHAN                     # mat duoi mach
Z_PCB_TREN = Z_PCB + 1.6
Z_CHIA = Z_PCB_TREN + 1.0              # mat ghep vo day / nap
CAO_XIAO = 12.2                        # header cai 8,5 + XIAO ~3,7
Z_MAN = Z_PCB_TREN + CAO_XIAO + 0.7    # mat duoi module man hinh
MAN_D, MAN_DAY = 38.6, 3.6             # module GC9A01 (do lai thuc te!)
KINH_D = 33.0                          # o nhin (vung hien thi ~32,4 mm)
NAP = 1.5
Z_TREN = Z_MAN + MAN_DAY + NAP
MAN_CX, MAN_CY = CX, CY

def yk(y_kicad):                        # doi toa do y KiCad (huong xuong) sang y len
    return BH - y_kicad

LO_VIT = [(3.55, yk(3.55)), (46.55, yk(3.55)), (3.55, yk(58.55)), (46.55, yk(58.55))]

def hop_bo_goc(w, h, r, z0, z1):
    return (cq.Workplane('XY').workplane(offset=z0).center(CX, CY)
            .rect(w, h).extrude(z1 - z0).edges('|Z').fillet(r))

# ---------------- Vo day (chua mach) ----------------
day = hop_bo_goc(OW, OH, OR, 0, Z_CHIA)
day = day.cut(hop_bo_goc(BW + 2 * HO, BH + 2 * HO, BR + HO, DAY, Z_CHIA + 1))
try:
    day = day.faces('<Z').edges().fillet(1.0)
except Exception:
    pass
# cot do mach + lo moi vit M2 (vit tu ren, lo 1,7 mm)
for x, y in LO_VIT:
    cot = cq.Workplane('XY').workplane(offset=DAY - 0.01).center(x, y).circle(2.6).extrude(CHAN + 0.01)
    day = day.union(cot)
    day = day.cut(cq.Workplane('XY').workplane(offset=0.6).center(x, y).circle(0.85).extrude(Z_PCB))

# cua so MAX30102 (U2 tam (25,05; 30,05) KiCad): lo 13 x 9, bac 15 x 11 sau 1 mm de dat mica 1 mm
mx, my = 25.05, yk(30.05)
day = day.cut(cq.Workplane('XY').center(mx, my).rect(13, 9).extrude(DAY + 0.1))
day = day.cut(cq.Workplane('XY').workplane(offset=DAY - 1.0).center(mx, my).rect(15, 11).extrude(1.1))
# cua so MAX30205 (CJMCU-30205, tam ~ (25; 51,5) KiCad)
day = day.cut(cq.Workplane('XY').center(25.05, yk(51.5)).rect(8, 8).extrude(DAY + 0.1))
# dien cuc E1 (LA) va E2 (RL): hoc 9 x 16 sau 0,6 mm mat ngoai de dan tam thep/dong, lo 2 mm luon day noi len pad
for ex in (41.05, 9.05):
    ey = yk(32.05)
    day = day.cut(cq.Workplane('XY').center(ex, ey).rect(9.4, 16.4).extrude(0.6))
    day = day.cut(cq.Workplane('XY').center(ex, ey).circle(1.0).extrude(DAY + 0.1))

# tai deo day 22 mm (hai dau tren/duoi), lo chot lo xo 1,3 mm
for dau in (1, -1):
    y_mep = CY + dau * OH / 2
    for sx in (-1, 1):
        x = CX + sx * (11.1 + 1.25)
        # tai dai 7 mm: 1 mm an vao thanh vo, 6 mm nho ra ngoai (khong lan vao long vo)
        tai = (cq.Workplane('XY').workplane(offset=0.5).center(x, y_mep + dau * 2.5)
               .rect(2.5, 7.0).extrude(Z_CHIA - 1.0))
        day = day.union(tai)
    chot = (cq.Workplane('YZ').workplane(offset=CX - 14).center(y_mep + dau * 3.8, 4.0)
            .circle(0.65).extrude(28))
    day = day.cut(chot)

# ---------------- Nap (man hinh) ----------------
nap = hop_bo_goc(OW, OH, OR, Z_CHIA, Z_TREN)
nap = nap.cut(hop_bo_goc(BW + 2 * HO, BH + 2 * HO, BR + HO, Z_CHIA - 0.1, Z_TREN - NAP))
try:
    nap = nap.faces('>Z').edges().fillet(1.5)
except Exception:
    pass
# o nhin man hinh + vanh dinh vi module man
nap = nap.cut(cq.Workplane('XY').workplane(offset=Z_TREN - NAP - 0.1).center(MAN_CX, MAN_CY).circle(KINH_D / 2).extrude(NAP + 0.2))
vanh = (cq.Workplane('XY').workplane(offset=Z_MAN).center(MAN_CX, MAN_CY)
        .circle(MAN_D / 2 + 1.2).circle(MAN_D / 2).extrude(Z_TREN - NAP - Z_MAN))
# khe cho chan header / day man (phia pad U5, goc tren-trai)
vanh = vanh.cut(cq.Workplane('XY').workplane(offset=Z_MAN - 0.1).center(MAN_CX - 14, MAN_CY + 14).rect(14, 14).extrude(10))
nap = nap.union(vanh)
# cot vit xuyen nap: lo 2,3 mm, khoet dau vit 4,2 x 2 mm o mat tren
for x, y in LO_VIT:
    cot = cq.Workplane('XY').workplane(offset=Z_PCB_TREN + 0.1).center(x, y).circle(2.6).extrude(Z_TREN - Z_PCB_TREN - 0.1)
    nap = nap.union(cot)
    nap = nap.cut(cq.Workplane('XY').workplane(offset=Z_PCB_TREN).center(x, y).circle(1.15).extrude(Z_TREN))
    nap = nap.cut(cq.Workplane('XY').workplane(offset=Z_TREN - 2.0).center(x, y).circle(2.1).extrude(3))

# lo canh: chan sac pogo (J2, trai), nut SOS (J5, trai), vit thep RA (J6, phai)
def lo_canh(x_mat, y, z, w, h, huong):
    return (cq.Workplane('YZ').workplane(offset=x_mat - (TUONG + HO + 1) if huong < 0 else x_mat - 1)
            .center(y, z).rect(w, h).extrude(TUONG + HO + 2))
x_trai, x_phai = CX - OW / 2, CX + OW / 2
nap = nap.cut(lo_canh(x_trai + TUONG + HO, yk(44.0), Z_CHIA + 3.5, 10, 5, -1))   # pogo (do dau pogo roi chinh)
nap = nap.cut(cq.Workplane('YZ').workplane(offset=x_trai - 1).center(yk(21.95), Z_CHIA + 3.0).circle(1.6).extrude(TUONG + 2))   # SOS
nap = nap.cut(cq.Workplane('YZ').workplane(offset=x_phai - TUONG - 1).center(yk(22.05), Z_CHIA + 5.0).circle(1.1).extrude(TUONG + 2))  # RA M2

# ---------------- Xuat file ----------------
os.makedirs(OUT, exist_ok=True)
cq.exporters.export(day, os.path.join(OUT, 'vo_day.step'))
cq.exporters.export(nap, os.path.join(OUT, 'vo_nap.step'))
cq.exporters.export(day, os.path.join(OUT, 'vo_day.stl'), tolerance=0.02, angularTolerance=0.1)
cq.exporters.export(nap, os.path.join(OUT, 'vo_nap.stl'), tolerance=0.02, angularTolerance=0.1)

pcb = cq.importers.importStep(PCB_STEP).translate((-100, 162, Z_PCB))
lap = cq.Assembly()
lap.add(day, name='vo_day', color=cq.Color(0.85, 0.85, 0.88))
lap.add(pcb, name='mach_1_3', color=cq.Color(0.1, 0.5, 0.2))
lap.add(nap, name='vo_nap', color=cq.Color(0.3, 0.3, 0.35, 0.6))
lap.save(os.path.join(OUT, 'lap_rap_vo_mach.step'))

# Kiem tra va cham vo - mach (the tich phan giao nhau)
pv = pcb.val()
for ten, vo in (('vo_day', day), ('vo_nap', nap)):
    try:
        giao = vo.val().intersect(pv).Volume()
    except Exception as e:
        giao = f'loi {e}'
    print(f'giao {ten} x mach: {giao}')
bb = day.union(nap).val().BoundingBox()
print(f'kich thuoc ngoai (khong tinh tai): {OW:.1f} x {OH:.1f} mm; cao {Z_TREN:.1f} mm; bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}')
print(f'Z: mach {Z_PCB:.1f}-{Z_PCB_TREN:.1f}, ghep {Z_CHIA:.1f}, man {Z_MAN:.1f}-{Z_MAN + MAN_DAY:.1f}, tren {Z_TREN:.1f}')

# Anh xem truoc (SVG)
for ten, obj, hd in (('xem_lap_rap', day.union(nap).union(pcb), (-1.2, -1.6, 1.1)),
                     ('xem_day_mat_da', day, (0.3, -0.5, -1.0)),
                     ('xem_nap', nap, (-1.0, -1.4, 1.3))):
    cq.exporters.export(obj, os.path.join(OUT, ten + '.svg'),
                        opt={'width': 900, 'height': 700, 'projectionDir': hd, 'showHidden': False, 'strokeWidth': 0.4})
print('xong')
