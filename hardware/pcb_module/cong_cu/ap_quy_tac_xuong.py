# Áp tiêu chuẩn của xưởng mạch trong nước lên bản mạch đã đi dây (bản 1.1 -> 1.2).
# Không đi dây lại: chỉ đổi lỗ khoan, pad, via, khoảng cách phủ đồng và chữ lụa.
# Chạy bằng Python của KiCad 10 (chạy lại nhiều lần vẫn cho cùng kết quả):
#   "C:\Program Files\KiCad\10.0\bin\python.exe" cong_cu\ap_quy_tac_xuong.py
import os, pcbnew

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PRJ, 'dong_ho_module.kicad_pcb')
MM = lambda v: pcbnew.FromMM(round(v, 4))   # làm tròn: 0,3 + 0,6 = 0,8999… sẽ bị cắt còn 0,899999 mm
mm = pcbnew.ToMM
V = pcbnew.VECTOR2I

MUI_KHOAN = [0.3, 0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 1.8, 2.0]   # mũi khoan xưởng có (mm)
VIEN_PAD = 0.6         # pad = lỗ khoan + 0,6 mm (vòng đồng 0,3 mm mỗi bên)
VIA_KHOAN = 0.3        # via: lỗ 0,3 mm, pad 0,9 mm
PHU_DONG = 0.65        # phủ đồng GND cách dây/pad khác lưới >= 25 mil (0,635 mm)
CHU_CAO = 0.8          # chữ lụa cao tối thiểu 0,8 mm để nét 0,2 mm không bị KiCad thu nhỏ
CHU_NET = 0.2          # độ dày nét chữ lụa
DUONG_LUA = 0.15       # nét vẽ lụa tối thiểu
PHIEN_BAN = ('v1.1', 'v1.2')

def mui(d):
    for a in MUI_KHOAN:
        if a >= d - 1e-4:
            return a
    return d

b = pcbnew.LoadBoard(PCB)
ds = b.GetDesignSettings()
ds.m_MinClearance = MM(0.25)          # xưởng cho 0,23; giữ 0,25 cho dư
ds.m_TrackMinWidth = MM(0.2)
ds.m_ViasMinSize = MM(VIA_KHOAN + VIEN_PAD)
ds.m_MinThroughDrill = MM(0.3)
ds.m_CopperEdgeClearance = MM(0.4)    # xưởng cần >= 0,25
ds.m_HoleClearance = MM(0.25)
ds.m_HoleToHoleMin = MM(0.5)
ds.m_ViasMinAnnularWidth = MM(VIEN_PAD / 2)

dem = {'pad': 0, 'via': 0, 'vung': 0, 'chu': 0, 'net': 0}

# 1) Pad xuyên lỗ: lỗ lên mũi khoan gần nhất của xưởng, pad = lỗ + 0,6
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        d = mui(mm(p.GetDrillSize().x))
        m = d + VIEN_PAD
        sz = p.GetSize(pcbnew.F_Cu)
        w, h = mm(sz.x), mm(sz.y)
        if abs(w - h) < 1e-3:
            w = h = m
        elif w < h:
            w = m
        else:
            h = m
        p.SetDrillSize(V(MM(d), MM(d)))
        p.SetSize(pcbnew.F_Cu, V(MM(w), MM(h)))
        dem['pad'] += 1

# 2) Via xuyên lỗ
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        t.SetDrill(MM(VIA_KHOAN))
        for lop in (pcbnew.F_Cu, pcbnew.B_Cu):   # KiCad 10: via đặt cỡ theo từng lớp
            t.SetWidth(lop, MM(VIA_KHOAN + VIEN_PAD))
        dem['via'] += 1

# 3) Phủ đồng GND (bỏ qua vùng cấm)
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    z.SetLocalClearance(MM(PHU_DONG))
    z.SetThermalReliefGap(MM(0.5))
    dem['vung'] += 1

# 4) Chữ và nét trên lớp lụa
LUA = (pcbnew.F_SilkS, pcbnew.B_SilkS)

def sua_chu(t):
    if t.GetLayer() not in LUA:
        return
    s = t.GetTextSize()
    c = max(mm(s.y), CHU_CAO)
    r = max(mm(s.x), CHU_CAO)
    t.SetTextSize(V(MM(r), MM(c)))
    t.SetTextThickness(MM(CHU_NET))
    if t.GetText().startswith(PHIEN_BAN[0]):
        t.SetText(t.GetText().replace(PHIEN_BAN[0], PHIEN_BAN[1], 1))
    dem['chu'] += 1

def sua_net(s):
    if s.GetLayer() in LUA and mm(s.GetWidth()) < DUONG_LUA:
        s.SetWidth(MM(DUONG_LUA))
        dem['net'] += 1

def cast(x):
    return x.Cast() if hasattr(x, 'Cast') else x

def sua(it):
    it = cast(it)
    k = it.GetClass()
    if k in ('PCB_TEXT', 'PCB_FIELD'):
        sua_chu(it)
    elif k == 'PCB_SHAPE':
        sua_net(it)

for it in b.GetDrawings():
    sua(it)
for fp in b.GetFootprints():
    for f in fp.GetFields():
        if f.IsVisible():
            sua_chu(f)
    for it in fp.GraphicalItems():
        sua(it)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print('Đã sửa:', dem)
