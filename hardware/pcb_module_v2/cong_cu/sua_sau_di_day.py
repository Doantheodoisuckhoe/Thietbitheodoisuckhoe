# Sửa nhỏ sau khi đi dây (không đi dây lại), chạy 1 lần sau gen_pcb.py (kể cả gen_pcb.py --giu-day), trước ap_quy_tac_xuong.py:
#  - đưa tên U1, U3 sang lớp Fab (khỏi đè pad)
#  - dời vài chữ lụa của bảng khỏi chân U3, cắt viền pin quanh chân U3 (cho bảng tạo bằng gen_pcb.py cũ)
#  - nối 2 pad "1" của nút SOS bằng 1 đoạn dây mặt dưới (KiCad coi 2 pad cùng số là 2 điểm cần nối)
#  - bỏ via khâu GND không chạm đồng GND ở cả 2 lớp
#   "C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\sua_sau_di_day.py
import os, pcbnew

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PRJ, 'dong_ho_module_v2.kicad_pcb')
OX, OY = 100.0, 100.0
MM = pcbnew.FromMM
mm = pcbnew.ToMM
def V(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}
fps['U1'].Reference().SetLayer(pcbnew.F_Fab)
fps['U3'].Reference().SetLayer(pcbnew.B_Fab)

# 2) chữ lụa của bảng
DOI_CHU = {}   # bản gen_pcb.py hiện tại đã đặt chữ đúng chỗ
for d in list(b.GetDrawings()):
    if d.GetClass() == 'PCB_TEXT' and d.GetText() in DOI_CHU and d.GetLayer() == pcbnew.F_SilkS:
        d.SetPosition(V(*DOI_CHU[d.GetText()]))
    if d.GetClass() == 'PCB_SHAPE' and d.GetLayer() == pcbnew.F_SilkS and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        s, e = d.GetStart(), d.GetEnd()
        x1, y1, x2, y2 = mm(s.x) - OX, mm(s.y) - OY, mm(e.x) - OX, mm(e.y) - OY
        if abs(x1 - 14.1) < 0.01 and abs(x2 - 14.1) < 1.0 and y1 > 27:      # mũi tên PCM cũ
            d.Move(V(9.0 - 14.1 - OX, -OY))
        elif abs(y1 - 34.5) < 0.01 and abs(y2 - 34.5) < 0.01 and x1 < 13.8 and x2 > 16.2:            # viền dưới pin: chừa chân U3
            d.SetEnd(V(13.8, 34.5))
            n = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
            n.SetStart(V(16.2, 34.5)); n.SetEnd(V(x2, 34.5)); n.SetLayer(pcbnew.F_SilkS); n.SetWidth(d.GetWidth())
            b.Add(n)

# 3) nối 2 pad "1" của SW1 (mặt dưới)
p1 = [p for p in fps['SW1'].Pads() if p.GetNumber() == '1']
t = pcbnew.PCB_TRACK(b)
t.SetStart(p1[0].GetPosition()); t.SetEnd(p1[1].GetPosition())
t.SetWidth(MM(0.3)); t.SetLayer(pcbnew.B_Cu); t.SetNet(p1[0].GetNet()); b.Add(t)

# 4) bỏ via GND lơ lửng
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND']
bo = 0
for v in [x for x in b.GetTracks() if x.Type() == pcbnew.PCB_VIA_T and x.GetNetname() == 'GND']:
    pos = v.GetPosition()
    tren = any(z.GetLayer() == pcbnew.F_Cu and z.HitTestFilledArea(pcbnew.F_Cu, pos) for z in zones)
    duoi = any(z.GetLayer() == pcbnew.B_Cu and z.HitTestFilledArea(pcbnew.B_Cu, pos) for z in zones)
    co_day = any(x.Type() == pcbnew.PCB_TRACE_T and x.GetNetname() == 'GND' and (x.GetStart() == pos or x.GetEnd() == pos)
                 for x in b.GetTracks())
    if not co_day and not (tren and duoi):
        b.Remove(v); bo += 1
filler.Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print('đã sửa; bỏ via GND lơ lửng:', bo)
