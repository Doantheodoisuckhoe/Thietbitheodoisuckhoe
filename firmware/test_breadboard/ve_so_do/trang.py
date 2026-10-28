import json, sys
svg = open('so_do.svg').read()
day = json.load(open('day.json')); mau = json.load(open('mau.json'))
def o(h): return h.replace('+','thanh +').replace('-','thanh −') if h[0] in '+-' and len(h)>1 else h
def nho(h):
    if h[0] in '+-': return 'thanh +' if h[0]=='+' else 'thanh −'
    return h
cot = [day[0:9], day[9:18], day[18:26]]
bang = ''
for c in cot:
    bang += '<table><tr><th>#</th><th>Từ</th><th>Đến</th><th>Nối gì</th></tr>'
    for so,a,b,m,mt in c:
        bang += f'<tr><td><span class="so" style="border-color:{mau[m]}">{so}</span></td><td>{a}</td><td>{nho(b)}</td><td>{mt}</td></tr>'
    bang += '</table>'
chu = [('3V3','3v3'),('GND','gnd'),('SDA (I2C)','sda'),('SCL (I2C)','scl'),('ECG','ecg'),('SOS','sos'),('Màn hình SPI','spi'),('Đèn nền','blk')]
chuthich = ''.join(f'<span><i style="background:{mau[k]}"></i>{t}</span>' for t,k in chu)
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;font-family:"DejaVu Sans",sans-serif;background:#fff;color:#222;width:1420px}}
h1{{font-size:21px;text-align:center;margin:14px 0 0}}
.sub{{text-align:center;font-size:13px;color:#555;margin:4px 0 0}}
svg text{{font-family:"DejaVu Sans",sans-serif}}
.wrap{{display:flex;gap:18px;padding:0 24px}}
table{{border-collapse:collapse;font-size:12.5px;flex:1}}
th{{background:#eef0f3;text-align:left;padding:5px 6px;font-weight:700}}
td{{padding:4px 6px;border-bottom:1px solid #e6e6e6;vertical-align:middle}}
.so{{display:inline-block;width:22px;height:22px;line-height:20px;border-radius:50%;border:2.5px solid;text-align:center;font-weight:700;font-size:11.5px;box-sizing:border-box}}
.chu{{display:flex;gap:22px;justify-content:center;font-size:12.5px;margin:12px 0 4px}}
.chu i{{display:inline-block;width:30px;height:5px;border-radius:3px;margin-right:6px;vertical-align:middle}}
.luu{{margin:10px 24px 16px;border:1.5px dashed #d33;border-radius:8px;padding:8px 14px;font-size:12.8px;line-height:1.55}}
.luu b{{color:#c00}}
.cap{{font-size:13px;font-weight:700;margin:6px 24px 6px}}
</style></head><body>
<h1>Cắm breadboard (28/10/2026): XIAO + AD8232 + MAX30102 + MAX30205 + màn GC9A01 + nút SOS</h1>
<p class="sub">Chân giống firmware <b>ble_suc_khoe</b> và mạch in 1.2. Mỗi dây có số; tra số trong bảng bên dưới.</p>
{svg}
<div class="cap">Bảng dây: cắm đầu 1 vào lỗ "Từ", đầu 2 vào lỗ "Đến". Các lỗ a–e cùng cột nối với nhau, f–j cùng cột nối với nhau.</div>
<div class="wrap">{bang}</div>
<div class="chu">{chuthich}</div>
<div class="luu">
<b>Khác bản cũ (21/10):</b> LO− của AD8232 <b>để trống</b>, không cắm D3 nữa (D3 giờ là đèn nền màn hình). Chỉ LO+ báo tuột điện cực ở D1.
Thêm màn GC9A01: SCL→D8, SDA→D10, CS→D7, DC→D6, BLK→D3, RES nối 3V3.<br>
<b>MAX30102 đen 2 hàng chân</b> không cắm thẳng được (2 hàng chân sẽ bị chập): dùng 4 dây đực–cái từ chân VIN, SDA, SCL, GND (hàng có chữ VIN) vào lỗ j25, j26, j27, j28. Hàng GND RD IRD INT bỏ trống.<br>
Thứ tự chân module của bạn có thể khác hình: <b>luôn cắm theo TÊN chân in trên module</b>. Cáp điện cực của bạn: đỏ = RA, xanh lá = LA, vàng = RL.<br>
<b>Động cơ rung: không cắm vào chân D nào</b> (cần MOSFET như mạch in). Mọi module dùng 3V3, <b>không dùng chân 5V</b>. Rút USB trước khi cắm hoặc đổi dây.
</div>
<script>
const g=document.getElementById('nhan');
for(const p of document.querySelectorAll('path.day')){{
  const L=p.getTotalLength(), q=p.getPointAtLength(L*parseFloat(p.dataset.t));
  const c=p.getAttribute('stroke');
  g.insertAdjacentHTML('beforeend',`<circle cx="${{q.x}}" cy="${{q.y}}" r="10.5" fill="#fff" stroke="${{c}}" stroke-width="2.5"/><text x="${{q.x}}" y="${{q.y+4}}" font-size="11" font-weight="700" text-anchor="middle" fill="#222">${{p.dataset.so}}</text>`);
}}
</script></body></html>'''
open('so_do.html','w').write(html)
