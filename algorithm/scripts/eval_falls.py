"""Đánh giá phát hiện té ngã trên dữ liệu té ngã giả lập.

Cách thu dữ liệu: bật chế độ RAW_STREAM trong firmware (config.h), đeo thiết bị,
chạy scripts/serial_logger.py để ghi file A.csv cho MỖI lần thử, rồi xếp vào:

    data/falls/fall/<tên>.csv    # té ngã giả lập lên nệm (ngã trước/sau/ngang...)
    data/falls/adl/<tên>.csv     # sinh hoạt thường: đi, ngồi xuống, nằm xuống, vỗ tay...

Mỗi lần té ngã phải nằm yên >= 35 s sau khi ngã.

Cũng đọc được dữ liệu nhóm đã thu bằng firmware/ghi_imu + algorithm/te_nga/ghi_du_lieu.py
(thư mục phẳng, tên file <nhãn>_<ngày>_<giờ>.csv, cột t_ms,ax,ay,az,... đơn vị g). Nhãn `nga` là
té ngã, `roi_board` bị bỏ qua (không phải người ngã), các nhãn khác là sinh hoạt thường.
Các bản ghi ngày 17/10 chỉ dài 10 s nên chưa kiểm được điều kiện "bất động 30 s"; tạm thời
chạy với --still-s 3 để kiểm tra phần phát hiện va chạm, và thu thêm bản ghi nằm yên >= 35 s.

    python scripts/eval_falls.py ../data/imu --still-s 3
    python scripts/eval_falls.py data/falls
    python scripts/eval_falls.py data/falls --sweep        # thử nhiều ngưỡng va chạm
    python scripts/eval_falls.py --synthetic               # chạy thử trên dữ liệu tổng hợp

Mục tiêu đề cương: phát hiện >= 90% té ngã giả lập.
"""
import argparse
import csv
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hwalgo import synthetic as syn  # noqa: E402
from hwalgo.fall import FallDetector  # noqa: E402


def load_acc_csv(path):
    """Đọc A.csv (serial_logger, đơn vị mg) hoặc file của ghi_imu (cột ax/ay/az, đơn vị g)."""
    t, a = [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = csv.DictReader(line for line in f if not line.startswith("#"))
        for row in rows:
            if "ax_mg" in row:
                a.append((float(row["ax_mg"]) / 1000, float(row["ay_mg"]) / 1000, float(row["az_mg"]) / 1000))
            else:
                a.append((float(row["ax"]), float(row["ay"]), float(row["az"])))
            t.append(float(row["t_ms"]))
    t = np.asarray(t)
    fs = 1000.0 * (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 else 104.0
    return np.asarray(a), fs


def detect(acc, fs, **params):
    fd = FallDetector(fs=fs, **params)
    for ax, ay, az in acc:
        ev = fd.update(ax, ay, az)
        if ev and ev["type"] == "fall":
            return True
    return False


def load_dataset(root):
    data = []
    if os.path.isdir(os.path.join(root, "fall")) or os.path.isdir(os.path.join(root, "adl")):
        for label in ("fall", "adl"):
            for p in sorted(glob.glob(os.path.join(root, label, "*.csv"))):
                acc, fs = load_acc_csv(p)
                data.append((label, os.path.basename(p), acc, fs))
        return data
    # thư mục phẳng kiểu data/imu: nhãn nằm ở đầu tên file
    for p in sorted(glob.glob(os.path.join(root, "*.csv"))):
        name = os.path.basename(p)
        tag = name.rsplit("_", 2)[0].lower()
        if tag == "roi_board":
            continue
        acc, fs = load_acc_csv(p)
        data.append(("fall" if tag == "nga" else "adl", name, acc, fs))
    return data


def synthetic_dataset():
    fs = 104.0
    data = []
    rng = np.random.default_rng(42)
    for i in range(20):
        acc = syn.acc_fall(fs, peak_g=float(rng.uniform(2.6, 6.0)), freefall=bool(i % 2),
                           move_blocks=int(rng.integers(0, 4)), seed=i)
        data.append(("fall", f"syn_fall_{i:02d}", acc, fs))
    for i in range(10):
        data.append(("adl", f"syn_walk_{i:02d}", syn.acc_walk(60, fs, seed=i), fs))
        data.append(("adl", f"syn_clap_{i:02d}", syn.acc_clap_then_walk(fs, peak_g=float(rng.uniform(3, 6)), seed=i), fs))
        data.append(("adl", f"syn_sit_{i:02d}", syn.acc_sit_down(fs, seed=i), fs))
    return data


def evaluate(data, verbose=True, **params):
    tp = fn = fp = tn = 0
    for label, name, acc, fs in data:
        hit = detect(acc, fs, **params)
        if label == "fall":
            tp += hit
            fn += not hit
        else:
            fp += hit
            tn += not hit
        if verbose and ((label == "fall") != hit):
            print(f"  SAI: {label:5s} {name}  -> {'báo té ngã' if hit else 'không báo'}")
    se = tp / max(1, tp + fn)
    sp = tn / max(1, tn + fp)
    return se, sp, (tp, fn, fp, tn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="data/falls")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--impact-g", type=float, default=2.8)
    ap.add_argument("--still-s", type=float, default=30.0)
    args = ap.parse_args()

    data = synthetic_dataset() if args.synthetic else load_dataset(args.root)
    if not data:
        print("Không có dữ liệu. Xem hướng dẫn ở đầu file.")
        return
    n_fall = sum(1 for d in data if d[0] == "fall")
    print(f"{n_fall} lần té ngã, {len(data) - n_fall} hoạt động thường")

    if args.sweep:
        print(f"{'impact_g':>9} {'Se %':>7} {'Sp %':>7}")
        for g in np.arange(2.0, 4.01, 0.2):
            se, sp, _ = evaluate(data, verbose=False, impact_g=float(g), still_s=args.still_s)
            print(f"{g:9.1f} {100 * se:7.1f} {100 * sp:7.1f}")
        return

    se, sp, (tp, fn, fp, tn) = evaluate(data, impact_g=args.impact_g, still_s=args.still_s)
    print(f"TP={tp} FN={fn} FP={fp} TN={tn}")
    print(f"Độ nhạy (phát hiện té ngã): {100 * se:.1f}%   -> {'ĐẠT' if se >= 0.9 else 'CHƯA ĐẠT'} mục tiêu 90%")
    print(f"Độ đặc hiệu (không báo nhầm): {100 * sp:.1f}%")


if __name__ == "__main__":
    main()
