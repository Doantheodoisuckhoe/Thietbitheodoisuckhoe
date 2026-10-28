# Ve so do cam breadboard 28/10: XIAO + AD8232 + MAX30102 + MAX30205 + GC9A01 + nut SOS
import sys
P = 20; X0 = 90
def X(c): return X0 + (c - 1) * P
RY = {'a':130,'b':150,'c':170,'d':190,'e':210,'f':250,'g':270,'h':290,'i':310,'j':330}
RAIL = {'+':70, '-':90}
MAU = {'3v3':'#e0302d','gnd':'#222','sda':'#1f7ae0','scl':'#e3b100','ecg':'#2e9e48','sos':'#8a2bb5',
       'spi':'#f07c00','blk':'#c2185b'}
W = 1420
def pt(h):
    if h[0] in '+-': return (X(int(h[1:])), RAIL[h[0]])
    return (X(int(h[1:])), RY[h[0]])

# (so, tu, den, mau, mo ta, cong, vi tri so tren day 0..1)
DAY = [
 (1,'a6','+6','3v3','3V3 của XIAO',0,0.5),
 (2,'a5','-5','gnd','GND của XIAO',0,0.5),
 (3,'b8',None,'sos','D9 (SOS): đầu tự do chạm thanh − = bấm',0,0.5),
 (4,'f15','-15','gnd','AD8232 GND',0,0.35),
 (5,'f16','+16','3v3','AD8232 3.3V',0,0.6),
 (6,'h4','h17','ecg','D0 (A0) → OUTPUT',22,0.5),
 (7,'i5','i19','ecg','D1 → LO+',26,0.9),
 (8,'f25','+25','3v3','MAX30102 VIN',0,0.45),
 (9,'f28','-28','gnd','MAX30102 GND',0,0.6),
 (10,'h8','h26','sda','D4 → SDA MAX30102',-34,0.5),
 (11,'i9','i27','scl','D5 → SCL MAX30102',14,0.3),
 (12,'f35','+35','3v3','MAX30205 VCC',0,0.45),
 (13,'f36','-36','gnd','MAX30205 GND',0,0.6),
 (14,'g26','g38','sda','SDA → SDA MAX30205',-26,0.45),
 (15,'h27','h37','scl','SCL → SCL MAX30205',-14,0.62),
 (16,'g36','g40','gnd','GND → A0',-14,0.5),
 (17,'h40','h41','gnd','A0 → A1',-12,0.5),
 (18,'i41','i42','gnd','A1 → A2',-12,0.5),
 (19,'f47','+47','3v3','Màn hình VCC',0,0.45),
 (20,'f48','-48','gnd','Màn hình GND',0,0.6),
 (21,'g47','g51','3v3','VCC → RES (không reset bằng chân)',-16,0.5),
 (22,'a9','h49','spi','D8 → SCL màn hình',0,0.36),
 (23,'a7','h50','spi','D10 → SDA màn hình',0,0.5),
 (24,'a10','i53','spi','D7 → CS màn hình',0,0.64),
 (25,'j10','i52','spi','D6 → DC màn hình',18,0.55),
 (26,'j7','h54','blk','D3 → BLK (đèn nền)',58,0.6),
]
# Duong cong rieng cho day man hinh (bat tu hang a, vong qua tren roi xuong)
DUONG = {
 22: lambda a,b: f"M{a[0]},{a[1]} C{a[0]+60},{a[1]-62} {b[0]-160},{a[1]-70} {b[0]-120},{180} S{b[0]},{b[1]-60} {b[0]},{b[1]}",
}
def duong(so, a, b, cong):
    if b is None:
        return f"M{a[0]},{a[1]} Q{a[0]+40},{a[1]-30} {a[0]+90},{a[1]-38}"
    if so in (22,23,24):
        lift = {22:-52, 23:-40, 24:-30}[so]
        mx = {22:0.55, 23:0.62, 24:0.70}[so]
        xm = a[0] + (b[0]-a[0])*mx
        return (f"M{a[0]},{a[1]} C{a[0]+20},{a[1]+lift} {xm-200},{a[1]+lift} {xm},{a[1]+lift} "
                f"S{b[0]},{b[1]-90} {b[0]},{b[1]}")
    if a[1] == b[1] or abs(a[1]-b[1]) < 30 and abs(a[0]-b[0]) > 30:
        mx = (a[0]+b[0])/2; my = (a[1]+b[1])/2 + cong
        return f"M{a[0]},{a[1]} Q{mx},{my+cong} {b[0]},{b[1]}"
    # day len thanh nguon: hoi cong ngang
    dx = 10 if b[1] < a[1] else -10
    return f"M{a[0]},{a[1]} C{a[0]+dx},{(a[1]+b[1])/2} {b[0]+dx},{(a[1]+b[1])/2} {b[0]},{b[1]}"

def bezier_pt(d, t):
    # lay diem tren duong bang trinh duyet sau; o day tra ve None, dung JS
    return None

svg = []
A = svg.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="620" viewBox="0 0 {W} 620" id="s">')
A('<rect x="48" y="44" width="1324" height="322" rx="12" fill="#efe9dc" stroke="#cfc6b3" stroke-width="2"/>')
# thanh nguon tren
for k,y in RAIL.items():
    col = '#d33' if k=='+' else '#1d3f99'
    A(f'<line x1="92" y1="{y-10 if k=="+" else y+10}" x2="1330" y2="{y-10 if k=="+" else y+10}" stroke="{col}" stroke-width="2"/>')
    A(f'<text x="62" y="{y+5}" font-size="16" font-weight="700" fill="{col}">{"+" if k=="+" else "−"}</text>')
    for c in range(1,63):
        if (c-1)%6==5: continue
        A(f'<rect x="{X(c)-4}" y="{y-4}" width="8" height="8" rx="1.5" fill="#2b2b2b"/>')
A('<text x="1340" y="75" font-size="12" fill="#d33">thanh +</text><text x="1340" y="95" font-size="12" fill="#1d3f99">thanh −</text>')
# ranh giua
A('<rect x="50" y="222" width="1320" height="16" fill="#e2dccd"/>')
for r,y in RY.items():
    A(f'<text x="64" y="{y+4}" font-size="12" fill="#888">{r}</text>')
    A(f'<text x="1344" y="{y+4}" font-size="12" fill="#888">{r}</text>')
    for c in range(1,64):
        A(f'<rect x="{X(c)-4}" y="{y-4}" width="8" height="8" rx="1.5" fill="#2b2b2b"/>')
for c in [1]+list(range(5,64,5)):
    A(f'<text x="{X(c)}" y="114" font-size="11" fill="#888" text-anchor="middle">{c}</text>')
    A(f'<text x="{X(c)}" y="354" font-size="11" fill="#888" text-anchor="middle">{c}</text>')
# thanh nguon duoi (khong dung)
A(f'<text x="{X(1)}" y="386" font-size="11" fill="#888">Thanh nguồn phía dưới (nếu có): không dùng</text>')
# XIAO
A(f'<rect x="{X(4)-16}" y="{RY["c"]-18}" width="{X(10)-X(4)+32}" height="{RY["g"]-RY["c"]+36}" rx="8" fill="#d6dde6" stroke="#5b6b7d" stroke-width="2"/>')
A(f'<rect x="{X(4)-38}" y="{(RY["c"]+RY["g"])/2-18}" width="24" height="36" rx="4" fill="#9aa6b2" stroke="#5b6b7d"/>')
A(f'<text x="{X(4)-26}" y="{(RY["c"]+RY["g"])/2-24}" font-size="10" fill="#555" text-anchor="middle">USB-C</text>')
A(f'<text x="{(X(4)+X(10))/2}" y="{(RY["c"]+RY["g"])/2+2}" font-size="17" font-weight="700" text-anchor="middle" fill="#223">XIAO</text>')
A(f'<text x="{(X(4)+X(10))/2}" y="{(RY["c"]+RY["g"])/2+18}" font-size="10" text-anchor="middle" fill="#556">chip quay lên</text>')
for i,n in enumerate(['5V','GND','3V3','D10','D9','D8','D7']):
    c=4+i; A(f'<circle cx="{X(c)}" cy="{RY["c"]}" r="6" fill="#e7b416" stroke="#9a7a0b"/>')
    A(f'<text x="{X(c)}" y="{RY["c"]+20}" font-size="8" font-weight="700" text-anchor="middle" fill="{"#c00" if n=="5V" else "#223"}">{n}</text>')
for i,n in enumerate(['D0','D1','D2','D3','D4','D5','D6']):
    c=4+i; A(f'<circle cx="{X(c)}" cy="{RY["g"]}" r="6" fill="#e7b416" stroke="#9a7a0b"/>')
    A(f'<text x="{X(c)}" y="{RY["g"]-12}" font-size="9.5" font-weight="700" text-anchor="middle" fill="#223">{n}</text>')

# module duoi board
def module(c0, ten, phu, chan, mau, dung=None, rong_them=0.8):
    x1 = X(c0) - P*rong_them; x2 = X(c0+len(chan)-1) + P*rong_them
    for i,n in enumerate(chan):
        c=c0+i; x=X(c)
        trong = dung is not None and n in dung
        A(f'<line x1="{x}" y1="{RY["j"]}" x2="{x}" y2="460" stroke="{"#bbb" if trong else "#c89a10"}" stroke-width="3"/>')
        A(f'<circle cx="{x}" cy="{RY["j"]}" r="4.5" fill="{"#bbb" if trong else "#c89a10"}"/>')
    A(f'<rect x="{x1}" y="460" width="{x2-x1}" height="104" rx="8" fill="{mau}" stroke="#0003" stroke-width="2"/>')
    for i,n in enumerate(chan):
        x=X(c0+i)
        A(f'<text x="{x+4}" y="468" font-size="10.5" font-weight="700" fill="#fff" transform="rotate(90 {x+4} 468)" opacity="{0.5 if dung and n in dung else 1}">{n}</text>')
    A(f'<text x="{(x1+x2)/2}" y="532" font-size="15" font-weight="700" fill="#fff" text-anchor="middle">{ten}</text>')
    A(f'<text x="{(x1+x2)/2}" y="550" font-size="10.5" fill="#fffd" text-anchor="middle">{phu}</text>')
    return x1,x2
module(15,'AD8232','điện tim ECG',['GND','3.3V','OUTPUT','LO−','LO+','SDN'],'#b8393a',dung=['LO−','SDN'])
A(f'<text x="{X(18)}" y="{RY["i"]+5}" font-size="16" font-weight="700" fill="#c00" text-anchor="middle">✕</text>')
module(25,'MAX30102','dây đực–cái',['VIN','SDA','SCL','GND'],'#3a3a3a',rong_them=1.0)
A(f'<text x="{(X(25)+X(28))/2}" y="578" font-size="10" fill="#555" text-anchor="middle">module đen 2 hàng chân</text>')
module(35,'MAX30205','CJMCU-30205',['VCC','GND','SCL','SDA','OS','A0','A1','A2'],'#2d6a3a',dung=['OS'])
module(47,'GC9A01','màn tròn 1,28"',['VCC','GND','SCL','SDA','RES','DC','CS','BLK'],'#1e4f8a')
# dien cuc
for i,(t,col) in enumerate([('Đỏ = RA','#d22'),('Xanh lá = LA','#2a9d3a'),('Vàng = RL','#d9a400')]):
    y=478+i*30
    A(f'<path d="M{X(15)-18},{512} C{X(15)-40},{512} {X(15)-60},{y} {X(15)-82},{y}" stroke="{col}" stroke-width="3" fill="none"/>')
    A(f'<circle cx="{X(15)-90}" cy="{y}" r="8" fill="#fff" stroke="{col}" stroke-width="3"/>')
    A(f'<text x="{X(15)-104}" y="{y+5}" font-size="12.5" font-weight="700" fill="{col}" text-anchor="end">{t}</text>')
A(f'<circle cx="{X(15)-18}" cy="512" r="4" fill="#222"/>')
A(f'<text x="{X(15)-120}" y="590" font-size="10.5" fill="#666">cáp 3 điện cực → jack 3,5 mm</text>')

# day
for so,a,b,m,_,cong,t in DAY:
    pa = pt(a); pb = pt(b) if b else None
    d = duong(so,pa,pb,cong)
    A(f'<path class="day" data-so="{so}" data-t="{t}" d="{d}" stroke="{MAU[m]}" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.92"/>')
    A(f'<rect x="{pa[0]-5}" y="{pa[1]-5}" width="10" height="10" rx="2" fill="{MAU[m]}"/>')
    if pb: A(f'<rect x="{pb[0]-5}" y="{pb[1]-5}" width="10" height="10" rx="2" fill="{MAU[m]}"/>')
    else:
        A(f'<circle cx="{pa[0]+90}" cy="{pa[1]-38}" r="7" fill="#fff" stroke="{MAU[m]}" stroke-width="3" stroke-dasharray="3 2"/>')
A('<g id="nhan"></g></svg>')
open(sys.argv[1],'w').write('\n'.join(svg))

# bang day
import json
json.dump([[so,a,b or 'tự do',m,mt] for so,a,b,m,mt,_,_ in DAY], open(sys.argv[2],'w'), ensure_ascii=False)
json.dump(MAU, open(sys.argv[3],'w'))
