"""Thời gian đến của sóng mạch (PAT – Pulse Arrival Time) từ ECG + PPG.

PAT = thời điểm chân sóng PPG (cổ tay) - thời điểm đỉnh R (ECG) của cùng nhịp.
Chân sóng xác định bằng phương pháp "tiếp tuyến cắt nhau" (intersecting tangent):
giao điểm của tiếp tuyến tại điểm dốc nhất của sườn lên với đường nằm ngang
qua cực tiểu trước đó.

ECG (250 Hz, ADC + TIMER4) và PPG (200 Hz, FIFO MAX30101) lấy mẫu độc lập -> mỗi mẫu mang
nhãn thời gian riêng (ms, theo đồng hồ vi điều khiển). Độ lệch cố định (trễ bộ
lọc analog của AD8232, trễ đọc FIFO...) bị triệt tiêu khi hiệu chuẩn cá nhân.

Bản C tương ứng: firmware/health_watch/pat.cpp
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from .filters import bandpass_sections, filtfilt_ss

STATUS_OK = 0
STATUS_LOW_QUALITY = 3


@dataclass
class PatResult:
    status: int
    pat_ms: Optional[float]
    iqr_ms: Optional[float]
    n_valid: int
    n_beats: int
    pats: List[float]


def time_derivative(y: np.ndarray, t_ms: np.ndarray) -> np.ndarray:
    d = np.zeros_like(y)
    if len(y) >= 3:
        dt = t_ms[2:] - t_ms[:-2]
        dt[dt == 0] = 1e-6
        d[1:-1] = (y[2:] - y[:-2]) / dt
    return d


def compute_pat(
    r_times_ms,
    ppg,
    t_ppg_ms,
    invert: bool = True,
    win_lo_ms: float = 100.0,
    win_hi_ms: float = 500.0,
    pat_range_ms=(80.0, 600.0),
    min_beats: int = 8,
) -> PatResult:
    r_times = np.asarray(r_times_ms, dtype=float)
    p = np.asarray(ppg, dtype=float)
    t = np.asarray(t_ppg_ms, dtype=float)
    n = min(len(p), len(t))
    p, t = p[:n], t[:n]
    if n < 10 or len(r_times) == 0:
        return PatResult(STATUS_LOW_QUALITY, None, None, 0, len(r_times), [])
    if invert:
        p = -p
    fs = 1000.0 * (n - 1) / (t[-1] - t[0])
    pf = filtfilt_ss(bandpass_sections(0.5, 8.0, fs), p)
    dp = time_derivative(pf, t)

    pats: List[float] = []
    for tr in r_times:
        i0 = int(np.searchsorted(t, tr + win_lo_ms))
        i1 = int(np.searchsorted(t, tr + win_hi_ms))
        if i0 < 1 or i1 >= n or i1 - i0 < 3:
            continue
        k = i0 + int(np.argmax(dp[i0:i1]))
        if dp[k] <= 0:
            continue
        j0 = int(np.searchsorted(t, tr))
        pmin = float(np.min(pf[j0:k + 1]))
        t_foot = t[k] - (pf[k] - pmin) / dp[k]
        pat = t_foot - tr
        if pat_range_ms[0] <= pat <= pat_range_ms[1]:
            pats.append(float(pat))

    if len(pats) < min_beats:
        return PatResult(STATUS_LOW_QUALITY, None, None, len(pats), len(r_times), pats)

    arr = np.asarray(pats)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med))) * 1.4826
    keep = arr[np.abs(arr - med) <= max(3.0 * mad, 5.0)]
    if len(keep) < min_beats:
        return PatResult(STATUS_LOW_QUALITY, None, None, len(keep), len(r_times), pats)
    q75, q25 = np.percentile(keep, [75, 25])
    return PatResult(STATUS_OK, float(np.median(keep)), float(q75 - q25), len(keep), len(r_times), pats)
