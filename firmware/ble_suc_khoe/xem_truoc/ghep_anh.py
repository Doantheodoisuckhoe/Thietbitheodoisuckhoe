# Doi cac file .ppm thanh PNG man tron (vien den ngoai vong tron) va ghep 1 tam tong hop.
# Can Pillow: python -m pip install pillow
import glob, os, sys
from PIL import Image, ImageDraw

thu_muc = sys.argv[1] if len(sys.argv) > 1 else '.'
TL = 2                      # phong to 2 lan cho de xem
anh = []
for f in sorted(glob.glob(os.path.join(thu_muc, '*.ppm'))):
    a = Image.open(f).convert('RGB').resize((240 * TL, 240 * TL), Image.NEAREST)
    nen = Image.new('RGB', (240 * TL + 40, 240 * TL + 40), (40, 40, 44))
    mat = Image.new('L', a.size, 0)
    ImageDraw.Draw(mat).ellipse((0, 0, a.size[0] - 1, a.size[1] - 1), fill=255)
    nen.paste(a, (20, 20), mat)
    ImageDraw.Draw(nen).ellipse((16, 16, 240 * TL + 23, 240 * TL + 23), outline=(110, 110, 115), width=4)
    png = f[:-4] + '.png'
    nen.save(png)
    anh.append((os.path.basename(f)[:-4], nen))
    os.remove(f)
if anh:
    cot = 4
    w, h = anh[0][1].size
    hang = (len(anh) + cot - 1) // cot
    tong = Image.new('RGB', (cot * w, hang * (h + 30)), (25, 25, 28))
    for i, (ten, a) in enumerate(anh):
        x, y = (i % cot) * w, (i // cot) * (h + 30)
        tong.paste(a, (x, y))
        ImageDraw.Draw(tong).text((x + 20, y + h + 6), ten, fill=(220, 220, 220))
    tong.save(os.path.join(thu_muc, 'tong_hop_man_hinh.png'))
    print('da ghep', len(anh), 'man')
