"""Bộ lọc dùng chung cho mọi thuật toán.

Toàn bộ bộ lọc là biquad bậc 2 (công thức RBJ "Audio EQ Cookbook"), ghép nối
tiếp HP + LP để tạo band-pass. Firmware C (firmware/health_watch/dsp.cpp) dùng
ĐÚNG các công thức và cách khởi tạo trạng thái này, nên kết quả Python và C
gần như trùng nhau (chỉ khác sai số float32).
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import numpy as np
from scipy.signal import lfilter

Section = Tuple[Tuple[float, float, float], Tuple[float, float, float]]  # (b, a)

BUTTERWORTH_Q = 1.0 / math.sqrt(2.0)


def design_biquad(kind: str, f0: float, fs: float, q: float = BUTTERWORTH_Q) -> Section:
    """Thiết kế 1 biquad low-pass hoặc high-pass. Trả về (b, a) với a0 = 1."""
    if not 0 < f0 < fs / 2:
        raise ValueError(f"f0={f0} phải nằm trong (0, fs/2={fs / 2})")
    w0 = 2.0 * math.pi * f0 / fs
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    if kind == "lowpass":
        b = ((1 - cw) / 2, 1 - cw, (1 - cw) / 2)
    elif kind == "highpass":
        b = ((1 + cw) / 2, -(1 + cw), (1 + cw) / 2)
    else:
        raise ValueError("kind phải là 'lowpass' hoặc 'highpass'")
    a0 = 1 + alpha
    a = (1.0, -2 * cw / a0, (1 - alpha) / a0)
    b = tuple(v / a0 for v in b)
    return (b, a)  # type: ignore[return-value]


def bandpass_sections(f_lo: float, f_hi: float, fs: float) -> List[Section]:
    """Band-pass = HP(f_lo) nối tiếp LP(f_hi)."""
    return [design_biquad("highpass", f_lo, fs), design_biquad("lowpass", f_hi, fs)]


def dc_gain(section: Section) -> float:
    b, a = section
    return (b[0] + b[1] + b[2]) / (a[0] + a[1] + a[2])


def steady_state(section: Section, u: float) -> Tuple[float, float, float]:
    """Trạng thái (z1, z2) và đầu ra khi đầu vào là hằng số u từ -vô cùng.

    Dùng để khởi tạo bộ lọc tại mẫu đầu tiên, tránh quá độ lớn do thành phần
    DC (PPG thô có DC ~ 1e5 count).
    """
    b, a = section
    y = dc_gain(section) * u
    z2 = b[2] * u - a[2] * y
    z1 = b[1] * u - a[1] * y + z2
    return z1, z2, y


class Biquad:
    """Biquad dạng Direct Form II Transposed, xử lý từng mẫu (giống C)."""

    def __init__(self, section: Section):
        (self.b0, self.b1, self.b2), (_, self.a1, self.a2) = section
        self.section = section
        self.z1 = 0.0
        self.z2 = 0.0

    def reset_to(self, u: float) -> float:
        self.z1, self.z2, y = steady_state(self.section, u)
        return y

    def process(self, x: float) -> float:
        y = self.b0 * x + self.z1
        self.z1 = self.b1 * x - self.a1 * y + self.z2
        self.z2 = self.b2 * x - self.a2 * y
        return y


class BiquadChain:
    def __init__(self, sections: Sequence[Section]):
        self.stages = [Biquad(s) for s in sections]

    def reset_to(self, u: float) -> None:
        for st in self.stages:
            u = st.reset_to(u)

    def process(self, x: float) -> float:
        for st in self.stages:
            x = st.process(x)
        return x


def _sosfilt_ss(sections: Sequence[Section], x: np.ndarray) -> np.ndarray:
    """Lọc xuôi chiều, trạng thái đầu khởi tạo theo x[0] (steady state)."""
    y = np.asarray(x, dtype=float)
    for sec in sections:
        b, a = sec
        if len(y) == 0:
            return y
        z1, z2, _ = steady_state(sec, float(y[0]))
        y, _ = lfilter(b, a, y, zi=[z1, z2])
    return y


def filtfilt_ss(sections: Sequence[Section], x: np.ndarray) -> np.ndarray:
    """Lọc pha-không (xuôi rồi ngược) — dùng cho xử lý offline trên bộ đệm.

    Cùng cách làm với dsp_filtfilt() trong firmware.
    """
    y = _sosfilt_ss(sections, x)
    y = _sosfilt_ss(sections, y[::-1])
    return y[::-1].copy()


def centered_diff(x: np.ndarray) -> np.ndarray:
    """Đạo hàm 5 điểm có tâm (Pan-Tompkins dạng không trễ), chia 8."""
    x = np.asarray(x, dtype=float)
    d = np.zeros_like(x)
    if len(x) >= 5:
        d[2:-2] = (-x[:-4] - 2 * x[1:-3] + 2 * x[3:-1] + x[4:]) / 8.0
    return d


def centered_moving_average(x: np.ndarray, width: int) -> np.ndarray:
    """Trung bình trượt có tâm, độ rộng `width` mẫu (biên: lấy phần có sẵn)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    half = width // 2
    c = np.concatenate([[0.0], np.cumsum(x)])
    idx = np.arange(n)
    lo = np.clip(idx - half, 0, n)
    hi = np.clip(idx + half + 1, 0, n)
    return (c[hi] - c[lo]) / (hi - lo)
