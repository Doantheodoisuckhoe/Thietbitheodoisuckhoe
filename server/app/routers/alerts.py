from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, utcnow
from ..models import Alert, CareLink, User
from ..schemas import AlertDetail, AlertOut, DeliveryOut
from ..security import can_access_patient, get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _get(db: Session, user: User, aid: int) -> Alert:
    a = db.get(Alert, aid)
    if a is None or not can_access_patient(db, user, a.patient_id):
        raise HTTPException(404, "Không tìm thấy cảnh báo")
    return a


def _secs(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
    return round((b - a).total_seconds(), 2) if a and b else None


def latency(a: Alert) -> dict:
    """Độ trễ (giây) tính từ lúc sự kiện xảy ra trên đồng hồ."""
    return {
        "device_to_server": _secs(a.event_ts, a.created_at),
        "push_sent": _secs(a.event_ts, a.push_sent_at),
        "push_delivered": _secs(a.event_ts, a.delivered_at),
        "sms_sent": _secs(a.event_ts, a.sms_sent_at),
        "acknowledged": _secs(a.event_ts, a.acknowledged_at),
    }


@router.get("", response_model=list[AlertOut])
def list_alerts(patient_id: Optional[int] = None, status: Optional[str] = None, limit: int = 100,
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Alert).order_by(Alert.created_at.desc()).limit(min(limit, 500))
    if user.role != "admin":
        q = q.where(Alert.patient_id.in_(select(CareLink.patient_id).where(CareLink.user_id == user.id)))
    if patient_id:
        q = q.where(Alert.patient_id == patient_id)
    if status:
        q = q.where(Alert.status == status)
    return list(db.scalars(q))


@router.get("/latency-stats")
def latency_stats(patient_id: Optional[int] = None, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """Thống kê độ trễ cảnh báo cho chương kiểm chứng (mục tiêu: push < 30 s, SMS < 60 s)."""
    alerts = list_alerts(patient_id, None, 500, user, db)
    out = {}
    for key in ("device_to_server", "push_sent", "push_delivered", "sms_sent"):
        vals = sorted(v for v in (latency(a)[key] for a in alerts if a.type in ("fall", "sos") or a.level == "danger")
                      if v is not None)
        if vals:
            out[key] = {"n": len(vals), "mean": round(sum(vals) / len(vals), 2), "max": vals[-1],
                        "p95": vals[min(len(vals) - 1, int(0.95 * len(vals)))]}
    return out


@router.get("/{aid}", response_model=AlertDetail)
def get_alert(aid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = _get(db, user, aid)
    return AlertDetail(**AlertOut.model_validate(a).model_dump(),
                       deliveries=[DeliveryOut.model_validate(d) for d in a.deliveries],
                       patient_name=a.patient.full_name, latency_s=latency(a))


@router.post("/{aid}/ack", response_model=AlertOut)
def acknowledge(aid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = _get(db, user, aid)
    if a.status == "open":
        a.status = "acknowledged"
        a.acknowledged_by = user.id
        a.acknowledged_at = utcnow()
        if a.delivered_at is None:
            a.delivered_at = a.acknowledged_at
        db.commit()
    return a


@router.post("/{aid}/resolve", response_model=AlertOut)
def resolve(aid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = _get(db, user, aid)
    if a.status != "resolved":
        if a.acknowledged_at is None:
            a.acknowledged_at, a.acknowledged_by = utcnow(), user.id
        a.status = "resolved"
        a.resolved_at = utcnow()
        db.commit()
    return a


@router.post("/{aid}/delivered", status_code=204)
def delivered(aid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """App người nhà gọi ngay khi nhận được push -> đo độ trễ đầu-cuối."""
    a = _get(db, user, aid)
    if a.delivered_at is None:
        a.delivered_at = utcnow()
        db.commit()
