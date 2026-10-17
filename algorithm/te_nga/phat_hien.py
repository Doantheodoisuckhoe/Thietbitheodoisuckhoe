"""Thuat toan phat hien te nga ban dau (dua tren nguong), chay tren cac file CSV trong data/imu.

Chay: python phat_hien.py                 (tat ca file trong data/imu)
      python phat_hien.py file1.csv ...   (cac file chi dinh)
Nhan cua file la phan ten truoc ngay-gio (vd di_bo_20261017_153000.csv -> di_bo); nhan 'nga' la te nga that.

Mot lan te nga can du 4 dieu kien quanh mot cu va cham:
  1. Va cham: do lon gia toc (SVM) vuot NGUONG_VA_CHAM.
  2. Giam trong luc: trong 1 giay truoc va cham, SVM xuong duoi NGUONG_ROI (nguoi bat dau roi).
     Nga that cua nguoi khong co pha roi tu do ro rang nhu tha roi do vat, nen nguong nay de cao.
  3. Nam yen: tu 1 den 3 giay sau va cham, SVM it dao dong (do lech chuan < DO_LECH_NAM_YEN).
  4. Doi tu the: huong trong luc truoc va sau khi nga lech nhau hon GOC_DOI_TU_THE.
Cac nguong duoi day la gia tri khoi dau; can chinh lai khi co them du lieu.
"""
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

TAN_SO = 100  # mau/giay sau khi lay mau lai
NGUONG_VA_CHAM = 2.5  # g
NGUONG_ROI = 0.75  # g
DO_LECH_NAM_YEN = 0.2  # g
GOC_DOI_TU_THE = 30  # do

THU_MUC = Path(__file__).resolve().parents[2] / "data" / "imu"


def doc_file(ten):
    """Doc file CSV, tra ve danh sach (ax, ay, az) theo g, lay mau lai deu TAN_SO mau/giay theo t_ms.

    Bo phan dau file truoc khoang trong thoi gian lon nhat (> 200 ms): do la du lieu cu con
    trong bo dem tu truoc luc bat dau ghi. Lay mau lai giup file ghi o tan so khac 100 Hz
    (vd ban sketch cu) van dung duoc cac nguong thoi gian.
    """
    with open(ten, newline="") as f:
        dong = [(int(r["t_ms"]), (float(r["ax"]), float(r["ay"]), float(r["az"])))
                for r in csv.DictReader(f)]
    for i in range(len(dong) - 1, 0, -1):
        if dong[i][0] - dong[i - 1][0] > 200:
            dong = dong[i:]
            break
    if len(dong) < 2:
        return [v for _, v in dong]
    buoc = 1000 / TAN_SO
    ket_qua, j, t = [], 0, dong[0][0]
    while t <= dong[-1][0]:
        while dong[j + 1][0] < t:
            j += 1
        (t0, v0), (t1, v1) = dong[j], dong[j + 1]
        k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
        ket_qua.append(tuple(a + (b - a) * k for a, b in zip(v0, v1)))
        t += buoc
    return ket_qua


def do_lon(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def do_lech_chuan(ds):
    tb = sum(ds) / len(ds)
    return math.sqrt(sum((x - tb) ** 2 for x in ds) / len(ds))


def trung_binh(vs):
    return tuple(sum(v[i] for v in vs) / len(vs) for i in range(3))


def goc(a, b):
    c = sum(x * y for x, y in zip(a, b)) / (do_lon(a) * do_lon(b))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def phat_hien(gia_toc):
    """Tra ve (co_nga, thoi_diem_va_cham_giay, ly_do) cho cu va cham dau tien thoa dieu kien."""
    svm = [do_lon(v) for v in gia_toc]
    n = len(svm)
    ly_do = "khong co va cham"
    k = 0
    while k < n:
        if svm[k] <= NGUONG_VA_CHAM:
            k += 1
            continue
        # Lay dinh cua cu va cham trong 0,2 giay.
        k = max(range(k, min(n, k + TAN_SO // 5)), key=lambda i: svm[i])
        truoc = svm[max(0, k - TAN_SO):k]
        sau = svm[k + TAN_SO:k + 3 * TAN_SO]
        if not truoc or min(truoc) >= NGUONG_ROI:
            ly_do = "khong giam trong luc truoc va cham"
        elif len(sau) < TAN_SO:
            ly_do = "file ket thuc qua som sau va cham"
        elif do_lech_chuan(sau) >= DO_LECH_NAM_YEN:
            ly_do = "khong nam yen sau va cham"
        elif k < TAN_SO * 3 // 2:
            ly_do = "file bat dau qua sat va cham"
        else:
            g = goc(trung_binh(gia_toc[k - TAN_SO * 3 // 2:k - TAN_SO // 2]),
                    trung_binh(gia_toc[k + TAN_SO:k + 3 * TAN_SO]))
            if g > GOC_DOI_TU_THE:
                return True, k / TAN_SO, f"doi tu the {g:.0f} do"
            ly_do = f"tu the chi doi {g:.0f} do"
        k += TAN_SO
    return False, None, ly_do


def main():
    files = [Path(p) for p in sys.argv[1:]] or sorted(THU_MUC.glob("*.csv"))
    if not files:
        print(f"Chua co file nao trong {THU_MUC}")
        return
    thong_ke = defaultdict(lambda: [0, 0])  # nhan -> [so file, so lan bao nga]
    for f in files:
        nhan = re.sub(r"_\d{8}_\d{6}$", "", f.stem)
        gia_toc = doc_file(f)
        co, t, ly_do = phat_hien(gia_toc)
        thong_ke[nhan][0] += 1
        thong_ke[nhan][1] += co
        lon_nhat = max(map(do_lon, gia_toc)) if gia_toc else 0.0
        ket_qua = f"BAO NGA luc {t:.2f}s ({ly_do})" if co else f"khong ({ly_do})"
        print(f"{f.name:40s} SVM max {lon_nhat:5.2f} g -> {ket_qua}")
    print("\nTong hop theo nhan:")
    for nhan, (tong, bao) in sorted(thong_ke.items()):
        dung = bao if nhan == "nga" else tong - bao
        print(f"  {nhan:15s} {tong:3d} file, bao nga {bao:3d}, dung {dung}/{tong}")


if __name__ == "__main__":
    main()
