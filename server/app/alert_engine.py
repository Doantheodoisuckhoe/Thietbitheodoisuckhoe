"""Bộ xử lý cảnh báo — nơi quyết định có cảnh báo hay không.

Quy tắc (ngưỡng mặc định theo đề cương, chỉnh được cho từng người trên web).
Mọi cảnh báo chỉ phát khi vượt ngưỡng LIÊN TỤC, tránh báo động giả:

  SpO2        : N lần đo liên tiếp (mặc định 2) < 94%  -> Cảnh báo;  < 90% -> Nguy hiểm
  Nhịp tim    : lúc nghỉ, >= 90% mẫu trong 5 phút < 50 hoặc > 120 -> Cảnh báo
                kèm SpO2 thấp (< ngưỡng cảnh báo) trong 30 phút gần nhất -> Nguy hiểm
  Nhiệt độ da : trung vị 30 phút cao hơn mức nền cá nhân (trung vị 7 ngày) >= 1 °C -> Cảnh báo
  Huyết áp    : SBP ước lượng >= 180 -> Nguy hiểm; trung bình ngày >= 140 trong 3 ngày liên tiếp -> Cảnh báo
  Té ngã, SOS : nguy hiểm ngay (đồng hồ đã xác nhận bất động 30 s / giữ nút 3 s)
  Không cử động ban ngày: đeo đồng hồ nhưng không chuyển động suốt 3 giờ (trong khung 7h–21h) -> Cảnh báo
  Mất kết nối > 30 phút, pin yếu -> Thông tin (chỉ push, không SMS)

Chống lặp: cùng loại cảnh báo trong thời gian "cooldown" (30 phút) không tạo mới,
trừ khi mức độ tăng lên (cảnh báo -> nguy hiểm). Té ngã và SOS luôn tạo mới.
"""
from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import utcnow
from .models import Alert, DeviceEvent, EcgRecord, Patient, Thresholds, VitalSample

log = logging.getLogger("alert_engine")

LEVEL_RANK = {"info": 0, "warning": 1, "danger": 2}
LEVEL_LABEL = {"info": "Thông tin", "warning": "Cảnh báo", "danger": "NGUY HIỂM"}

MIN_HR_QUALITY = 50
MIN_SPO2_QUALITY = 40
REST_ACTIVITY_PER_S = 5    # <= 5 mẫu IMU/giây có chuyển động -> coi là đang nghỉ
INACTIVE_ACTIVITY_MAX = 5  # <= 5 mẫu/chu kỳ -> coi như không cử động


def get_thresholds(db: Session, patient_id: int) -> Thresholds:
    th = db.get(Thresholds, patient_id)
    if th is None:
        th = Thresholds(patient_id=patient_id)
        db.add(th)
        db.flush()
        db.refresh(th)
    return th


def create_alert(db: Session, patient: Patient, type_: str, level: str, title: str, message: str,
                 value: Optional[float] = None, event_ts: Optional[datetime] = None,
                 dedupe: bool = True) -> Optional[Alert]:
    th = get_thresholds(db, patient.id)
    now = utcnow()
    if dedupe:
        recent = db.scalar(
            select(Alert)
            .where(Alert.patient_id == patient.id, Alert.type == type_, Alert.status != "resolved",
                   Alert.created_at >= now - timedelta(minutes=th.cooldown_min))
            .order_by(Alert.created_at.desc()).limit(1))
        if recent is not None and LEVEL_RANK[level] <= LEVEL_RANK[recent.level]:
            return None
    alert = Alert(patient_id=patient.id, type=type_, level=level, title=title, message=message,
                  value=value, event_ts=event_ts or now, created_at=now)
    db.add(alert)
    db.flush()
    log.info("ALERT #%s [%s] %s – %s: %s", alert.id, level, patient.full_name, title, message)
    return alert


# =============================================================================
# Chỉ số định kỳ (gói VITALS)
# =============================================================================
def evaluate_vitals(db: Session, patient: Patient, new_samples: list[VitalSample]) -> list[Alert]:
    if not new_samples:
        return []
    th = get_thresholds(db, patient.id)
    ref_ts = max(s.ts for s in new_samples)
    out: list[Optional[Alert]] = []
    if any(s.spo2 for s in new_samples):
        out.append(_rule_spo2(db, patient, th, ref_ts))
    out.append(_rule_hr(db, patient, th, ref_ts))
    out.append(_rule_temp(db, patient, th, ref_ts))
    return [a for a in out if a is not None]


def _window(db: Session, patient_id: int, start: datetime, end: datetime) -> list[VitalSample]:
    return list(db.scalars(
        select(VitalSample)
        .where(VitalSample.patient_id == patient_id, VitalSample.ts > start, VitalSample.ts <= end)
        .order_by(VitalSample.ts)))


def _recent_min_spo2(db: Session, patient_id: int, end: datetime, minutes: int = 30) -> Optional[float]:
    return db.scalar(select(func.min(VitalSample.spo2)).where(
        VitalSample.patient_id == patient_id, VitalSample.spo2.is_not(None),
        VitalSample.spo2_quality >= MIN_SPO2_QUALITY,
        VitalSample.ts > end - timedelta(minutes=minutes), VitalSample.ts <= end))


def _rule_spo2(db, patient, th, ref_ts) -> Optional[Alert]:
    rows = list(db.scalars(
        select(VitalSample)
        .where(VitalSample.patient_id == patient.id, VitalSample.spo2.is_not(None),
               VitalSample.spo2_quality >= MIN_SPO2_QUALITY, VitalSample.ts <= ref_ts,
               VitalSample.ts > ref_ts - timedelta(minutes=60))
        .order_by(VitalSample.ts.desc()).limit(th.spo2_consecutive)))
    if len(rows) < th.spo2_consecutive:
        return None
    vals = [r.spo2 for r in rows]
    if all(v < th.spo2_danger for v in vals):
        level, thr = "danger", th.spo2_danger
    elif all(v < th.spo2_warning for v in vals):
        level, thr = "warning", th.spo2_warning
    else:
        return None
    return create_alert(db, patient, "spo2_low", level, "SpO2 thấp",
                        f"SpO2 {vals[0]:.0f}% — {len(vals)} lần đo liên tiếp dưới {thr:.0f}%",
                        value=vals[0], event_ts=rows[0].ts)


def _rule_hr(db, patient, th, ref_ts) -> Optional[Alert]:
    rows = [r for r in _window(db, patient.id, ref_ts - timedelta(seconds=th.hr_persist_s), ref_ts) if r.worn]
    if not rows:
        return None
    interval = statistics.median(r.interval_s or 10 for r in rows)
    expected = th.hr_persist_s / interval
    valid = [r for r in rows if r.hr and (r.hr_quality or 0) >= MIN_HR_QUALITY
             and (r.activity or 0) <= REST_ACTIVITY_PER_S * (r.interval_s or 10)]
    if len(valid) < 0.6 * expected:
        return None  # không đủ dữ liệu lúc nghỉ đáng tin
    abnormal = [r for r in valid if r.hr < th.hr_low or r.hr > th.hr_high]
    if len(abnormal) < 0.9 * len(valid):
        return None
    hr = statistics.median(r.hr for r in abnormal)
    kind = "chậm" if hr < th.hr_low else "nhanh"
    minutes = th.hr_persist_s / 60
    level = "warning"
    msg = f"Nhịp tim lúc nghỉ {hr:.0f} lần/phút ({kind}) kéo dài {minutes:.0f} phút"
    spo2 = _recent_min_spo2(db, patient.id, ref_ts)
    if spo2 is not None and spo2 < th.spo2_warning:
        level = "danger"
        msg += f", kèm SpO2 thấp {spo2:.0f}%"
    return create_alert(db, patient, "hr_abnormal", level, f"Nhịp tim {kind} bất thường", msg,
                        value=hr, event_ts=ref_ts)


def _rule_temp(db, patient, th, ref_ts) -> Optional[Alert]:
    if patient.temp_baseline is None:
        return None
    rows = _window(db, patient.id, ref_ts - timedelta(seconds=th.temp_persist_s), ref_ts)
    temps = [r.skin_temp for r in rows if r.worn and r.skin_temp is not None]
    if not rows:
        return None
    interval = statistics.median(r.interval_s or 10 for r in rows)
    if len(temps) < 0.6 * th.temp_persist_s / interval:
        return None
    med = statistics.median(temps)
    if med - patient.temp_baseline < th.temp_rise:
        return None
    return create_alert(db, patient, "temp_rise", "warning", "Nhiệt độ da tăng",
                        f"Nhiệt độ da {med:.1f} °C, cao hơn mức nền {patient.temp_baseline:.1f} °C "
                        f"({med - patient.temp_baseline:+.1f} °C) trong {th.temp_persist_s // 60} phút",
                        value=med, event_ts=ref_ts)


def update_temp_baselines(db: Session, now: Optional[datetime] = None, min_samples: int = 1000) -> None:
    """Mức nền = trung vị nhiệt độ da 7 ngày (bỏ 1 giờ gần nhất). Chạy mỗi giờ."""
    now = now or utcnow()
    for p in db.scalars(select(Patient)):
        temps = list(db.scalars(select(VitalSample.skin_temp).where(
            VitalSample.patient_id == p.id, VitalSample.worn.is_(True), VitalSample.skin_temp.is_not(None),
            VitalSample.ts > now - timedelta(days=7), VitalSample.ts <= now - timedelta(hours=1))))
        if len(temps) >= min_samples:
            p.temp_baseline = round(statistics.median(temps), 2)
            p.temp_baseline_at = now
    db.commit()


# =============================================================================
# Sự kiện từ đồng hồ
# =============================================================================
def evaluate_event(db: Session, patient: Patient, ev: DeviceEvent) -> Optional[Alert]:
    th = get_thresholds(db, patient.id)
    if ev.type == "fall" and th.fall_enabled:
        g = f"{ev.value1:.1f} g" if ev.value1 else "mạnh"
        return create_alert(db, patient, "fall", "danger", "Phát hiện té ngã",
                            f"Va chạm {g}, sau đó bất động 30 giây", value=ev.value1, event_ts=ev.ts,
                            dedupe=False)
    if ev.type == "sos":
        return create_alert(db, patient, "sos", "danger", "Bấm nút SOS",
                            "Người dùng giữ nút SOS trên đồng hồ", event_ts=ev.ts, dedupe=False)
    if ev.type == "low_battery":
        pct = f" ({ev.value1:.0f}%)" if ev.value1 is not None else ""
        return create_alert(db, patient, "low_battery", "info", "Pin đồng hồ yếu",
                            f"Pin còn thấp{pct}, hãy sạc đồng hồ", value=ev.value1, event_ts=ev.ts)
    return None  # impact / fall_cancelled: chỉ lưu lại


# =============================================================================
# ECG / huyết áp
# =============================================================================
def evaluate_ecg(db: Session, patient: Patient, rec: EcgRecord) -> list[Alert]:
    if rec.sbp_est is None:
        return []
    th = get_thresholds(db, patient.id)
    out = []
    if rec.sbp_est >= th.sbp_danger:
        out.append(create_alert(db, patient, "bp_high", "danger", "Huyết áp rất cao (ước lượng)",
                                f"Huyết áp tâm thu ước lượng {rec.sbp_est:.0f} mmHg. "
                                f"Nên đo lại bằng máy vòng bít.", value=rec.sbp_est, event_ts=rec.ts))
    tz = ZoneInfo(get_settings().timezone)
    first_day = rec.ts.astimezone(tz).date() - timedelta(days=th.bp_trend_days - 1)
    start = datetime.combine(first_day, datetime.min.time(), tzinfo=tz)
    rows = db.scalars(select(EcgRecord).where(EcgRecord.patient_id == patient.id, EcgRecord.sbp_est.is_not(None),
                                             EcgRecord.ts >= start, EcgRecord.ts <= rec.ts))
    by_day = defaultdict(list)
    for r in rows:
        by_day[r.ts.astimezone(tz).date()].append(r.sbp_est)
    means = {d: sum(v) / len(v) for d, v in by_day.items()}
    if len(means) >= th.bp_trend_days and all(m >= th.sbp_warning for m in means.values()):
        avg = sum(means.values()) / len(means)
        out.append(create_alert(db, patient, "bp_trend", "warning", "Xu hướng huyết áp cao",
                                f"Huyết áp tâm thu trung bình {avg:.0f} mmHg, >= {th.sbp_warning:.0f} "
                                f"suốt {th.bp_trend_days} ngày liên tiếp (ước lượng)", value=avg, event_ts=rec.ts))
    return [a for a in out if a is not None]


# =============================================================================
# Kiểm tra định kỳ (mỗi phút)
# =============================================================================
def periodic_checks(db: Session, now: Optional[datetime] = None) -> list[Alert]:
    now = now or utcnow()
    out = []
    for p in db.scalars(select(Patient)):
        if not p.devices:
            continue
        th = get_thresholds(db, p.id)
        out.append(_rule_inactivity(db, p, th, now))
        out.append(_rule_offline(db, p, now))
    db.commit()
    return [a for a in out if a is not None]


def _rule_inactivity(db, patient, th, now) -> Optional[Alert]:
    tz = ZoneInfo(get_settings().timezone)
    local_now = now.astimezone(tz)
    start = now - timedelta(hours=th.inactivity_hours)
    day_start = local_now.replace(hour=th.day_start_hour, minute=0, second=0, microsecond=0)
    if start.astimezone(tz) < day_start:
        return None  # cửa sổ 3 giờ phải nằm trọn trong ban ngày
    if th.day_end_hour < 24 and local_now >= local_now.replace(hour=th.day_end_hour, minute=0, second=0,
                                                               microsecond=0):
        return None
    rows = _window(db, patient.id, start, now)
    if not rows:
        return None
    interval = statistics.median(r.interval_s or 10 for r in rows)
    if len(rows) < 0.7 * th.inactivity_hours * 3600 / interval:
        return None  # thiếu dữ liệu (mất kết nối) -> do quy tắc mất kết nối xử lý
    if sum(1 for r in rows if r.worn) < 0.9 * len(rows):
        return None  # tháo đồng hồ, không phải bất động
    moving = sum(1 for r in rows if (r.activity or 0) > INACTIVE_ACTIVITY_MAX)
    if moving > 0.02 * len(rows):
        return None
    return create_alert(db, patient, "inactivity", "warning", "Không cử động ban ngày",
                        f"Không phát hiện chuyển động trong {th.inactivity_hours:g} giờ "
                        f"(từ {start.astimezone(tz):%H:%M})", event_ts=now)


def _rule_offline(db, patient, now) -> Optional[Alert]:
    seen = [d.last_seen_at for d in patient.devices if d.last_seen_at]
    if not seen:
        return None
    last = max(seen)
    minutes = get_settings().device_offline_min
    if now - last < timedelta(minutes=minutes):
        return None
    exists = db.scalar(select(Alert.id).where(Alert.patient_id == patient.id, Alert.type == "device_offline",
                                              Alert.created_at >= last))
    if exists:
        return None
    tz = ZoneInfo(get_settings().timezone)
    return create_alert(db, patient, "device_offline", "info", "Mất kết nối đồng hồ",
                        f"Không nhận được dữ liệu từ {last.astimezone(tz):%H:%M %d/%m} "
                        f"(hơn {minutes} phút). Kiểm tra điện thoại/đồng hồ.", event_ts=now, dedupe=False)
