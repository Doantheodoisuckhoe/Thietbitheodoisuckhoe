"""Bộ sinh tín hiệu tổng hợp để kiểm thử thuật toán khi chưa có phần cứng.

KHÔNG dùng để báo cáo độ chính xác trong đồ án — chỉ để kiểm tra code chạy đúng.
Đánh giá thật dùng MIT-BIH, BIDMC và dữ liệu đo trên người tình nguyện.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np


def beat_times(duration_s: float, hr_bpm, rng: np.random.Generator, rr_sd: float = 0.02,
               start_s: float = 0.3) -> np.ndarray:
    """Danh sách thời điểm đỉnh R. hr_bpm có thể là số hoặc hàm hr(t)."""
    times = []
    t = start_s
    while t < duration_s:
        times.append(t)
        hr = hr_bpm(t) if callable(hr_bpm) else hr_bpm
        rr = 60.0 / hr
        t += max(0.3, rr * (1 + rng.normal(0, rr_sd)))
    return np.asarray(times)


def ecg(duration_s: float, fs: float, hr_bpm=72.0, seed: int = 0, noise: float = 0.03,
        wander: float = 0.2, mains: float = 0.03, amplitude: float = 1000.0,
        invert: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """ECG dạng tổng các Gauss (P, Q, R, S, T). Trả về (tín hiệu, chỉ số mẫu đỉnh R)."""
    rng = np.random.default_rng(seed)
    n = int(duration_s * fs)
    t = np.arange(n) / fs
    rt = beat_times(duration_s, hr_bpm, rng)
    waves = [  # (offset s, biên độ, độ rộng s)
        (-0.20, 0.12, 0.025),
        (-0.030, -0.12, 0.010),
        (0.000, 1.00, 0.011),
        (0.032, -0.25, 0.012),
        (0.28, 0.30, 0.050),
    ]
    x = np.zeros(n)
    for r in rt:
        for off, a, w in waves:
            c = r + off
            lo, hi = int(max(0, (c - 5 * w) * fs)), int(min(n, (c + 5 * w) * fs + 1))
            tt = t[lo:hi]
            x[lo:hi] += a * np.exp(-0.5 * ((tt - c) / w) ** 2)
    x += wander * np.sin(2 * math.pi * 0.25 * t + rng.uniform(0, 6))
    x += mains * np.sin(2 * math.pi * 50 * t)
    x += rng.normal(0, noise, n)
    if invert:
        x = -x
    r_idx = np.round(rt * fs).astype(int)
    return x * amplitude, r_idx[r_idx < n]


def _pulse_shape(tp: np.ndarray, t_peak: float = 0.12, k: float = 3.0) -> np.ndarray:
    out = np.zeros_like(tp)
    m = tp > 0
    u = tp[m] / t_peak
    out[m] = u ** k * np.exp(k * (1 - u))
    return out


def ppg_from_beats(t: np.ndarray, onsets: np.ndarray, dc: float = 100000.0, pi: float = 0.01,
                   noise_rel: float = 0.0005, seed: int = 1, dicrotic: float = 0.35,
                   reflect: bool = True) -> np.ndarray:
    """PPG phản xạ: count = DC * (1 - PI * xung). onsets = thời điểm chân sóng (s)."""
    rng = np.random.default_rng(seed)
    pulse = np.zeros_like(t)
    for o in onsets:
        lo = np.searchsorted(t, o)
        hi = np.searchsorted(t, o + 1.2)
        tp = t[lo:hi] - o
        pulse[lo:hi] += _pulse_shape(tp) + dicrotic * _pulse_shape(tp - 0.25, 0.10)
    pulse /= max(1e-9, pulse.max())
    resp = 0.002 * np.sin(2 * math.pi * 0.25 * t)
    sig = dc * (1 - pi * pulse + resp) if reflect else dc * (1 + pi * pulse + resp)
    return sig + rng.normal(0, noise_rel * dc, len(t))


def ppg(duration_s: float, fs: float, hr_bpm=72.0, seed: int = 0, **kw) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(int(duration_s * fs)) / fs
    on = beat_times(duration_s, hr_bpm, rng) + 0.25
    return ppg_from_beats(t, on, seed=seed + 1, **kw)


def red_ir(duration_s: float, fs: float, ratio: float, hr_bpm: float = 70.0, seed: int = 0,
           dc_red: float = 80000.0, dc_ir: float = 120000.0, pi_ir: float = 0.01):
    """Cặp PPG đỏ/IR có tỉ số R mong muốn."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(duration_s * fs)) / fs
    on = beat_times(duration_s, hr_bpm, rng) + 0.25
    ir = ppg_from_beats(t, on, dc=dc_ir, pi=pi_ir, seed=seed + 1)
    red = ppg_from_beats(t, on, dc=dc_red, pi=pi_ir * ratio, seed=seed + 2)
    return red, ir


# ----------------------------------------------------------------------------
# Gia tốc kế (đơn vị g)
# ----------------------------------------------------------------------------

def _noise(n, sd, rng):
    return rng.normal(0, sd, (n, 3))


def acc_still(duration_s, fs, g_dir=(0, 0, 1), seed=0, sd=0.01):
    rng = np.random.default_rng(seed)
    n = int(duration_s * fs)
    g = np.asarray(g_dir, float)
    g /= np.linalg.norm(g)
    return np.tile(g, (n, 1)) + _noise(n, sd, rng)


def acc_walk(duration_s, fs, seed=0, step_hz=1.8, amp=0.3):
    rng = np.random.default_rng(seed)
    n = int(duration_s * fs)
    t = np.arange(n) / fs
    a = np.zeros((n, 3))
    a[:, 2] = 1.0 + amp * np.sin(2 * math.pi * step_hz * t)
    a[:, 0] = 0.5 * amp * np.sin(2 * math.pi * step_hz / 2 * t + 1.0)
    a[:, 1] = 0.2 * amp * np.sin(2 * math.pi * step_hz * t + 0.5)
    return a + _noise(n, 0.03, rng)


def acc_fall(fs, peak_g=4.0, freefall=True, lie_s=40.0, seed=0, move_blocks=0, pre_s=3.0):
    """Đứng yên -> (rơi tự do) -> va chạm -> nằm bất động (có thể cử động nhẹ vài giây)."""
    rng = np.random.default_rng(seed)
    parts = [acc_still(pre_s, fs, (0, 0, 1), seed)]
    if freefall:
        nff = int(0.35 * fs)
        ff = np.tile([0.0, 0.0, 0.25], (nff, 1)) + _noise(nff, 0.03, rng)
        parts.append(ff)
    nimp = max(2, int(0.06 * fs))
    imp = np.zeros((nimp, 3))
    shape = np.sin(np.linspace(0, math.pi, nimp))
    imp[:, 0] = peak_g * shape
    imp[:, 2] = 0.5 * shape
    parts.append(imp + _noise(nimp, 0.05, rng))
    nb = int(1.0 * fs)
    parts.append(acc_still(1.0, fs, (1, 0, 0.2), seed + 1, sd=0.25))  # dao động sau va chạm
    lie = acc_still(lie_s, fs, (1, 0, 0.2), seed + 2, sd=0.01)
    for k in range(move_blocks):  # vài giây cử động nhẹ khi nằm
        s = int((5 + 4 * k) * fs)
        lie[s:s + nb] += _noise(nb, 0.15, rng)
    parts.append(lie)
    return np.vstack(parts)


def acc_clap_then_walk(fs, peak_g=4.5, seed=0, walk_s=40.0):
    """Vỗ tay/đập tay xuống bàn rồi đi lại -> KHÔNG được báo té ngã."""
    rng = np.random.default_rng(seed)
    nimp = int(0.05 * fs)
    imp = np.zeros((nimp, 3))
    imp[:, 1] = peak_g * np.sin(np.linspace(0, math.pi, nimp))
    return np.vstack([acc_walk(5, fs, seed), imp + _noise(nimp, 0.05, rng), acc_walk(walk_s, fs, seed + 3)])


def acc_sit_down(fs, peak_g=1.8, seed=0, sit_s=40.0):
    """Ngồi xuống (va chạm nhẹ) rồi ngồi yên -> KHÔNG được báo té ngã."""
    rng = np.random.default_rng(seed)
    nimp = int(0.1 * fs)
    imp = np.zeros((nimp, 3))
    imp[:, 2] = 1 + (peak_g - 1) * np.sin(np.linspace(0, math.pi, nimp))
    return np.vstack([acc_walk(5, fs, seed), imp + _noise(nimp, 0.03, rng),
                      acc_still(sit_s, fs, (0.3, 0, 1), seed + 5, sd=0.01)])
