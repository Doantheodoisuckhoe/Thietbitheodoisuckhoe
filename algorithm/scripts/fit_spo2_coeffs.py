"""Fit lại đường cong SpO2(R) từ dữ liệu đo song song với máy kẹp ngón.

Mỗi lần đo SpO2, firmware gửi kèm tỉ số R (xem log USB "#SPO2 R=...") —
ghi lại R cùng giá trị máy kẹp ngón vào CSV:

    ratio,spo2_ref
    0.52,98
    0.55,97
    ...

    python scripts/fit_spo2_coeffs.py spo2_calib.csv
Sau đó chép hệ số vào SPO2_COEF_A/B/C trong firmware/health_watch/config.h.

Lưu ý: người khoẻ hầu như chỉ có SpO2 95–100% nên dữ liệu rất hẹp; fit bậc 2
trên dải hẹp dễ sai khi SpO2 thấp. Nếu dữ liệu hẹp, dùng --order 1 hoặc chỉ
chỉnh hệ số c (bù lệch) và ghi rõ hạn chế trong báo cáo.
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hwalgo.spo2 import DEFAULT_COEFFS, arms, fit_coeffs, spo2_from_ratio  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_file")
    ap.add_argument("--order", type=int, default=2, choices=[1, 2])
    args = ap.parse_args()
    r, s = [], []
    with open(args.csv_file, newline="") as f:
        for row in csv.DictReader(f):
            r.append(float(row["ratio"]))
            s.append(float(row["spo2_ref"]))
    before = arms([spo2_from_ratio(x) for x in r], s)
    coeffs = fit_coeffs(r, s, args.order)
    after = arms([spo2_from_ratio(x, coeffs) for x in r], s)
    print(f"n = {len(r)}, dải SpO2 tham chiếu {min(s):.0f}–{max(s):.0f}%")
    print(f"Hệ số mặc định {DEFAULT_COEFFS}: Arms = {before:.2f}%")
    print(f"Hệ số mới  a={coeffs[0]:.4f} b={coeffs[1]:.4f} c={coeffs[2]:.4f}: Arms = {after:.2f}%")
    print("\nChép vào config.h:")
    print(f"#define SPO2_COEF_A ({coeffs[0]:.4f}f)\n#define SPO2_COEF_B ({coeffs[1]:.4f}f)\n#define SPO2_COEF_C ({coeffs[2]:.4f}f)")
    if np.ptp(s) < 5:
        print("\nCẢNH BÁO: dải SpO2 tham chiếu quá hẹp (< 5%), hệ số chỉ đáng tin quanh dải này.")


if __name__ == "__main__":
    main()
