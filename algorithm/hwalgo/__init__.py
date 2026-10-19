"""hwalgo — thuật toán xử lý tín hiệu cho thiết bị đeo tay giám sát sức khỏe.

Mỗi module ở đây là bản "tham chiếu" bằng Python; firmware C port lại đúng logic.
"""
from .bp import BpModel, fit_model
from .ecg_rpeak import detect_r_peaks, heart_rate_from_peaks, match_beats
from .fall import FallDetector
from .hr_ppg import HeartRateEstimator, estimate_hr_series
from .pat import compute_pat
from .spo2 import compute_spo2, spo2_from_ratio

__all__ = [
    "BpModel", "fit_model", "detect_r_peaks", "heart_rate_from_peaks", "match_beats",
    "FallDetector", "HeartRateEstimator", "estimate_hr_series", "compute_pat",
    "compute_spo2", "spo2_from_ratio",
]
