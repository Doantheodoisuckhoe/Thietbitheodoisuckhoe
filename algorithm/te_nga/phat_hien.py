"""Thuat toan phat hien te nga ban dau (dua tren nguong), chay tren cac file CSV trong data/imu.

Chay: python phat_hien.py                 (tat ca file trong data/imu)
      python phat_hien.py file1.csv ...   (cac file chi dinh)
Nhan cua file la phan ten truoc ngay-gio (vd di_bo_20261017_153000.csv -> di_bo); nhan 'nga' la te nga that.

Mot lan te nga = 3 giai doan noi tiep nhau:
  1. Roi tu do: do lon gia toc (SVM) giam duoi NGUONG_ROI trong it nhat THOI_GIAN_ROI.
  2. Va cham: trong CUA_SO_VA_CHAM sau do, SVM vuot NGUONG_VA_CHAM.
  3. Nam yen: tu 1 den 3 giay sau va cham, SVM gan 1 g va it dao dong.
Cac nguong duoi day la gia tri khoi dau theo tai lieu; can chinh lai theo du lieu nhom thu duoc.
"""
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

TAN_SO = 100  # mau/giay
NGUONG_ROI = 0.6  # g
THOI_GIAN_ROI = 0.06  # giay
CUA_SO_VA_CHAM = 1.0  # giay
NGUONG_VA_CHAM = 2.5  # g
DO_LECH_NAM_YEN = 0.2  # g, do lech chuan cua SVM khi nam yen

THU_MUC = Path(__file__).resolve().parents[2] / "data" / "imu"


def doc_svm(ten):
    with open(ten, newline="") as f:
        return [math.sqrt(float(r["ax"]) ** 2 + float(r["ay"]) ** 2 + float(r["az"]) ** 2)
                for r in csv.DictReader(f)]


def do_lech_chuan(ds):
    tb = sum(ds) / len(ds)
    return math.sqrt(sum((x - tb) ** 2 for x in ds) / len(ds))


def phat_hien(svm):
    """Tra ve (co_nga, thoi_diem_va_cham_giay, svm_lon_nhat)."""
    n = len(svm)
    can_roi = int(THOI_GIAN_ROI * TAN_SO)
    i = 0
    while i < n:
        if svm[i] >= NGUONG_ROI:
            i += 1
            continue
        j = i
        while j < n and svm[j] < NGUONG_ROI:
            j += 1
        if j - i >= can_roi:
            cuoi = min(n, j + int(CUA_SO_VA_CHAM * TAN_SO))
            for k in range(j, cuoi):
                if svm[k] > NGUONG_VA_CHAM:
                    sau = svm[k + TAN_SO:k + 3 * TAN_SO]
                    if len(sau) >= TAN_SO and do_lech_chuan(sau) < DO_LECH_NAM_YEN:
                        return True, k / TAN_SO, max(svm)
                    break
        i = j
    return False, None, max(svm) if svm else 0.0


def main():
    files = [Path(p) for p in sys.argv[1:]] or sorted(THU_MUC.glob("*.csv"))
    if not files:
        print(f"Chua co file nao trong {THU_MUC}")
        return
    thong_ke = defaultdict(lambda: [0, 0])  # nhan -> [so file, so lan bao nga]
    for f in files:
        nhan = re.sub(r"_\d{8}_\d{6}$", "", f.stem)
        co, t, lon_nhat = phat_hien(doc_svm(f))
        thong_ke[nhan][0] += 1
        thong_ke[nhan][1] += co
        ket_qua = f"BAO NGA luc {t:.2f}s" if co else "khong"
        print(f"{f.name:40s} SVM max {lon_nhat:5.2f} g -> {ket_qua}")
    print("\nTong hop theo nhan:")
    for nhan, (tong, bao) in sorted(thong_ke.items()):
        dung = bao if nhan == "nga" else tong - bao
        print(f"  {nhan:15s} {tong:3d} file, bao nga {bao:3d}, dung {dung}/{tong}")


if __name__ == "__main__":
    main()
