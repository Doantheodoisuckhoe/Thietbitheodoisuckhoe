"""SpO2 theo phương pháp tỉ số R (Ratio-of-Ratios) từ PPG đỏ + hồng ngoại.

Đo định kỳ khi người dùng đứng yên (firmware kiểm tra IMU), mỗi lần ~30 s ở 100 Hz.

    R = (AC_đỏ / DC_đỏ) / (AC_IR / DC_IR)
    SpO2 = a*R^2 + b*R + c   (mặc định hệ số của Maxim: -45.060, 30.354, 94.845)

AC = RMS tín hiệu sau band-pass 0,5–5 Hz; DC = trung bình tín hiệu thô.
Tính trên các cửa sổ 4 s (bước 2 s), chỉ giữ cửa sổ đạt chất lượng
(tương quan đỏ–IR >= 0,8, chỉ số tưới máu đủ lớn, R hợp lý), lấy trung vị.

LƯU Ý: Hệ số a, b, c phải được hiệu chuẩn cho đúng phần cứng (LED, khoảng cách,
vị trí cổ tay) mới đạt Arms <= 4% theo ISO 80601-2-61. Trong đồ án, hãy đo song
song với máy kẹp ngón, lưu R và SpO2 tham chiếu, rồi fit lại bằng
scripts/fit_spo2_coeffs.py.

Bản C tương ứng: firmware/health_watch/spo2.cpp
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from .filters import bandpass_sections, filtfilt_ss

STATUS_OK = 0
STATUS_NO_CONTACT = 1
STATUS_LOW_QUALITY = 2

DEFAULT_COEFFS = (-45.060, 30.354, 94.845)


@dataclass
class Spo2Result:
    status: int
    spo2: Optional[float]
    ratio: Optional[float]
    quality: int
    n_valid: int
    n_windows: int


def spo2_from_ratio(r: float, coeffs: Sequence[float] = DEFAULT_COEFFS) -> float:
    a, b, c = coeffs
    return float(min(100.0, max(70.0, a * r * r + b * r + c)))


def compute_spo2(
    red: Sequence[float],
    ir: Sequence[float],
    fs: float,
    coeffs: Sequence[float] = DEFAULT_COEFFS,
    win_s: float = 4.0,
    hop_s: float = 2.0,
    skip_s: float = 2.0,
    dc_min: float = 10000.0,
    min_corr: float = 0.8,
    min_pi: float = 0.0005,
    r_range=(0.2, 2.0),
    min_windows: int = 3,
) -> Spo2Result:
    red = np.asarray(red, dtype=float)
    ir = np.asarray(ir, dtype=float)
    n = min(len(red), len(ir))
    red, ir = red[:n], ir[:n]
    win = int(round(win_s * fs))
    hop = int(round(hop_s * fs))
    skip = int(round(skip_s * fs))
    if n < skip + win:
        return Spo2Result(STATUS_LOW_QUALITY, None, None, 0, 0, 0)

    if red[skip:].mean() < dc_min or ir[skip:].mean() < dc_min:
        return Spo2Result(STATUS_NO_CONTACT, None, None, 0, 0, 0)

    sections = bandpass_sections(0.5, 5.0, fs)
    red_bp = filtfilt_ss(sections, red)
    ir_bp = filtfilt_ss(sections, ir)

    ratios, corrs = [], []
    n_windows = 0
    start = skip
    while start + win <= n:
        e = start + win
        n_windows += 1
        dc_r = red[start:e].mean()
        dc_i = ir[start:e].mean()
        r_seg = red_bp[start:e] - red_bp[start:e].mean()
        i_seg = ir_bp[start:e] - ir_bp[start:e].mean()
        ac_r = float(np.sqrt(np.mean(r_seg * r_seg)))
        ac_i = float(np.sqrt(np.mean(i_seg * i_seg)))
        start += hop
        if dc_r < dc_min or dc_i < dc_min or ac_i <= 0 or ac_r <= 0:
            continue
        corr = float(np.sum(r_seg * i_seg) / (np.sqrt(np.sum(r_seg ** 2) * np.sum(i_seg ** 2)) + 1e-12))
        pi_ir = ac_i / dc_i
        ratio = (ac_r / dc_r) / pi_ir
        if corr >= min_corr and pi_ir >= min_pi and r_range[0] <= ratio <= r_range[1]:
            ratios.append(ratio)
            corrs.append(corr)

    if len(ratios) < min_windows:
        q = int(100 * len(ratios) / max(1, n_windows))
        return Spo2Result(STATUS_LOW_QUALITY, None, None, q, len(ratios), n_windows)

    r_med = float(np.median(ratios))
    quality = int(round(100.0 * len(ratios) / n_windows * float(np.mean(corrs))))
    return Spo2Result(STATUS_OK, spo2_from_ratio(r_med, coeffs), r_med, quality, len(ratios), n_windows)


def fit_coeffs(ratios: Sequence[float], spo2_ref: Sequence[float], order: int = 2):
    """Fit lại hệ số đường cong SpO2(R) từ dữ liệu đo song song với máy tham chiếu."""
    r = np.asarray(ratios, float)
    s = np.asarray(spo2_ref, float)
    if order == 1:
        b, c = np.polyfit(r, s, 1)
        return (0.0, float(b), float(c))
    a, b, c = np.polyfit(r, s, 2)
    return (float(a), float(b), float(c))


def arms(estimate: Sequence[float], reference: Sequence[float]) -> float:
    """Accuracy root-mean-square (ISO 80601-2-61)."""
    d = np.asarray(estimate, float) - np.asarray(reference, float)
    return float(np.sqrt(np.mean(d * d)))
