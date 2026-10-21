# Dựng PCB 2 lớp cho bản mạch module: đặt linh kiện, đi dây bằng bộ định tuyến lưới, đổ GND
import os, sys, math, heapq, time, uuid
import numpy as np
import pcbnew
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, findall

PRJ = r'C:\DoAnTotNghiep\hardware\pcb_module'
NAME = 'dong_ho_module'
FPLIB = r'C:\Program Files\KiCad\10.0\share\kicad\footprints'
NETFILE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Admin\AppData\Local\Temp\net.net'
OX, OY = 100.0, 100.0          # gốc toạ độ bảng trong KiCad
BW, BH = 50.0, 62.0            # kích thước bảng (mm)
CORNER = 3.0
MM = pcbnew.FromMM
def mm(v):
    return pcbnew.ToMM(v)
def V(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

# ---------------------------------------------------------------- netlist
net = parse(open(NETFILE, encoding='utf-8').read())[0]
comps = {}
for c in findall(find(net, 'components'), 'comp'):
    ref = str(find(c, 'ref')[1])
    de = find(c, 'description')
    comps[ref] = dict(value=str(find(c, 'value')[1]), fp=str(find(c, 'footprint')[1]),
                      ts=str(find(c, 'tstamps')[1]), desc=str(de[1]) if de and len(de) > 1 else '')
nets = {}
for n in findall(find(net, 'nets'), 'net'):
    nm = str(find(n, 'name')[1])
    nodes = [(str(find(x, 'ref')[1]), str(find(x, 'pin')[1])) for x in findall(n, 'node')]
    nets[nm] = nodes

# ---------------------------------------------------------------- bảng
board = pcbnew.NewBoard(os.path.join(PRJ, NAME + '.kicad_pcb'))
board.SetCopperLayerCount(2)
ds = board.GetDesignSettings()
ds.m_MinClearance = MM(0.25)
ds.m_TrackMinWidth = MM(0.3)
ds.m_ViasMinSize = MM(0.8)
ds.m_MinThroughDrill = MM(0.4)
ds.m_CopperEdgeClearance = MM(0.4)
ds.m_HoleClearance = MM(0.25)
ds.m_HoleToHoleMin = MM(0.5)
ds.m_ViasMinAnnularWidth = MM(0.2)

netinfo = {}
for nm in nets:
    ni = pcbnew.NETINFO_ITEM(board, nm)
    board.Add(ni)
    netinfo[nm] = ni
padnet = {}
for nm, nodes in nets.items():
    for ref, pin in nodes:
        padnet[(ref, pin)] = nm

POWER = {'GND', '+3V3', '+5V', '/VCHG', '/VBAT+', '/VBAT-', '/MOTOR_N'}

# ---------------------------------------------------------------- đặt linh kiện
# ref: (x, y, góc, mặt dưới?)   toạ độ trong khung bảng 50x62, gốc góc trên-trái, nhìn từ mặt trên
PLACE = {
    'U1': (32.62, 18.12, 180, False),     # XIAO: chân 1 (D0) ở dưới-phải, đầu anten sát mép trên
    'U2': (32.62, 23.0, 180, True),         # MAX30102 mặt da
    'U3': (16.11, 56.5, 0, True),       # CJMCU-30205 mặt da
    'U4': (37.0, 7.5, 0, False),          # pad dây AD8232
    'U5': (2.8, 7.4, 0, False),           # pad dây màn GC9A01
    'E1': (41.0, 32.0, 0, True),          # điện cực LA
    'E2': (9.0, 32.0, 0, True),           # điện cực RL
    'J6': (47.6, 22.0, 0, False),         # dây RA -> vít
    'J5': (2.8, 21.9, 90, False),        # nút SOS (2 pad ngang)
    'R4': (2.6, 18.6, 0, False),
    'C9': (6.0, 18.6, 0, False),
    'C7': (9.4, 18.6, 0, False),
    'C8': (12.8, 18.6, 0, False),
    'D2': (37.4, 16.8, 0, False),
    'D3': (42.3, 16.8, 0, False),
    'R3': (46.6, 16.4, 90, False),
    'C5': (37.0, 20.4, 0, False),
    'C6': (40.4, 20.4, 0, False),
    'C1': (28.0, 20.2, 0, False),         # dưới thân XIAO, sát chân VIN của MAX30102
    'C2': (24.6, 20.2, 0, False),
    'D1': (47.6, 28.0, 90, False),
    'Q1': (47.6, 34.0, 90, False),
    'R2': (47.6, 38.0, 90, False),
    'J1': (47.6, 42.6, 0, False),         # motor (THT, ngoài vùng điện cực mặt dưới)
    'R1': (47.6, 50.0, 90, False),
    'D5': (2.4, 28.0, 270, False),
    'D4': (2.4, 34.6, 270, False),
    'J2': (2.4, 42.6, 0, False),          # chân sạc pogo
    'J3': (8.6, 58.6, 0, False),          # JST pin
    'C3': (19.6, 60.2, 0, False),
    'C4': (23.0, 60.2, 0, False),
    'J4': (23.73, 9.5, 270, False),       # dây sang BAT+/BAT- của XIAO
    'H1': (3.5, 3.5, 0, False), 'H2': (46.5, 3.5, 0, False),
    'H3': (3.5, 58.5, 0, False), 'H4': (46.5, 58.5, 0, False),
}

def libpath(lib):
    if lib == 'DoAnModule':
        return os.path.join(PRJ, 'lib', 'DoAnModule.pretty')
    return os.path.join(FPLIB, lib + '.pretty')

fps = {}
for ref, c in comps.items():
    lib, name = c['fp'].split(':')
    fp = pcbnew.FootprintLoad(libpath(lib), name)
    if fp is None:
        raise SystemExit('không tải được ' + c['fp'])
    fp.SetFPIDAsString(c['fp'])
    fp.SetReference(ref)
    fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH('/' + c['ts']))
    fp.SetSheetname('dong_ho_module')
    fp.SetField('Description', c['desc']); fp.SetLibDescription(c['desc'])
    fp.SetSheetfile(NAME + '.kicad_sch')
    board.Add(fp)
    x, y, a, bot = PLACE[ref]
    fp.SetPosition(V(x, y))
    if bot:
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(a)
    for p in fp.Pads():
        k = (ref, p.GetNumber())
        if k in padnet and padnet[k] in netinfo:
            p.SetNet(netinfo[padnet[k]])
    fps[ref] = fp

for ref, fp in fps.items():
    rf = fp.Reference()
    if ref[0] in 'RCDQH' or ref in ('J1', 'J2', 'J5'):
        rf.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
REFPOS = {'U1': (25.0, 16.2), 'U5': (11.0, 5.6), 'U4': (46.0, 11.0), 'J4': (25.0, 12.0)}
for ref, (x, y) in REFPOS.items():
    fps[ref].Reference().SetPosition(V(x, y))
    fps[ref].Reference().SetTextAngleDegrees(0)
if '--bbox' in sys.argv:
    for ref in ('U1', 'U2', 'U3', 'E1', 'E2', 'J3', 'J5', 'U4', 'U5'):
        bb = fps[ref].GetCourtyard(pcbnew.B_CrtYd if fps[ref].IsFlipped() else pcbnew.F_CrtYd).BBox()
        print(ref, 'courtyard', round(mm(bb.GetX()) - OX, 2), round(mm(bb.GetY()) - OY, 2), round(mm(bb.GetRight()) - OX, 2), round(mm(bb.GetBottom()) - OY, 2))
if '--dump' in sys.argv:
    for ref, fp in sorted(fps.items()):
        for p in fp.Pads():
            c = p.GetPosition()
            print(ref, p.GetNumber(), round(pcbnew.ToMM(c.x) - OX, 2), round(pcbnew.ToMM(c.y) - OY, 2), p.GetNetname())

# ---------------------------------------------------------------- viền bảng (chữ nhật bo góc)
def edge_seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
def edge_arc(cx, cy, sx, sy, ang):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetCenter(V(cx, cy)); s.SetStart(V(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
r = CORNER
edge_seg(r, 0, BW - r, 0); edge_seg(BW, r, BW, BH - r); edge_seg(BW - r, BH, r, BH); edge_seg(0, BH - r, 0, r)
edge_arc(BW - r, r, BW - r, 0, 90)
edge_arc(BW - r, BH - r, BW, BH - r, 90)
edge_arc(r, BH - r, r, BH, 90)
edge_arc(r, r, 0, r, 90)

# ---------------------------------------------------------------- vùng cấm
ANT = (18.6, 0.0, 31.4, 4.6)        # dưới anten XIAO: không dây, không via, không đổ đồng (cả 2 lớp)
BAT = (5.0, 24.5, 45.0, 54.5)       # chỗ đặt pin 40x30 mm ở mặt trên: không đặt linh kiện

def rule_area(rect, layers, tracks, vias, fill, footprints, name):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowZoneFills(fill)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(footprints)
    z.SetZoneName(name)
    o = z.Outline(); o.NewOutline()
    x1, y1, x2, y2 = rect
    for (x, y) in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        o.Append(MM(OX + x), MM(OY + y))
    board.Add(z)

rule_area(ANT, [pcbnew.F_Cu, pcbnew.B_Cu], True, True, True, False, 'Anten XIAO')
rule_area(BAT, [pcbnew.F_Cu], False, False, False, True, 'Pin LiPo 603040')

# ---------------------------------------------------------------- bộ định tuyến lưới
G = 0.2
NX, NY = int(BW / G) + 1, int(BH / G) + 1
XS = np.arange(NX) * G
YS = np.arange(NY) * G
CLR = 0.25
EDGE = 0.4
MARGIN = 0.08
VIA_R = 0.4
VIA_DRILL = 0.4

def mm(v):
    return pcbnew.ToMM(v)

# hình đồng: (loại, tham số, net, các lớp {0: F, 1: B})
shapes = []
pad_info = {}   # (ref,num) -> dict
for ref, fp in fps.items():
    for p in fp.Pads():
        c = p.GetPosition()
        cx, cy = mm(c.x) - OX, mm(c.y) - OY
        lay = set()
        if p.IsOnLayer(pcbnew.F_Cu): lay.add(0)
        if p.IsOnLayer(pcbnew.B_Cu): lay.add(1)
        nm = p.GetNetname()
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            d = mm(p.GetDrillSize().x) / 2
            shapes.append(('c', (cx, cy, d), '#HOLE', {0, 1}))
            continue
        bb = p.GetBoundingBox()
        if p.GetShape(pcbnew.F_Cu if 0 in lay else pcbnew.B_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
            sh = ('c', (cx, cy, mm(p.GetSize(pcbnew.F_Cu if 0 in lay else pcbnew.B_Cu).x) / 2))
        else:
            sh = ('r', (mm(bb.GetX()) - OX, mm(bb.GetY()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY))
        shapes.append((sh[0], sh[1], nm, lay))
        pad_info[(ref, p.GetNumber())] = dict(sh=sh, lay=lay, net=nm, c=(cx, cy))

def dist_field(kind, prm, i0, i1, j0, j1):
    X = XS[i0:i1][None, :]
    Y = YS[j0:j1][:, None]
    if kind == 'c':
        cx, cy, rr = prm
        return np.hypot(X - cx, Y - cy) - rr
    if kind == 'r':
        x1, y1, x2, y2 = prm
        dx = np.maximum(np.maximum(x1 - X, X - x2), 0)
        dy = np.maximum(np.maximum(y1 - Y, Y - y2), 0)
        return np.hypot(dx, dy)
    if kind == 's':
        x1, y1, x2, y2, w = prm
        vx, vy = x2 - x1, y2 - y1
        L2 = vx * vx + vy * vy
        if L2 == 0:
            t = np.zeros_like(X + Y)
        else:
            t = np.clip(((X - x1) * vx + (Y - y1) * vy) / L2, 0, 1)
        return np.hypot(X - (x1 + t * vx), Y - (y1 + t * vy)) - w / 2

def bbox(kind, prm):
    if kind == 'c':
        cx, cy, rr = prm; return cx - rr, cy - rr, cx + rr, cy + rr
    if kind == 'r':
        return prm
    x1, y1, x2, y2, w = prm
    return min(x1, x2) - w / 2, min(y1, y2) - w / 2, max(x1, x2) + w / 2, max(y1, y2) + w / 2

def mark(arr, kind, prm, infl):
    x1, y1, x2, y2 = bbox(kind, prm)
    i0 = max(0, int((x1 - infl) / G) - 1); i1 = min(NX, int((x2 + infl) / G) + 2)
    j0 = max(0, int((y1 - infl) / G) - 1); j1 = min(NY, int((y2 + infl) / G) + 2)
    if i0 >= i1 or j0 >= j1:
        return
    d = dist_field(kind, prm, i0, i1, j0, j1)
    arr[j0:j1, i0:i1] |= d < infl

def edge_mask(infl):
    X = XS[None, :]; Y = YS[:, None]
    m = (X < infl) | (Y < infl) | (X > BW - infl) | (Y > BH - infl)
    # góc bo
    for cx, cy in ((CORNER, CORNER), (BW - CORNER, CORNER), (CORNER, BH - CORNER), (BW - CORNER, BH - CORNER)):
        inq = ((X - cx) * (cx - BW / 2) >= 0) & ((Y - cy) * (cy - BH / 2) >= 0)
        m |= inq & (np.hypot(X - cx, Y - cy) > CORNER - infl)
    return m

def rect_mask(rect, infl):
    x1, y1, x2, y2 = rect
    X = XS[None, :]; Y = YS[:, None]
    return (X > x1 - infl) & (X < x2 + infl) & (Y > y1 - infl) & (Y < y2 + infl)
# ---------------------------------------------------------------- bộ định tuyến thương lượng (kiểu PathFinder)
# Mỗi vòng: gỡ và đi lại từng net; ô bị nhiều net dùng chung bị phạt dần cho tới khi hết xung đột.
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
SQ2 = math.sqrt(2)
VIA_COST = float(os.environ.get('VIA_COST', '6'))
BOTTOM_COST = float(os.environ.get('BOTTOM_COST', '1.3'))
INF = float('inf')
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
pad_shapes = list(shapes)

def cells_in(sh, lay, blk, shrink=0.05):
    kind, prm = sh
    x1, y1, x2, y2 = bbox(kind, prm)
    out = []
    for i in range(max(0, int(x1 / G)), min(NX, int(x2 / G) + 2)):
        for j in range(max(0, int(y1 / G)), min(NY, int(y2 / G) + 2)):
            x, y = i * G, j * G
            if kind == 'c':
                inside = math.hypot(x - prm[0], y - prm[1]) <= prm[2] - shrink
            else:
                inside = prm[0] + shrink <= x <= prm[2] - shrink and prm[1] + shrink <= y <= prm[3] - shrink
            if inside:
                for l in lay:
                    if not blk[l][j, i]:
                        out.append((l, j, i))
    return out

def static_maps(netname, hw):
    infl = CLR + hw + MARGIN
    blk = [edge_mask(EDGE + hw + MARGIN) | rect_mask(ANT, hw + MARGIN) for _ in range(2)]
    via = edge_mask(EDGE + VIA_R + MARGIN) | rect_mask(ANT, VIA_R + MARGIN)
    near = [np.zeros((NY, NX), bool) for _ in range(2)]
    for kind, prm, nm, lay in pad_shapes:
        if nm == '#HOLE':
            for l in (0, 1):
                mark(blk[l], kind, prm, CLR + hw + MARGIN)
            mark(via, kind, prm, 0.5 + VIA_R + MARGIN)
            continue
        if nm != netname:
            for l in lay:
                mark(blk[l], kind, prm, infl)
                mark(near[l], kind, prm, infl + 0.4)
            mark(via, kind, prm, CLR + VIA_R + MARGIN)
        else:
            mark(via, kind, prm, VIA_R + 0.1)
    via |= blk[0] | blk[1]
    return blk, via, near

class Net:
    pass

NETS = {}
for nm in netinfo:
    pads = [(k, v) for k, v in pad_info.items() if v['net'] == nm]
    if len(pads) < 2:
        continue
    n = Net()
    n.name = nm
    n.w = 0.5 if nm in POWER else 0.3
    n.pads = pads
    n.blk, n.via, n.near = static_maps(nm, n.w / 2)
    n.segs, n.vias, n.cells, n.vcells = [], [], [], []
    n.ownT = [np.zeros((NY, NX), np.int16) for _ in range(4)]   # [lớp0 sig, lớp1 sig, lớp0 pwr, lớp1 pwr]
    n.ownV = [np.zeros((NY, NX), np.int16) for _ in range(2)]
    NETS[nm] = n

occT = [np.zeros((NY, NX), np.int16) for _ in range(4)]
occV = [np.zeros((NY, NX), np.int16) for _ in range(2)]
hist = [np.zeros((NY, NX), np.float32) for _ in range(2)]

def dilate(n):
    """Tính vùng chiếm chỗ của net n (để net khác tránh) từ các đoạn và via."""
    T = [np.zeros((NY, NX), bool) for _ in range(4)]
    Vv = [np.zeros((NY, NX), bool) for _ in range(2)]
    for (l, x1, y1, x2, y2) in n.segs:
        prm = (x1, y1, x2, y2, n.w)
        mark(T[l], 's', prm, CLR + 0.15 + MARGIN)
        mark(T[2 + l], 's', prm, CLR + 0.25 + MARGIN)
        mark(Vv[l], 's', prm, CLR + VIA_R + MARGIN)
    for (x, y) in n.vias:
        prm = (x, y, VIA_R)
        for l in (0, 1):
            mark(T[l], 'c', prm, CLR + 0.15 + MARGIN)
            mark(T[2 + l], 'c', prm, CLR + 0.25 + MARGIN)
            mark(Vv[l], 'c', prm, max(CLR + VIA_R, 0.5 + VIA_R) + MARGIN)   # khoảng cách lỗ-lỗ 0,5 mm
    for k in range(4):
        n.ownT[k] = T[k].astype(np.int16)
    for k in range(2):
        n.ownV[k] = Vv[k].astype(np.int16)

def rip(n):
    for k in range(4):
        occT[k] -= n.ownT[k]
        n.ownT[k][:] = 0
    for k in range(2):
        occV[k] -= n.ownV[k]
        n.ownV[k][:] = 0
    n.segs, n.vias, n.cells, n.vcells = [], [], [], []

def commit(n):
    dilate(n)
    for k in range(4):
        occT[k] += n.ownT[k]
    for k in range(2):
        occV[k] += n.ownV[k]

def path_to_geom(path):
    segs, vias = [], []
    k = 0
    while k < len(path) - 1:
        l, j, i = path[k]
        l2, j2, i2 = path[k + 1]
        if l2 != l:
            vias.append((i * G, j * G)); k += 1; continue
        d = (i2 - i, j2 - j)
        m = k + 1
        while m < len(path) - 1:
            l3, j3, i3 = path[m + 1]
            lm, jm, im = path[m]
            if l3 != l or (i3 - im, j3 - jm) != d:
                break
            m += 1
        le, je, ie = path[m]
        segs.append((l, i * G, j * G, ie * G, je * G))
        k = m
    return segs, vias

def astar(cm, vc, starts, targets, goal, maxexp=3_000_000):
    gx, gy = goal
    best = {}
    prev = {}
    h0 = []
    cnt = 0
    def hh(i, j):
        dx, dy = abs(i - gx), abs(j - gy)
        return max(dx, dy) + (SQ2 - 1) * min(dx, dy)
    for (l, j, i) in starts:
        for d in range(8):
            k = (l, j, i, d)
            best[k] = 0.0; prev[k] = None
            heapq.heappush(h0, (hh(i, j), 0.0, cnt, k)); cnt += 1
    while h0:
        f, g, _, k = heapq.heappop(h0)
        if g > best.get(k, INF):
            continue
        l, j, i, d = k
        if (l, j, i) in targets:
            path = []
            while k is not None:
                path.append(k[:3]); k = prev[k]
            path.reverse()
            out = []
            for p in path:
                if not out or out[-1] != p:
                    out.append(p)
            return out
        cnt += 1
        if cnt > maxexp:
            return None
        row = cm[l]
        for nd in range(8):
            turn = (nd - d) % 8
            if turn in (3, 4, 5):
                continue
            dx, dy = DIRS[nd]
            ni, nj = i + dx, j + dy
            if ni < 0 or nj < 0 or ni >= NX or nj >= NY:
                continue
            m = row[nj][ni]
            if m == INF:
                continue
            if dx and dy and row[j][ni] == INF and row[nj][i] == INF:
                continue
            c = SQ2 if (dx and dy) else 1.0
            if turn in (1, 7):
                c += 0.3
            elif turn in (2, 6):
                c += 1.0
            ng = g + c * m
            nk = (l, nj, ni, nd)
            if ng < best.get(nk, INF):
                best[nk] = ng; prev[nk] = k
                heapq.heappush(h0, (ng + hh(ni, nj), ng, cnt, nk))
        v = vc[j][i]
        if v == INF:
            continue
        nl = 1 - l
        if cm[nl][j][i] == INF:
            continue
        ng = g + v
        nk = (nl, j, i, d)
        if ng < best.get(nk, INF):
            best[nk] = ng; prev[nk] = k
            heapq.heappush(h0, (ng + hh(i, j), ng, cnt, nk))
    return None

def route_one(n, pf):
    sig = 0 if n.w < 0.4 else 2
    cm = []
    for l in (0, 1):
        oth = (occT[sig + l] - n.ownT[sig + l]).astype(np.float32)
        m = (1.0 + hist[l]) * (1.0 + pf * oth) + n.near[l] * 0.6
        if l == 1:
            m = m * BOTTOM_COST
        m = np.where(n.blk[l], np.inf, m)
        cm.append(m.tolist())
    ov = (occV[0] - n.ownV[0] + occV[1] - n.ownV[1]).astype(np.float32)
    vcm = VIA_COST * (1.0 + 0.5 * (hist[0] + hist[1])) * (1.0 + pf * ov)
    vcm = np.where(n.via, np.inf, vcm).tolist()
    pads = list(n.pads)
    cx = sum(v['c'][0] for k, v in pads) / len(pads); cy = sum(v['c'][1] for k, v in pads) / len(pads)
    pads.sort(key=lambda kv: math.hypot(kv[1]['c'][0] - cx, kv[1]['c'][1] - cy))
    def pcells(v):
        st = cells_in(v['sh'], v['lay'], n.blk)
        if not st:
            i, j = round(v['c'][0] / G), round(v['c'][1] / G)
            st = [(l, j, i) for l in v['lay']]
        return st
    tree = [pads[0]]
    targets = set(pcells(pads[0][1]))
    todo = pads[1:]
    ok = True
    while todo:
        todo.sort(key=lambda kv: min(math.hypot(kv[1]['c'][0] - t[1]['c'][0], kv[1]['c'][1] - t[1]['c'][1]) for t in tree))
        k, v = todo.pop(0)
        near = min(tree, key=lambda t: math.hypot(v['c'][0] - t[1]['c'][0], v['c'][1] - t[1]['c'][1]))
        starts = pcells(v)
        if set(starts) & targets:
            tree.append((k, v)); targets.update(starts); continue
        path = astar(cm, vcm, starts, targets, (round(near[1]['c'][0] / G), round(near[1]['c'][1] / G)))
        if path is None:
            ok = False
            print('   không đi được', n.name, k, flush=True)
            continue
        segs, vias = path_to_geom(path)
        n.segs += segs; n.vias += vias
        n.cells += [p for p in path]
        n.vcells += [(j, i) for (x, y) in vias for (j, i) in [(round(y / G), round(x / G))]]
        targets.update(path); targets.update(starts)
        tree.append((k, v))
    return ok

def conflicts(n):
    sig = 0 if n.w < 0.4 else 2
    bad = []
    for (l, j, i) in n.cells:
        if occT[sig + l][j, i] - n.ownT[sig + l][j, i] > 0:
            bad.append((l, j, i))
    for (j, i) in n.vcells:
        for l in (0, 1):
            if occV[l][j, i] - n.ownV[l][j, i] > 0:
                bad.append((l, j, i))
    return bad

def negotiate(order, iters):
    pf = 0.5
    todo = list(order)
    for it in range(iters):
        t0 = time.time()
        failed = []
        for nm in todo:
            n = NETS[nm]
            rip(n)
            if not route_one(n, pf):
                failed.append(nm)
            commit(n)
        tot = 0
        bad_nets = []
        for nm, n in NETS.items():
            b = conflicts(n)
            if b:
                bad_nets.append(nm); tot += len(b)
                for (l, j, i) in b:
                    hist[l][max(0, j - 1):j + 2, max(0, i - 1):i + 2] += 0.4
        print(f'vòng {it + 1}: xung đột {tot} ô trên {len(bad_nets)} net, thiếu {failed}, pf={pf:.2f} ({time.time() - t0:.0f}s)', flush=True)
        if tot == 0 and not failed:
            return True
        pf *= 1.5
        todo = [nm for nm in order if nm in set(bad_nets) | set(failed)]
    return False

def emit():
    for n in NETS.values():
        for (l, x1, y1, x2, y2) in n.segs:
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(MM(n.w)); t.SetLayer(LAYERS[l])
            t.SetNet(netinfo[n.name]); board.Add(t)
        for (x, y) in n.vias:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(V(x, y)); v.SetDrill(MM(VIA_DRILL)); v.SetWidth(MM(2 * VIA_R))
            v.SetNet(netinfo[n.name]); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(v)

def stitch():
    n = NETS['GND']
    free = ~n.via & (occV[0] - n.ownV[0] == 0) & (occV[1] - n.ownV[1] == 0)
    # tránh xa đồng net khác thêm 0,5 mm để chắc có đồng GND hai lớp quanh via
    pts = []
    for y in np.arange(2.0, BH - 1.0, 3.5):
        for x in np.arange(2.0, BW - 1.0, 3.5):
            i, j = int(round(x / G)), int(round(y / G))
            win = free[max(0, j - 3):j + 4, max(0, i - 3):i + 4]
            if win.size and win.all():
                pts.append((i * G, j * G))
                free[max(0, j - 6):j + 7, max(0, i - 6):i + 7] = False
    for (x, y) in pts:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y)); v.SetDrill(MM(VIA_DRILL)); v.SetWidth(MM(2 * VIA_R))
        v.SetNet(netinfo['GND']); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(v)
    print('via khâu GND:', len(pts))

if '--noroute' not in sys.argv:
    # net nhiều chân, dài trước
    def span(nm):
        xs = [v['c'][0] for k, v in NETS[nm].pads]; ys = [v['c'][1] for k, v in NETS[nm].pads]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))
    order = sorted(NETS, key=lambda nm: -span(nm))
    ok = negotiate(order, int(os.environ.get('VONG', '40')))
    print('KẾT QUẢ:', 'sạch' if ok else 'CÒN XUNG ĐỘT')
    emit()
    stitch()
# ---------------------------------------------------------------- đổ đồng GND hai lớp
def gnd_zone(layer, prio):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(netinfo['GND'])
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName('GND ' + ('trên' if layer == pcbnew.F_Cu else 'dưới'))
    o = z.Outline(); o.NewOutline()
    for (x, y) in ((0, 0), (BW, 0), (BW, BH), (0, BH)):
        o.Append(MM(OX + x), MM(OY + y))
    board.Add(z)
    return z

if '--nozone' not in sys.argv:
    gnd_zone(pcbnew.F_Cu, 0)
    gnd_zone(pcbnew.B_Cu, 0)

# ---------------------------------------------------------------- chữ trên lụa
def silk(s, x, y, size=0.8, layer=pcbnew.F_SilkS, rot=0, just=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(0.15 if size >= 1 else 0.12))
    if rot:
        t.SetTextAngleDegrees(rot)
    if layer in (pcbnew.B_SilkS, pcbnew.B_Fab):
        t.SetMirrored(True)
    if just < 0:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif just > 0:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    board.Add(t)

def comment_rect(rect, layer):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    s.SetStart(V(rect[0], rect[1])); s.SetEnd(V(rect[2], rect[3]))
    s.SetLayer(layer); s.SetWidth(MM(0.12)); board.Add(s)

comment_rect(BAT, pcbnew.Cmts_User)
comment_rect(BAT, pcbnew.F_Fab)
silk('PIN LiPo 603040', 25, 38.0, 1.2)
silk('40 x 30 x 6 mm', 25, 40.2, 1.0)
silk('(dán băng keo cách điện)', 25, 42.2, 0.8)
silk('ANTEN', 25, 2.4, 0.8)
silk('ĐỒNG HỒ SỨC KHỎE', 25, 46.5, 1.0)
silk('v1.0  10/2026', 25, 48.5, 0.8)
silk('MẶT DA', 25, 40.5, 1.2, pcbnew.B_SilkS)
silk('LA', 41.0, 22.9, 1.0, pcbnew.B_SilkS)
silk('RL', 9.0, 22.9, 1.0, pcbnew.B_SilkS)
silk('J2 SẠC', 3.2, 40.4, 0.7)
silk('+', 4.4, 42.6, 0.8)
silk('J1 MOTOR', 46.4, 40.4, 0.7)
silk('+', 45.6, 42.6, 0.8)
silk('SOS', 8.3, 21.9, 0.8)
silk('J5', 10.8, 21.9, 0.8)
silk('BAT-  BAT+', 22.46, 7.0, 0.7)
silk('RA', 45.6, 22.0, 0.7)
silk('+', 8.6, 55.5, 0.8)

if '--nozone' not in sys.argv and '--nofill' not in sys.argv:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
pcbnew.SaveBoard(os.path.join(PRJ, NAME + '.kicad_pcb'), board)
print('đã lưu')
