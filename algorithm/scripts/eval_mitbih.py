"""Đánh giá phát hiện đỉnh R trên MIT-BIH Arrhythmia Database.

Mô phỏng đúng cách thiết bị chạy: tín hiệu được lấy mẫu lại về 250 Hz (như AD8232 trên thiết bị) và xử lý
theo từng đoạn 30 s độc lập (giống 1 lần đo ECG theo yêu cầu).

    python scripts/eval_mitbih.py                 # tải trực tiếp từ PhysioNet (cần mạng)
    python scripts/eval_mitbih.py --local-dir data/mitdb   # đã tải sẵn
    python scripts/eval_mitbih.py --records 100 101 105

Mục tiêu đề cương: phát hiện đúng >= 95% đỉnh R (Se và +P).
"""
import argparse
import os
import sys

import numpy as np
from scipy.signal import resample_poly

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hwalgo.ecg_rpeak import detect_r_peaks, match_beats  # noqa: E402

RECORDS = [
    "100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "111", "112",
    "113", "114", "115", "116", "117", "118", "119", "121", "122", "123", "124", "200",
    "201", "202", "203", "205", "207", "208", "209", "210", "212", "213", "214", "215",
    "217", "219", "220", "221", "222", "223", "228", "230", "231", "232", "233", "234",
]
BEAT_SYMBOLS = set("NLRBAaJSVrFejnE/fQ?")
FS_DEVICE = 250


def load(rec, local_dir):
    import wfdb
    if local_dir:
        path = os.path.join(local_dir, rec)
        return wfdb.rdrecord(path), wfdb.rdann(path, "atr")
    return wfdb.rdrecord(rec, pn_dir="mitdb"), wfdb.rdann(rec, "atr", pn_dir="mitdb")


def evaluate_record(rec, local_dir=None, seg_s=30):
    record, ann = load(rec, local_dir)
    fs = record.fs
    sig = record.p_signal[:, 0]  # MLII
    from math import gcd
    g = gcd(int(fs), FS_DEVICE)
    x = resample_poly(sig, FS_DEVICE // g, int(fs) // g) * 1000.0  # mV -> µV
    ref = np.array([int(round(s * FS_DEVICE / fs)) for s, sym in zip(ann.sample, ann.symbol)
                    if sym in BEAT_SYMBOLS])
    seg = int(seg_s * FS_DEVICE)
    det = []
    for start in range(0, len(x), seg):
        chunk = x[start:start + seg]
        if len(chunk) < FS_DEVICE * 2:
            continue
        det.extend((detect_r_peaks(chunk, FS_DEVICE) + start).tolist())
    return match_beats(det, ref, int(0.15 * FS_DEVICE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", nargs="*", default=RECORDS)
    ap.add_argument("--local-dir", default=None)
    ap.add_argument("--seg", type=float, default=30.0)
    args = ap.parse_args()

    tot = np.zeros(3, dtype=int)
    print(f"{'Bản ghi':>8} {'TP':>7} {'FP':>6} {'FN':>6} {'Se %':>7} {'+P %':>7}")
    for rec in args.records:
        tp, fp, fn = evaluate_record(rec, args.local_dir, args.seg)
        tot += (tp, fp, fn)
        se = 100 * tp / max(1, tp + fn)
        ppv = 100 * tp / max(1, tp + fp)
        print(f"{rec:>8} {tp:>7} {fp:>6} {fn:>6} {se:>7.2f} {ppv:>7.2f}")
    tp, fp, fn = tot
    se = 100 * tp / max(1, tp + fn)
    ppv = 100 * tp / max(1, tp + fp)
    f1 = 2 * se * ppv / max(1e-9, se + ppv)
    print("-" * 46)
    print(f"{'TỔNG':>8} {tp:>7} {fp:>6} {fn:>6} {se:>7.2f} {ppv:>7.2f}   F1={f1:.2f}%")
    print("ĐẠT mục tiêu >= 95%" if min(se, ppv) >= 95 else "CHƯA đạt mục tiêu >= 95%")


if __name__ == "__main__":
    main()
