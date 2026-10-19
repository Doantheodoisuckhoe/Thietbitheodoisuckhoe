"""So sánh thiết bị với máy đối chứng: sai số trung bình + biểu đồ Bland–Altman.

File CSV đầu vào (mỗi dòng 1 lần đo song song), ví dụ huyet_ap.csv:

    subject,device,reference
    SV01,128,131
    SV01,122,118
    ...

    python scripts/bland_altman.py huyet_ap.csv --unit mmHg --out ba_sbp.png
    python scripts/bland_altman.py spo2.csv --unit % --arms        # SpO2: in thêm Arms
    python scripts/bland_altman.py hr.csv --device-col hr_watch --ref-col hr_finger

Tiêu chí tham khảo trong đề cương:
    Nhịp tim : |sai số| <= 5 bpm lúc nghỉ
    SpO2     : Arms <= 4 %  (ISO 80601-2-61)
    Huyết áp : sai số TB <= 5 mmHg, SD <= 8 mmHg (ISO 81060-2)
"""
import argparse
import csv

import numpy as np


def bland_altman_stats(device, reference):
    d = np.asarray(device, float)
    r = np.asarray(reference, float)
    diff = d - r
    bias = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0
    return {
        "n": int(len(diff)),
        "bias": bias,
        "sd": sd,
        "loa_low": bias - 1.96 * sd,
        "loa_high": bias + 1.96 * sd,
        "mae": float(np.mean(np.abs(diff))),
        "rmse": float(np.sqrt(np.mean(diff ** 2))),
        "pearson_r": float(np.corrcoef(d, r)[0, 1]) if len(d) > 2 else float("nan"),
    }


def plot_bland_altman(device, reference, out_png, title="Bland-Altman", unit=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = np.asarray(device, float)
    r = np.asarray(reference, float)
    s = bland_altman_stats(d, r)
    mean = (d + r) / 2
    diff = d - r
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(mean, diff, s=14, alpha=0.6)
    ax.axhline(s["bias"], color="k", label=f"bias = {s['bias']:.2f} {unit}")
    ax.axhline(s["loa_high"], color="r", ls="--", label=f"+1.96 SD = {s['loa_high']:.2f}")
    ax.axhline(s["loa_low"], color="r", ls="--", label=f"-1.96 SD = {s['loa_low']:.2f}")
    ax.set_xlabel(f"Trung bình (thiết bị, tham chiếu) [{unit}]")
    ax.set_ylabel(f"Thiết bị - tham chiếu [{unit}]")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_file")
    ap.add_argument("--device-col", default="device")
    ap.add_argument("--ref-col", default="reference")
    ap.add_argument("--unit", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("--title", default="Bland-Altman")
    ap.add_argument("--arms", action="store_true", help="in Arms (dùng cho SpO2)")
    args = ap.parse_args()

    dev, ref = [], []
    with open(args.csv_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                dev.append(float(row[args.device_col]))
                ref.append(float(row[args.ref_col]))
            except (KeyError, ValueError):
                continue
    s = bland_altman_stats(dev, ref)
    for k, v in s.items():
        print(f"{k:>10}: {v:.3f}" if isinstance(v, float) else f"{k:>10}: {v}")
    if args.arms:
        print(f"{'Arms':>10}: {s['rmse']:.3f}  (đạt nếu <= 4)")
    if args.out:
        plot_bland_altman(dev, ref, args.out, args.title, args.unit)
        print("Đã lưu", args.out)


if __name__ == "__main__":
    main()
