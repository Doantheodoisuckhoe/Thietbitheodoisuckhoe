"""Đánh giá nhịp tim từ PPG trên BIDMC PPG and Respiration Dataset (PhysioNet).

BIDMC: 53 bản ghi 8 phút, PPG ngón tay 125 Hz + giá trị tham chiếu HR/PULSE 1 Hz
từ monitor. Tín hiệu được lấy mẫu lại về 50 Hz (đúng tần số của thiết bị) rồi chạy
bộ ước lượng streaming y hệt firmware.

    python scripts/eval_bidmc.py                    # tải từ PhysioNet
    python scripts/eval_bidmc.py --local-dir data/bidmc --plot ket_qua_hr.png

Mục tiêu đề cương: sai số <= 5 lần/phút lúc nghỉ.
Lưu ý: PPG BIDMC là PPG ngón tay của monitor (đã đảo dấu, sóng lên khi tâm thu)
-> invert=False. PPG cổ tay thật của thiết bị khó hơn: phải kiểm chứng thêm trên người.
"""
import argparse
import os
import sys

import numpy as np
from scipy.signal import resample_poly

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hwalgo.hr_ppg import estimate_hr_series  # noqa: E402
from bland_altman import bland_altman_stats, plot_bland_altman  # noqa: E402

FS_DEVICE = 50


def _find(names, key):
    for i, n in enumerate(names):
        if n.strip().rstrip(",").upper() == key.upper():
            return i
    raise KeyError(f"không thấy kênh {key} trong {names}")


def load(rec, local_dir):
    import wfdb
    if local_dir:
        p = os.path.join(local_dir, rec)
        return wfdb.rdrecord(p), wfdb.rdrecord(p + "n")
    return wfdb.rdrecord(rec, pn_dir="bidmc"), wfdb.rdrecord(rec + "n", pn_dir="bidmc")


def evaluate_record(rec, local_dir=None, ref_key="PULSE", skip_s=20, min_quality=50):
    sig, num = load(rec, local_dir)
    ppg = sig.p_signal[:, _find(sig.sig_name, "PLETH")]
    ppg = np.nan_to_num(ppg)
    x = resample_poly(ppg, 2, 5) * 1000.0  # 125 -> 50 Hz
    ref = num.p_signal[:, _find(num.sig_name, ref_key)]
    t, hr, q = estimate_hr_series(x, FS_DEVICE, step_s=1.0, invert=False)
    est, refv = [], []
    for ti, h, qq in zip(t, hr, q):
        k = int(round(ti))
        if ti < skip_s or k >= len(ref) or h <= 0 or qq < min_quality or not np.isfinite(ref[k]) or ref[k] <= 0:
            continue
        est.append(h)
        refv.append(ref[k])
    coverage = len(est) / max(1, len([ti for ti in t if ti >= skip_s]))
    return np.array(est), np.array(refv), coverage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", nargs="*", default=[f"bidmc{i:02d}" for i in range(1, 54)])
    ap.add_argument("--local-dir", default=None)
    ap.add_argument("--ref", default="PULSE", help="PULSE (oximeter) hoặc HR (ECG)")
    ap.add_argument("--plot", default=None, help="lưu biểu đồ Bland-Altman ra file PNG")
    args = ap.parse_args()

    all_est, all_ref = [], []
    print(f"{'Bản ghi':>9} {'MAE':>6} {'bias':>6} {'phủ %':>6}")
    for rec in args.records:
        try:
            est, ref, cov = evaluate_record(rec, args.local_dir, args.ref)
        except Exception as e:  # noqa: BLE001
            print(f"{rec:>9}  lỗi: {e}")
            continue
        if len(est) == 0:
            print(f"{rec:>9}  không có ước lượng đạt chất lượng")
            continue
        all_est.append(est)
        all_ref.append(ref)
        print(f"{rec:>9} {np.mean(np.abs(est - ref)):6.2f} {np.mean(est - ref):6.2f} {100 * cov:6.1f}")
    est = np.concatenate(all_est)
    ref = np.concatenate(all_ref)
    s = bland_altman_stats(est, ref)
    print("-" * 34)
    for k, v in s.items():
        print(f"{k:>12}: {v:.3f}" if isinstance(v, float) else f"{k:>12}: {v}")
    print(f"Tỉ lệ |sai số| <= 5 bpm: {100 * np.mean(np.abs(est - ref) <= 5):.1f}%")
    if args.plot:
        plot_bland_altman(est, ref, args.plot, title="HR PPG vs tham chiếu BIDMC", unit="bpm")
        print("Đã lưu", args.plot)


if __name__ == "__main__":
    main()
