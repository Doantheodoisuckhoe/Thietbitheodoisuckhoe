"""Kiểm thử thuật toán bằng tín hiệu tổng hợp:  cd algorithm && python -m pytest -q"""
import numpy as np
import pytest
from scipy.signal import lfilter

from hwalgo import synthetic as syn
from hwalgo.bp import fit_model
from hwalgo.ecg_rpeak import detect_r_peaks, heart_rate_from_peaks, match_beats
from hwalgo.fall import FallDetector
from hwalgo.filters import Biquad, BiquadChain, bandpass_sections, design_biquad, filtfilt_ss
from hwalgo.hr_ppg import HeartRateEstimator, estimate_hr_series
from hwalgo.pat import compute_pat
from hwalgo.spo2 import STATUS_NO_CONTACT, STATUS_OK, compute_spo2, spo2_from_ratio


# ---------------------------------------------------------------- bộ lọc
def test_biquad_streaming_matches_lfilter():
    sec = design_biquad("lowpass", 5.0, 100.0)
    x = np.random.default_rng(0).normal(size=500)
    bq = Biquad(sec)
    y_stream = np.array([bq.process(v) for v in x])
    y_ref = lfilter(sec[0], sec[1], x)
    assert np.allclose(y_stream, y_ref, atol=1e-12)


def test_steady_state_init_removes_dc_transient():
    chain = BiquadChain(bandpass_sections(0.5, 4.0, 50.0))
    chain.reset_to(1e5)
    out = [chain.process(1e5) for _ in range(100)]
    assert max(abs(v) for v in out) < 1e-6
    y = filtfilt_ss(bandpass_sections(0.5, 4.0, 50.0), np.full(300, 1e5))
    assert np.max(np.abs(y)) < 1e-6


# ---------------------------------------------------------------- nhịp tim PPG
@pytest.mark.parametrize("hr", [48, 72, 110, 150])
def test_hr_constant(hr):
    fs = 50.0
    x = syn.ppg(60, fs, hr_bpm=hr, seed=hr)
    t, h, q = estimate_hr_series(x, fs)
    tail = np.array(h[20:])
    assert np.all(tail > 0)
    assert np.median(np.abs(tail - hr)) <= 3.0
    assert np.median(q[20:]) >= 50


def test_hr_tracks_step_change():
    fs = 50.0
    x = syn.ppg(90, fs, hr_bpm=lambda t: 70 if t < 45 else 100, seed=3)
    t, h, q = estimate_hr_series(x, fs)
    assert abs(h[40] - 70) <= 3
    assert abs(h[-1] - 100) <= 3   # sau 45 s phải bắt kịp


def test_hr_no_contact():
    est = HeartRateEstimator(50.0, contact_dc_min=50000)
    for v in np.random.default_rng(0).normal(2000, 50, 1000):
        est.update(v)
    assert est.hr() == (0.0, 0)


# ---------------------------------------------------------------- SpO2
@pytest.mark.parametrize("ratio", [0.45, 0.6, 0.8, 1.0])
def test_spo2_ratio(ratio):
    red, ir = syn.red_ir(30, 100.0, ratio, seed=int(ratio * 100))
    res = compute_spo2(red, ir, 100.0)
    assert res.status == STATUS_OK
    assert abs(res.ratio - ratio) < 0.03
    assert abs(res.spo2 - spo2_from_ratio(ratio)) < 1.5


def test_spo2_no_contact():
    rng = np.random.default_rng(0)
    res = compute_spo2(rng.normal(500, 10, 3000), rng.normal(500, 10, 3000), 100.0)
    assert res.status == STATUS_NO_CONTACT


# ---------------------------------------------------------------- ECG
@pytest.mark.parametrize("hr,invert,seed", [(60, False, 1), (75, False, 2), (120, False, 3), (75, True, 4), (45, False, 5)])
def test_rpeak_detection(hr, invert, seed):
    fs = 256.0
    x, ref = syn.ecg(30, fs, hr_bpm=hr, seed=seed, invert=invert)
    det = detect_r_peaks(x, fs)
    tp, fp, fn = match_beats(det, ref, int(0.15 * fs))
    se = tp / (tp + fn)
    ppv = tp / (tp + fp)
    assert se >= 0.97 and ppv >= 0.97, (se, ppv)
    assert abs(heart_rate_from_peaks(det, fs) - hr) < 3


def test_rpeak_noisy():
    fs = 256.0
    x, ref = syn.ecg(30, fs, hr_bpm=80, seed=7, noise=0.12, wander=0.5)
    det = detect_r_peaks(x, fs)
    tp, fp, fn = match_beats(det, ref, int(0.15 * fs))
    assert tp / (tp + fn) >= 0.95 and tp / (tp + fp) >= 0.95


def test_match_beats():
    assert match_beats([10, 50, 100], [12, 98, 200], 5) == (2, 1, 1)


# ---------------------------------------------------------------- PAT
def _pat_case(pat_s, seed=0):
    fs_e, fs_p, dur = 256.0, 200.0, 30.0
    rng = np.random.default_rng(seed)
    rt = syn.beat_times(dur, 70, rng)
    t_e = np.arange(int(dur * fs_e)) / fs_e
    # ECG từ đúng các thời điểm R
    x = np.zeros_like(t_e)
    for r in rt:
        x += np.exp(-0.5 * ((t_e - r) / 0.011) ** 2) - 0.25 * np.exp(-0.5 * ((t_e - r - 0.032) / 0.012) ** 2)
    x += rng.normal(0, 0.02, len(t_e))
    t_p = np.arange(int(dur * fs_p)) / fs_p + 0.0013  # lệch pha giữa 2 chip
    p = syn.ppg_from_beats(t_p, rt + pat_s, seed=seed)
    peaks = detect_r_peaks(x * 1000, fs_e)
    r_ms = t_e[peaks] * 1000.0
    return compute_pat(r_ms, p, t_p * 1000.0)


def test_pat_tracks_changes():
    a = _pat_case(0.250, seed=1)
    b = _pat_case(0.220, seed=2)
    assert a.status == 0 and b.status == 0
    assert a.n_valid >= 25
    assert abs((a.pat_ms - b.pat_ms) - 30.0) < 3.0
    assert a.iqr_ms < 10


# ---------------------------------------------------------------- huyết áp
def test_bp_single_point_offset():
    m = fit_model([(250.0, 125.0, 80.0)])
    s, d = m.estimate(250.0)
    assert abs(s - 125) < 1e-6 and abs(d - 80) < 1e-6
    s2, _ = m.estimate(230.0)
    assert s2 > s  # PAT ngắn hơn -> huyết áp cao hơn
    assert m.method == "offset"


def test_bp_regression_recovers_model():
    true_a, true_b = 20.0, 26.0
    pts = []
    for pat in [200.0, 230.0, 260.0, 300.0]:
        x = 1000 / pat
        pts.append((pat, true_a + true_b * x, 40 + 10 * x))
    m = fit_model(pts)
    assert m.method == "regression"
    assert abs(m.b_sbp - true_b) < 1e-6
    assert abs(m.estimate(240.0)[0] - (true_a + true_b * 1000 / 240)) < 1e-6


# ---------------------------------------------------------------- té ngã
def _run_fall(acc, fs=104.0, **kw):
    fd = FallDetector(fs=fs, **kw)
    events = []
    for ax, ay, az in acc:
        ev = fd.update(ax, ay, az)
        if ev:
            events.append(ev)
    return events, fd


@pytest.mark.parametrize("seed,peak,ff,moves", [(0, 4.0, True, 0), (1, 3.2, False, 0), (2, 5.5, True, 2),
                                               (3, 3.0, False, 3), (4, 6.0, True, 1)])
def test_fall_detected(seed, peak, ff, moves):
    acc = syn.acc_fall(104.0, peak_g=peak, freefall=ff, move_blocks=moves, seed=seed)
    events, _ = _run_fall(acc)
    falls = [e for e in events if e["type"] == "fall"]
    assert len(falls) == 1
    assert falls[0]["peak_g"] >= 2.8
    assert falls[0]["angle_deg"] > 45
    assert falls[0]["freefall"] == ff


@pytest.mark.parametrize("acc", [
    syn.acc_walk(60, 104.0),
    syn.acc_clap_then_walk(104.0),
    syn.acc_sit_down(104.0),
])
def test_no_false_alarm(acc):
    events, _ = _run_fall(acc)
    assert not [e for e in events if e["type"] == "fall"]


def test_fall_cancel_by_button():
    acc = syn.acc_fall(104.0, peak_g=4.0)
    fd = FallDetector(fs=104.0)
    falls = 0
    for i, (ax, ay, az) in enumerate(acc):
        ev = fd.update(ax, ay, az)
        if ev and ev["type"] == "impact":
            assert fd.cancel()
        if ev and ev["type"] == "fall":
            falls += 1
    assert falls == 0


def test_activity_counter():
    fd = FallDetector(fs=104.0)
    for ax, ay, az in syn.acc_still(10, 104.0):
        fd.update(ax, ay, az)
    assert fd.take_activity() == 0
    assert fd.still_seconds() > 9
    for ax, ay, az in syn.acc_walk(10, 104.0):
        fd.update(ax, ay, az)
    assert fd.take_activity() > 300
