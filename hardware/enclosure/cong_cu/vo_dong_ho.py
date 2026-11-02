# Vo dong ho v3 cho mach module 1.3 (50,1 x 62,1 mm). CadQuery, don vi mm.
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
# v3 (01/11/2026): lam mong ~26 -> ~18 mm. Gia dinh DA LAM buoc 1:
#   XIAO han thang xuong mach (khong header cai), AD8232 da thao jack + header (han day 30 AWG),
#   cac header J1/J2/J4/J5/J6 khong cam chan duc cao: han day/linh kien truc tiep vao lo.
DAY = 1.2                              # be day day vo (v2: 1,5)
CHAN = 3.0                             # cot do mach = cao MAX30102 3 mm (v2: 3,5)
Z_PCB = DAY + CHAN                     # mat duoi mach
Z_PCB_TREN = Z_PCB + 1.6
Z_CHIA = Z_PCB_TREN + 1.0              # mat ghep vo day / nap
# So do that 01/11/2026 (MINH):
#   XIAO han thang: ~7 mm tren mat mach (v2 co header cai: 16,5 mm)
#   AD8232 bo jack: ~2,5 mm, dat chong tren pin 5,5 mm + mut 0,5 mm (hoac chi Kapton)
#   Man GC9A01 7 chan: tron D 35 mm, day 3 mm, them tai chan 7 x 23 mm o 1 ben
CAO_XIAO = 7.0
MUT = 0.5                              # mut / Kapton duoi pin (v2: 1,0)
CAO_AD8232 = 2.5
CAO_PIN_AD8232 = MUT + 5.5 + CAO_AD8232
MAN_D, MAN_DAY = 35.0, 3.0
TAI_MAN_RONG, TAI_MAN_DAI = 8.0, 23.0  # tai chan man (de du 1 mm)
LO_MAN_D = MAN_D + 0.3                 # lo nap vua khit man (ho 0,15 mm moi ben)
GO_MAN = 0.5                           # go do man (vanh 1,5 mm duoi mep man), nam trong khe 0,5 mm tren AD8232
NAP = 1.5
# Man lap phang mat nap (nhu dong ho that): khong co nhua de len kinh -> mat tren man = mat tren vo.
Z_MAN = max(Z_PCB_TREN + CAO_PIN_AD8232 + GO_MAN,          # man nam tren go, go tren AD8232
            Z_PCB_TREN + CAO_XIAO + 0.5 + NAP - MAN_DAY)   # long nap phai cao hon dinh XIAO
Z_TREN = Z_MAN + MAN_DAY
# v3: XIAO han thang chi cao ~7 mm (dinh 12,8 < mat duoi man 14,8) nen man dat GIUA mat dong ho, nam chong len XIAO.
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

# cua so MAX30102 (U2 tam (25,05; 30,05) KiCad): lo 13 x 9, bac 15 x 11 sau 0,7 mm (mica 0,5-0,7 mm), vanh giu mica 0,5 mm
mx, my = 25.05, yk(30.05)
day = day.cut(cq.Workplane('XY').center(mx, my).rect(13, 9).extrude(DAY + 0.1))
day = day.cut(cq.Workplane('XY').workplane(offset=0.5).center(mx, my).rect(15, 11).extrude(DAY))
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
# lo man vua khit D 35,3 xuyen nap: kinh man phang mat nap; vanh om man + go do man 0,5 mm (rong 1,5 mm) o duoi
nap = nap.cut(cq.Workplane('XY').workplane(offset=Z_TREN - NAP - 0.1).center(MAN_CX, MAN_CY).circle(LO_MAN_D / 2).extrude(NAP + 0.2))
vanh = (cq.Workplane('XY').workplane(offset=Z_MAN).center(MAN_CX, MAN_CY)
        .circle(LO_MAN_D / 2 + 1.2).circle(LO_MAN_D / 2).extrude(Z_TREN - NAP - Z_MAN))
vanh = vanh.union(cq.Workplane('XY').workplane(offset=Z_MAN - GO_MAN).center(MAN_CX, MAN_CY)
                  .circle(LO_MAN_D / 2 + 1.2).circle(MAN_D / 2 - 1.5).extrude(GO_MAN))
# tai chan man (7 chan RST..VCC) quay ve ben trai: cat vanh cho tai lot qua, them go do tai
x_tai = MAN_CX - MAN_D / 2 - TAI_MAN_RONG / 2 + 2.0
vanh = vanh.cut(cq.Workplane('XY').workplane(offset=Z_MAN - 0.1).center(x_tai, MAN_CY)
                .rect(TAI_MAN_RONG + 4.0, TAI_MAN_DAI + 0.6).extrude(MAN_DAY + 1))
nap = nap.union(vanh)
# hoc duoi mat nap cho tai chan man (tai day 1,6 mm nam sat mat duoi man): nap con 1,2 mm o vung tai
nap = nap.cut(cq.Workplane('XY').workplane(offset=Z_MAN - GO_MAN - 0.1).center(x_tai, MAN_CY)
              .rect(TAI_MAN_RONG + 4.0, TAI_MAN_DAI + 0.6).extrude(GO_MAN + 0.1 + 1.8))
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
# Nut SOS: nut nhan goc vuong 6 x 6 chan cam (do that: cao 10 mm tu dinh num toi day kim loai, rong 7, dai 11 tinh ca chan).
# Num tron xuyen qua thanh trai (lo 3,8 mm), than nut nam trong vo, giu bang khung vuong 6,4 x 6,4 sau 4 mm (dan keo).
# Dat cao hon pin (z 13,1) va cao hon header J5 trong file STEP (z ~15,1); duoi man (z 21,6).
# v3: long nap thap (tran nap z = Z_TREN - NAP) -> nut nam sat tran; doi len y KiCad 16,4 (tren J5 5,5 mm) de khung
# khong cham pin (mep pin y 37,6) va khong cham chan header J5 (cao toi z 14,3). Day nut han vao J5.
SOS_Y, SOS_Z = yk(15.2), Z_TREN - NAP - 4.2   # y KiCad 15,2: khung khong cham tai chan man (man o giua)
x_trong_trai = CX - BW / 2 - HO
nap = nap.cut(cq.Workplane('YZ').workplane(offset=x_trai - 1).center(SOS_Y, SOS_Z).circle(1.9).extrude(TUONG + HO + 2))
khung_sos = (cq.Workplane('YZ').workplane(offset=x_trong_trai - 0.01).center(SOS_Y, SOS_Z)
             .rect(8.4, 8.4).rect(6.4, 6.4).extrude(4.0))
khung_sos = khung_sos.cut(cq.Workplane('YZ').workplane(offset=x_trong_trai - 0.1).center(SOS_Y + 3.7, SOS_Z).rect(1.2, 4.0).extrude(4.2))  # khe ra chan
nap = nap.union(khung_sos)
nap = nap.cut(cq.Workplane('YZ').workplane(offset=x_phai - TUONG - 1).center(yk(22.05), Z_CHIA + 5.0).circle(1.1).extrude(TUONG + 2))  # RA M2

# ---------------- Xuat file ----------------
os.makedirs(OUT, exist_ok=True)
cq.exporters.export(day, os.path.join(OUT, 'vo_day.step'))
cq.exporters.export(nap, os.path.join(OUT, 'vo_nap.step'))
cq.exporters.export(day, os.path.join(OUT, 'vo_day.stl'), tolerance=0.02, angularTolerance=0.1)
cq.exporters.export(nap, os.path.join(OUT, 'vo_nap.stl'), tolerance=0.02, angularTolerance=0.1)

pcb = cq.importers.importStep(PCB_STEP).translate((-100, 162, Z_PCB))

# Khoi gia lap cac module KHONG co trong file STEP mach (kich thuoc do that) de kiem va cham
def khoi(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').workplane(offset=z0).center((x0 + x1) / 2, (y0 + y1) / 2).rect(x1 - x0, y1 - y0).extrude(z1 - z0)
z_pin = Z_PCB_TREN + MUT
mo_phong = {
    'XIAO': khoi(15.9, 34.2, yk(22.6), yk(0.0), Z_PCB_TREN, Z_PCB_TREN + CAO_XIAO),
    'pin_45x30': khoi(5.0, 50.0, yk(54.5), yk(24.5), z_pin, z_pin + 5.5),
    'AD8232': khoi(9.0, 45.0, yk(54.5), yk(24.5), z_pin + 5.5, Z_PCB_TREN + CAO_PIN_AD8232),
    'man_GC9A01': (cq.Workplane('XY').workplane(offset=Z_MAN).center(MAN_CX, MAN_CY).circle(MAN_D / 2).extrude(MAN_DAY)
                   .union(khoi(x_tai - TAI_MAN_RONG / 2 + 1.0, MAN_CX - MAN_D / 2 + 2, MAN_CY - TAI_MAN_DAI / 2, MAN_CY + TAI_MAN_DAI / 2, Z_MAN, Z_MAN + 1.6))),
}
for ten, k in mo_phong.items():
    for ten_vo, vo in (('vo_day', day), ('vo_nap', nap)):
        v = vo.val().intersect(k.val()).Volume()
        if v > 0.01:
            print(f'CANH BAO va cham {ten} x {ten_vo}: {v:.2f} mm3')
print('kiem tra module gia lap: xong')
# than nut SOS (6 x 6, sau ~7 mm vao trong) phai nam lot trong khung, khong cham pin / AD8232 / man
than_sos = khoi(x_trong_trai, x_trong_trai + 7.0, SOS_Y - 3.0, SOS_Y + 3.0, SOS_Z - 3.0, SOS_Z + 3.0)
for ten, k in mo_phong.items():
    v = than_sos.val().intersect(k.val()).Volume()
    if v > 0.01:
        print(f'CANH BAO nut SOS cham {ten}: {v:.2f} mm3')
v = than_sos.val().intersect(pcb.val()).Volume()
print(f'nut SOS x mach: {v:.2f} mm3')
lap = cq.Assembly()
lap.add(day, name='vo_day', color=cq.Color(0.85, 0.85, 0.88))
lap.add(pcb, name='mach_1_3', color=cq.Color(0.1, 0.5, 0.2))
lap.add(nap, name='vo_nap', color=cq.Color(0.3, 0.3, 0.35, 0.6))
for ten, k in mo_phong.items():
    lap.add(k, name=ten, color=cq.Color(0.9, 0.6, 0.2))
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
tat_ca = day.union(pcb)
for k in mo_phong.values():
    tat_ca = tat_ca.union(k)
for ten, obj, hd in (('xem_lap_rap', tat_ca, (1.0, -1.3, 1.8)),
                     ('xem_canh_chong_lop', tat_ca.union(nap), (0.0, -1.0, 0.0)),
                     ('xem_day_mat_da', day, (0.3, -0.5, -1.0)),
                     ('xem_nap', nap, (-1.0, -1.4, 1.3))):
    cq.exporters.export(obj, os.path.join(OUT, ten + '.svg'),
                        opt={'width': 900, 'height': 700, 'projectionDir': hd, 'showHidden': False, 'strokeWidth': 0.4})
print('xong')
