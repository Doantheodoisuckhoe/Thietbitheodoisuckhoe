"""So sánh thuật toán C (firmware) với bản Python tham chiếu trên cùng dữ liệu.

    cd firmware/tests
    python run_host_tests.py        # cần g++ (Linux/macOS, hoặc MSYS2/MinGW trên Windows)

Kiểm tra: HR, SpO2, đỉnh R, PAT, té ngã cho ra cùng kết quả (sai khác float32 nhỏ).
"""
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.join(HERE, "..", "health_watch")
sys.path.insert(0, os.path.join(HERE, "..", "..", "algorithm"))

from hwalgo import synthetic as syn  # noqa: E402
from hwalgo.ecg_rpeak import detect_r_peaks  # noqa: E402
from hwalgo.fall import FallDetector  # noqa: E402
from hwalgo.hr_ppg import estimate_hr_series  # noqa: E402
from hwalgo.pat import compute_pat  # noqa: E402
from hwalgo.spo2 import compute_spo2  # noqa: E402

SRCS = ["dsp", "hr_ppg", "spo2", "ecg_rpeak", "pat", "fall_detect"]


def build(tmp):
    exe = os.path.join(tmp, "host_test")
    cmd = ["g++", "-O2", "-std=c++17", "-Wall", "-Wextra", "-Wno-unused-parameter", f"-I{FW}",
           os.path.join(HERE, "host_test.cpp")] + [os.path.join(FW, s + ".cpp") for s in SRCS] + ["-o", exe]
    subprocess.run(cmd, check=True)
    return exe


def run(exe, *args):
    out = subprocess.run([exe, *map(str, args)], check=True, capture_output=True, text=True).stdout
    return [line.split(",") for line in out.strip().splitlines() if line]


def save(path, arr):
    np.savetxt(path, np.atleast_2d(np.asarray(arr, dtype=np.float32)).reshape(len(arr), -1),
               delimiter=",", fmt="%.6f")


def main():
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        exe = build(tmp)
        f = lambda n: os.path.join(tmp, n)  # noqa: E731

        # ---- HR
        for hr, seed in [(55, 1), (75, 2), (130, 3)]:
            x = syn.ppg(60, 50.0, hr_bpm=hr, seed=seed).astype(np.float32)
            save(f("hr.csv"), x)
            c = run(exe, "hr", 50, 1, f("hr.csv"))
            _, py, pq = estimate_hr_series(x.astype(float), 50.0)
            c_hr = np.array([float(r[0]) for r in c])
            ok = len(c_hr) == len(py) and np.max(np.abs(c_hr - np.array(py))) < 0.5
            print(f"HR {hr:3d} bpm: C={np.median(c_hr[20:]):.2f} Py={np.median(py[20:]):.2f}  {'OK' if ok else 'LỆCH'}")
            failures += not ok

        # ---- SpO2
        for ratio in [0.5, 0.8]:
            red, ir = syn.red_ir(30, 100.0, ratio, seed=5)
            save(f("s.csv"), np.c_[red, ir])
            c = run(exe, "spo2", 100, f("s.csv"))[0]
            py = compute_spo2(red.astype(np.float32).astype(float), ir.astype(np.float32).astype(float), 100.0)
            ok = int(c[0]) == py.status and abs(float(c[1]) - py.spo2) < 0.1 and int(c[4]) == py.n_valid
            print(f"SpO2 R={ratio}: C={float(c[1]):.2f}% Py={py.spo2:.2f}%  {'OK' if ok else 'LỆCH'}")
            failures += not ok

        # ---- ECG
        for hr, inv, noise, seed in [(70, False, 0.03, 1), (110, True, 0.08, 2), (50, False, 0.1, 3)]:
            x, _ = syn.ecg(30, 256.0, hr_bpm=hr, seed=seed, invert=inv, noise=noise)
            x = x.astype(np.float32)
            save(f("e.csv"), x)
            c = np.array([int(r[0]) for r in run(exe, "ecg", 256, f("e.csv"))])
            py = detect_r_peaks(x.astype(float), 256.0)
            ok = len(c) == len(py) and np.max(np.abs(c - py)) <= 1
            print(f"ECG {hr} bpm: C={len(c)} đỉnh, Py={len(py)} đỉnh  {'OK' if ok else 'LỆCH'}")
            failures += not ok

        # ---- PAT
        rng = np.random.default_rng(4)
        rt = syn.beat_times(30, 72, rng)
        t0, dt = 3.7, 5.0
        t_p = t0 + np.arange(6000) * dt
        p = syn.ppg_from_beats(t_p / 1000.0, rt + 0.24).astype(np.float32)
        r_ms = (rt * 1000.0).astype(np.float32)
        save(f("r.csv"), r_ms)
        save(f("p.csv"), p)
        c = run(exe, "pat", f("r.csv"), f("p.csv"), t0, dt)[0]
        py = compute_pat(r_ms.astype(float), p.astype(float), t_p)
        ok = int(c[0]) == py.status and abs(float(c[1]) - py.pat_ms) < 0.2
        print(f"PAT: C={float(c[1]):.2f} ms Py={py.pat_ms:.2f} ms  {'OK' if ok else 'LỆCH'}")
        failures += not ok

        # ---- té ngã
        for name, acc in [("fall", syn.acc_fall(104.0, peak_g=4.0, move_blocks=2, seed=1)),
                          ("fall_noff", syn.acc_fall(104.0, peak_g=3.1, freefall=False, seed=2)),
                          ("clap", syn.acc_clap_then_walk(104.0))]:
            acc = acc.astype(np.float32)
            save(f("a.csv"), acc)
            c = [(int(r[0]), int(r[1])) for r in run(exe, "fall", 104, f("a.csv"))]
            fd = FallDetector(fs=104.0)
            py = []
            for i, (ax, ay, az) in enumerate(acc.astype(float)):
                ev = fd.update(ax, ay, az)
                if ev:
                    py.append((i, 1 if ev["type"] == "impact" else 2))
            ok = c == py
            print(f"Té ngã [{name}]: C={c} Py={py}  {'OK' if ok else 'LỆCH'}")
            failures += not ok

    print("\nTẤT CẢ KHỚP" if failures == 0 else f"\n{failures} TRƯỜNG HỢP LỆCH")
    return failures


if __name__ == "__main__":
    sys.exit(main())
