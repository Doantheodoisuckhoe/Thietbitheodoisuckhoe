"""Ước lượng nhịp tim liên tục từ PPG ánh sáng xanh (MAX30101).

Thuật toán xử lý TỪNG MẪU (streaming) để chạy được trên vi điều khiển:

1. Đảo dấu tín hiệu thô (PPG phản xạ: máu nhiều -> ánh sáng về ít -> count giảm),
   để đỉnh tâm thu hướng lên.
2. Lọc band-pass 0,5–4 Hz (biquad HP + LP).
3. Tìm cực đại cục bộ dương; chấp nhận là nhịp nếu
   - cách nhịp trước >= thời gian trơ (0,6 x IBI trung vị, để loại sóng dội),
   - biên độ >= 40% biên độ đỉnh tham chiếu (giảm dần với hằng số 2,5 s).
4. IBI (khoảng giữa hai nhịp) hợp lệ 0,3–2,0 s; loại IBI lệch > 30% so với trung vị;
   nếu 3 IBI liên tiếp bị loại thì coi như nhịp tim đã đổi thật -> làm mới bộ đệm.
5. HR = 60 / trung vị 8 IBI gần nhất; chất lượng 0–100 từ độ phân tán IBI.

Bản C tương ứng: firmware/health_watch/hr_ppg.cpp
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .filters import BiquadChain, bandpass_sections


def median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else 0.5 * (s[m - 1] + s[m])


class HeartRateEstimator:
    def __init__(
        self,
        fs: float,
        invert: bool = True,
        f_lo: float = 0.5,
        f_hi: float = 4.0,
        amp_tau_s: float = 2.5,
        thr_ratio: float = 0.4,
        refr_init_s: float = 0.30,
        refr_min_s: float = 0.25,
        refr_max_s: float = 1.2,
        refr_ratio: float = 0.6,
        ibi_min_s: float = 0.3,
        ibi_max_s: float = 2.0,
        n_ibi: int = 8,
        outlier_ratio: float = 0.3,
        max_outliers: int = 3,
        beat_timeout_s: float = 3.0,
        min_ibis: int = 4,
        dc_tau_s: float = 2.0,
        contact_dc_min: float = 0.0,
    ):
        self.fs = fs
        self.invert = invert
        self.bp = BiquadChain(bandpass_sections(f_lo, f_hi, fs))
        self.amp_decay = math.exp(-1.0 / (amp_tau_s * fs))
        self.thr_ratio = thr_ratio
        self.refr_init = refr_init_s * fs
        self.refr_min = refr_min_s * fs
        self.refr_max = refr_max_s * fs
        self.refr_ratio = refr_ratio
        self.ibi_min = ibi_min_s
        self.ibi_max = ibi_max_s
        self.n_ibi = n_ibi
        self.outlier_ratio = outlier_ratio
        self.max_outliers = max_outliers
        self.beat_timeout = beat_timeout_s * fs
        self.min_ibis = min_ibis
        self.dc_alpha = 1.0 / (dc_tau_s * fs)
        self.contact_dc_min = contact_dc_min
        self.reset()

    def reset(self) -> None:
        self.started = False
        self.n = 0
        self.y1 = 0.0
        self.y2 = 0.0
        self.amp = 0.0
        self.last_peak: Optional[int] = None
        self.ibis: List[float] = []
        self.consec_outliers = 0
        self.dc = 0.0

    # ------------------------------------------------------------------
    def update(self, x: float) -> bool:
        """Đưa vào 1 mẫu thô. Trả về True nếu vừa phát hiện 1 nhịp."""
        s = -x if self.invert else x
        if not self.started:
            self.bp.reset_to(s)
            self.dc = x
            self.started = True
        self.dc += (x - self.dc) * self.dc_alpha
        y = self.bp.process(s)
        self.amp *= self.amp_decay

        beat = False
        if self.y1 > self.y2 and self.y1 >= y and self.y1 > 0.0:
            p = self.n - 1
            if len(self.ibis) >= 2:
                refr = self.refr_ratio * median(self.ibis) * self.fs
                refr = min(max(refr, self.refr_min), self.refr_max)
            else:
                refr = self.refr_init
            if self.last_peak is None or (p - self.last_peak) >= refr:
                if self.y1 >= self.thr_ratio * self.amp:
                    beat = True
                    if self.y1 > self.amp:
                        self.amp = self.y1
                    if self.last_peak is not None:
                        self._add_ibi((p - self.last_peak) / self.fs)
                    self.last_peak = p
        self.y2 = self.y1
        self.y1 = y
        self.n += 1
        return beat

    def _add_ibi(self, ibi: float) -> None:
        if not (self.ibi_min <= ibi <= self.ibi_max):
            return  # bỏ qua (thường do mất nhịp hoặc nhiễu)
        if len(self.ibis) >= 3:
            med = median(self.ibis)
            if abs(ibi - med) > self.outlier_ratio * med:
                self.consec_outliers += 1
                if self.consec_outliers >= self.max_outliers:
                    self.ibis = [ibi]
                    self.consec_outliers = 0
                return
        self.ibis.append(ibi)
        if len(self.ibis) > self.n_ibi:
            self.ibis.pop(0)
        self.consec_outliers = 0

    # ------------------------------------------------------------------
    def in_contact(self) -> bool:
        return self.contact_dc_min <= 0 or self.dc >= self.contact_dc_min

    def hr(self) -> Tuple[float, int]:
        """(nhịp/phút, chất lượng 0–100). (0, 0) nếu chưa đủ tin cậy."""
        if not self.in_contact():
            return 0.0, 0
        if self.last_peak is None or (self.n - self.last_peak) > self.beat_timeout:
            return 0.0, 0
        if len(self.ibis) < self.min_ibis:
            return 0.0, 0
        med = median(self.ibis)
        mad = median([abs(v - med) for v in self.ibis])
        q = 100.0 * (1.0 - (mad / med) / 0.15) - 20.0 * self.consec_outliers
        q = int(max(0.0, min(100.0, q)))
        return 60.0 / med, q


def estimate_hr_series(signal, fs: float, step_s: float = 1.0, **kwargs):
    """Tiện ích offline: chạy estimator trên cả bản ghi, trả về (t, hr, quality) mỗi step_s."""
    est = HeartRateEstimator(fs, **kwargs)
    step = max(1, int(round(step_s * fs)))
    t, hr, q = [], [], []
    for i, x in enumerate(signal):
        est.update(float(x))
        if (i + 1) % step == 0:
            h, qq = est.hr()
            t.append((i + 1) / fs)
            hr.append(h)
            q.append(qq)
    return t, hr, q
