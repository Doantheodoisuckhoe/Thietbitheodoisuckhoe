"""API cho app gateway (điện thoại ghép với đồng hồ) đẩy dữ liệu lên.

Xác thực bằng header X-Device-Key (cấp khi đăng ký thiết bị trên web).
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..alert_engine import evaluate_ecg, evaluate_event, evaluate_vitals
from ..db import get_db, utcnow
from ..models import Alert, Device, DeviceEvent, EcgRecord, VitalSample
from ..notifier import notify_new_alert
from ..schemas import AlertOut, EcgIn, EventsBatch, VitalsBatch
from ..security import get_device
from .patients import current_bp_model

router = APIRouter(prefix="/api/ingest", tags=["ingest (gateway)"])

EVENT_TYPES = {"fall", "sos", "fall_cancelled", "low_battery", "impact"}


class IngestResult(BaseModel):
    accepted: int
    duplicates: int = 0
    alerts: list[int] = []


class EcgResult(BaseModel):
    id: int
    sbp_est: Optional[float]
    dbp_est: Optional[float]
    bp_method: Optional[str]
    calibrated: bool
    alerts: list[int] = []


def _dispatch(bg: BackgroundTasks, alerts: list[Alert]) -> list[int]:
    for a in alerts:
        bg.add_task(notify_new_alert, a.id)
    return [a.id for a in alerts]


@router.get("/me")
def device_info(dev: Device = Depends(get_device)):
    return {"device_id": dev.id, "device_name": dev.name, "patient_id": dev.patient_id,
            "patient_name": dev.patient.full_name}


@router.post("/vitals", response_model=IngestResult)
def ingest_vitals(body: VitalsBatch, bg: BackgroundTasks, dev: Device = Depends(get_device),
                  db: Session = Depends(get_db)):
    new, dup = [], 0
    for s in sorted(body.samples, key=lambda x: x.ts):
        exists = db.scalar(select(VitalSample.id).where(VitalSample.device_id == dev.id, VitalSample.ts == s.ts,
                                                        VitalSample.seq == s.seq))
        if exists:
            dup += 1
            continue
        data = s.model_dump()
        # 0 nghĩa là "không có" trong giao thức BLE
        for k in ("hr", "spo2"):
            if data[k] is not None and data[k] <= 0:
                data[k] = None
        row = VitalSample(patient_id=dev.patient_id, device_id=dev.id, **data)
        db.add(row)
        new.append(row)
    if new:
        last = new[-1]
        dev.last_seen_at = utcnow()
        dev.last_battery, dev.last_charging, dev.last_worn = last.battery_pct, last.charging, last.worn
        if body.firmware:
            dev.firmware = body.firmware
        db.flush()
    alerts = evaluate_vitals(db, dev.patient, new)
    db.commit()
    return IngestResult(accepted=len(new), duplicates=dup, alerts=_dispatch(bg, alerts))


@router.post("/events", response_model=IngestResult)
def ingest_events(body: EventsBatch, bg: BackgroundTasks, dev: Device = Depends(get_device),
                  db: Session = Depends(get_db)):
    accepted, dup, alerts = 0, 0, []
    for e in body.events:
        if e.type not in EVENT_TYPES:
            continue
        if db.scalar(select(DeviceEvent.id).where(DeviceEvent.device_id == dev.id, DeviceEvent.seq == e.seq,
                                                  DeviceEvent.ts == e.ts)):
            dup += 1
            continue
        ev = DeviceEvent(patient_id=dev.patient_id, device_id=dev.id, **e.model_dump())
        db.add(ev)
        db.flush()
        accepted += 1
        a = evaluate_event(db, dev.patient, ev)
        if a:
            alerts.append(a)
    dev.last_seen_at = utcnow()
    db.commit()
    return IngestResult(accepted=accepted, duplicates=dup, alerts=_dispatch(bg, alerts))


@router.post("/ecg", response_model=EcgResult)
def ingest_ecg(body: EcgIn, bg: BackgroundTasks, dev: Device = Depends(get_device), db: Session = Depends(get_db)):
    rec = EcgRecord(patient_id=dev.patient_id, device_id=dev.id, **body.model_dump())
    if rec.pat_ms is not None and rec.pat_ms <= 0:
        rec.pat_ms = None
    model = current_bp_model(db, dev.patient_id)
    if model and rec.pat_ms and rec.status == 0:
        sbp, dbp = model.estimate(rec.pat_ms)
        rec.sbp_est, rec.dbp_est, rec.bp_method = round(sbp, 1), round(dbp, 1), model.method
    db.add(rec)
    dev.last_seen_at = utcnow()
    db.flush()
    alerts = evaluate_ecg(db, dev.patient, rec)
    db.commit()
    return EcgResult(id=rec.id, sbp_est=rec.sbp_est, dbp_est=rec.dbp_est, bp_method=rec.bp_method,
                     calibrated=model is not None, alerts=_dispatch(bg, alerts))


@router.get("/alerts", response_model=list[AlertOut])
def gateway_alerts(since_id: int = 0, dev: Device = Depends(get_device), db: Session = Depends(get_db)):
    """App gateway hỏi định kỳ để biết cảnh báo đã được người nhà xác nhận -> rung đồng hồ trấn an."""
    return list(db.scalars(select(Alert).where(Alert.patient_id == dev.patient_id, Alert.id > since_id)
                           .order_by(Alert.id.desc()).limit(20)))
