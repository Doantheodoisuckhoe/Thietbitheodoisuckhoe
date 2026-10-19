"""Chạy lại thuật toán Python trên dữ liệu thô đã ghi bằng serial_logger.py.

Dùng để so sánh kết quả Python với kết quả firmware tính trên cùng dữ liệu,
và để thử tham số mới mà không phải nạp lại firmware.

    python scripts/replay_log.py data/session_01            # tự nhận các file có sẵn
    python scripts/replay_log.py data/ecg_01 --plot ecg.png
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hwalgo.ecg_rpeak import detect_r_peaks, heart_rate_from_peaks  # noqa: E402
from hwalgo.hr_ppg import estimate_hr_series  # noqa: E402
from hwalgo.pat import compute_pat  # noqa: E402
from hwalgo.spo2 import compute_spo2  # noqa: E402


def read(path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    return np.asarray(rows[1:], dtype=float)


def fs_of(t_ms):
    return 1000.0 * (len(t_ms) - 1) / (t_ms[-1] - t_ms[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--plot", default=None)
    args = ap.parse_args()
    f = lambda k: os.path.join(args.folder, f"{k}.csv")  # noqa: E731

    if os.path.exists(f("G")):
        g = read(f("G"))
        fs = fs_of(g[:, 0])
        t, hr, q = estimate_hr_series(g[:, 1], fs, step_s=1.0)
        valid = [h for h, qq in zip(hr, q) if h > 0 and qq >= 50]
        print(f"[HR] fs={fs:.1f} Hz, {len(valid)}/{len(hr)} giây có HR tin cậy, "
              f"trung vị {np.median(valid) if valid else 0:.1f} bpm")

    if os.path.exists(f("S")):
        s = read(f("S"))
        fs = fs_of(s[:, 0])
        r = compute_spo2(s[:, 1], s[:, 2], fs)
        print(f"[SpO2] fs={fs:.1f} Hz, status={r.status}, SpO2={r.spo2}, R={r.ratio}, "
              f"quality={r.quality}, cửa sổ hợp lệ {r.n_valid}/{r.n_windows}")

    if os.path.exists(f("E")):
        e = read(f("E"))
        fs = fs_of(e[:, 0])
        peaks = detect_r_peaks(e[:, 1], fs)
        print(f"[ECG] fs={fs:.1f} Hz, {len(peaks)} đỉnh R, HR={heart_rate_from_peaks(peaks, fs):.1f} bpm")
        if os.path.exists(f("P")):
            p = read(f("P"))
            res = compute_pat(e[peaks, 0], p[:, 1], p[:, 0])
            print(f"[PAT] status={res.status}, PAT={res.pat_ms} ms, IQR={res.iqr_ms}, "
                  f"{res.n_valid}/{res.n_beats} nhịp")
        if args.plot:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 3.5))
            tt = (e[:, 0] - e[0, 0]) / 1000
            ax.plot(tt, e[:, 1], lw=0.7)
            ax.plot(tt[peaks], e[peaks, 1], "rv")
            ax.set_xlabel("s")
            fig.tight_layout()
            fig.savefig(args.plot, dpi=130)
            print("Đã lưu", args.plot)


if __name__ == "__main__":
    main()
