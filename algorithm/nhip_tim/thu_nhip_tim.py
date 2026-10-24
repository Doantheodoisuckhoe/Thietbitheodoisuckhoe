"""Thuat toan dem nhip tim tu song IR cua MAX30102, ban Python giong het firmware ble_suc_khoe.

Cach lam:
  1. Loc IR bang 2 bo loc bac 2: thong cao 0,5 Hz (bo nen troi do ngon tay xe dich, do tho)
     va thong thap 5 Hz (bo nhieu).
  2. Lay dao ham (mau sau tru mau truoc) de lam ro suon len cua moi nhip.
  3. Moi giay, lay 6 giay gan nhat tinh tu tuong quan: dich song di L mau roi so voi chinh no.
     Khi L dung bang 1 chu ky nhip tim thi song trung khop nhat.
  4. Chon dinh tu tuong quan cao nhat trong 0,3-1,5 giay (200-40 lan/phut). Neu co dinh ngan hon
     cao gan bang va dinh chon duoc gap 2-3 lan no, thi lay dinh ngan (tranh dem thieu nhip).
  5. Bo cua so neu 1 giay nao co nang luong gap 8 lan giay khac (cu dong manh)
     hoac dinh tu tuong quan < 0,3 (song khong ro).
  6. Nhip tim = trung vi 3 lan uoc luong gan nhat.

Vi sao doi: do thu ngay 24/10/2026, nen IR troi (~1000 don vi) lon hon ca nhip tim (~500 don vi),
cach tim dinh cu khong bat duoc nhip nao (HR luon = 0).

Chay: python thu_nhip_tim.py           -> thu voi song gia, in nhip tim moi giay
      python thu_nhip_tim.py file.csv  -> doc cot IR (100 mau/giay) tu file CSV cua doc_max30102
Khong can cai thu vien nao.
"""
import csv
import math
import random
import sys

FS = 100
CUA_SO = 600          # 6 giay
TRE_MIN, TRE_MAX = 30, 150


def he_so_loc(f0, loai):
    """Bo loc Butterworth bac 2 (cong thuc bilinear), tra ve (b0, b1, b2, a1, a2)."""
    w = 2 * math.pi * f0 / FS
    alpha = math.sin(w) / (2 / math.sqrt(2))
    c = math.cos(w)
    b = [(1 + c) / 2, -(1 + c), (1 + c) / 2] if loai == "cao" else [(1 - c) / 2, 1 - c, (1 - c) / 2]
    a0 = 1 + alpha
    return (b[0] / a0, b[1] / a0, b[2] / a0, -2 * c / a0, (1 - alpha) / a0)


class Loc:
    def __init__(self, hs):
        self.b0, self.b1, self.b2, self.a1, self.a2 = hs
        self.z1 = self.z2 = 0.0

    def loc(self, x):
        y = self.b0 * x + self.z1
        self.z1 = self.b1 * x - self.a1 * y + self.z2
        self.z2 = self.b2 * x - self.a2 * y
        return y


def uoc_luong(v):
    tb = sum(v) / len(v)
    v = [x - tb for x in v]
    r0 = sum(x * x for x in v)
    if r0 <= 0:
        return 0
    nl = [sum(x * x for x in v[j * 100:(j + 1) * 100]) for j in range(6)]
    if max(nl) > 8 * min(nl):
        return 0
    n = len(v)
    r = {L: sum(v[k] * v[k + L] for k in range(n - L)) / r0 * n / (n - L)
         for L in range(TRE_MIN - 1, TRE_MAX + 2)}
    dinh = [L for L in range(TRE_MIN, TRE_MAX + 1) if r[L] >= r[L - 1] and r[L] >= r[L + 1]]
    if not dinh:
        return 0
    tot = max(dinh, key=lambda L: r[L])
    for L in dinh:
        if L < tot and r[L] > 0.8 * r[tot]:
            k = round(tot / L)
            if k >= 2 and abs(tot / L - k) < 0.15 * k:
                tot = L
                break
    if r[tot] < 0.3:
        return 0
    a, b, c = r[tot - 1], r[tot], r[tot + 1]
    lech = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0
    return round(6000 / (tot + lech))


def dem_nhip(ir):
    """Tra ve danh sach nhip tim moi giay (0 = chua co / song khong ro)."""
    cao, thap = Loc(he_so_loc(0.5, "cao")), Loc(he_so_loc(5, "thap"))
    cao.z1, cao.z2 = -cao.b0 * ir[0], cao.b2 * ir[0]   # tranh giat luc dau
    truoc = 0.0
    song, gan_day, ket_qua, nhip, lan_cuoi = [], [], [], 0, 0
    for i, x in enumerate(ir, 1):
        y = thap.loc(cao.loc(x))
        song.append(y - truoc)
        truoc = y
        song = song[-CUA_SO:]
        if i % 100:
            continue
        if i >= CUA_SO + 200:
            u = uoc_luong(song)
            if u:
                gan_day = (gan_day + [u])[-3:]
                lan_cuoi = i
                if len(gan_day) >= 2:
                    nhip = sorted(gan_day)[len(gan_day) // 2]
        if nhip and i - lan_cuoi > 500:      # 5 giay khong co uoc luong moi
            nhip, gan_day = 0, []
        ket_qua.append(nhip)
    return ket_qua


def song_gia(bpm, bien_do, nhieu, troi, giay=30, hrv=0.05):
    """Song IR gia: moi nhip 1 hop xuong (mau vao lam IR giam) + nhieu + nen troi cham."""
    moc, t = [], 0.0
    while t < giay + 2:
        moc.append(t)
        t += 60 / bpm * (1 + random.gauss(0, hrv))
    ir, j = [], 0
    for i in range(giay * FS):
        tt = i / FS
        while moc[j + 1] <= tt:
            j += 1
        p = (tt - moc[j]) / (moc[j + 1] - moc[j])
        xung = math.exp(-((p - 0.15) / 0.07) ** 2) + 0.25 * math.exp(-((p - 0.45) / 0.08) ** 2)
        ir.append(108000 - bien_do * xung + random.gauss(0, nhieu)
                  + troi * math.sin(2 * math.pi * 0.2 * tt) + 0.5 * troi * math.sin(2 * math.pi * 0.07 * tt + 1))
    return ir


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], newline="") as f:
            ir = [float(d["ir"]) for d in csv.DictReader(r for r in f if not r.startswith("#"))]
        print(dem_nhip(ir))
    else:
        random.seed(3)
        for bpm, bd, nh, tr in [(75, 500, 30, 1000), (60, 300, 50, 1500), (50, 300, 40, 800),
                                (130, 400, 40, 800), (85, 150, 100, 1000)]:
            kq = dem_nhip(song_gia(bpm, bd, nh, tr))
            print(f"that {bpm:3d} lan/phut, nhip {bd}, nhieu {nh}, troi {tr}: {kq[8:]}")
