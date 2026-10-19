"""Ước lượng huyết áp từ PAT với hiệu chuẩn cá nhân.

Mô hình (xuất phát từ phương trình Moens–Korteweg, dạng tuyến tính theo 1/PAT):

    SBP = a_s + b_s / PAT      DBP = a_d + b_d / PAT      (PAT tính bằng giây)

- 1–2 điểm hiệu chuẩn: giữ hệ số dốc mặc định (dân số), chỉ fit hệ số chặn a.
- >= 3 điểm và SBP trải rộng >= 10 mmHg: fit cả a và b (bình phương tối thiểu),
  b bị giới hạn trong khoảng hợp lý để tránh mô hình "điên" khi dữ liệu ít.

Một điểm hiệu chuẩn = đo ECG+PPG lấy PAT, đồng thời đo máy huyết áp vòng bít.
Nên hiệu chuẩn lại mỗi 2–4 tuần. Kết quả chỉ mang tính THAM KHẢO.

Server dùng bản sao của file này: server/app/bp.py
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

DEFAULT_B_SBP = 50.0   # mmHg·s  (~ -0,8 mmHg/ms quanh PAT = 250 ms)
DEFAULT_B_DBP = 25.0
B_SBP_RANGE = (10.0, 150.0)
B_DBP_RANGE = (5.0, 100.0)


@dataclass
class BpModel:
    a_sbp: float
    b_sbp: float
    a_dbp: float
    b_dbp: float
    n_points: int
    method: str  # "offset" | "regression"

    def estimate(self, pat_ms: float) -> Tuple[float, float]:
        x = 1000.0 / pat_ms
        return self.a_sbp + self.b_sbp * x, self.a_dbp + self.b_dbp * x


def _fit_one(x: np.ndarray, y: np.ndarray, b_default: float, b_range, regression: bool):
    if regression:
        b = float(np.polyfit(x, y, 1)[0])
        b = min(max(b, b_range[0]), b_range[1])
    else:
        b = b_default
    a = float(np.mean(y - b * x))
    return a, b


def fit_model(points: Sequence[Tuple[float, float, float]]) -> Optional[BpModel]:
    """points: [(pat_ms, sbp_ref, dbp_ref), ...]"""
    pts = [p for p in points if p[0] and p[0] > 0]
    if not pts:
        return None
    arr = np.asarray(pts, dtype=float)
    x = 1000.0 / arr[:, 0]
    sbp, dbp = arr[:, 1], arr[:, 2]
    regression = len(pts) >= 3 and (sbp.max() - sbp.min()) >= 10.0 and np.std(x) > 1e-3
    a_s, b_s = _fit_one(x, sbp, DEFAULT_B_SBP, B_SBP_RANGE, regression)
    a_d, b_d = _fit_one(x, dbp, DEFAULT_B_DBP, B_DBP_RANGE, regression)
    return BpModel(a_s, b_s, a_d, b_d, len(pts), "regression" if regression else "offset")
