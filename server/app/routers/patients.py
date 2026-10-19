"""Quản lý người được theo dõi, ngưỡng, người nhà, thiết bị và xem dữ liệu."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..alert_engine import get_thresholds
from ..bp import fit_model
from ..db import get_db, utcnow
from ..models import (Alert, BpCalibration, CareLink, Device, DeviceEvent, EcgRecord, Patient, User,
                      VitalSample)
from ..schemas import (BpModelOut, CalibrationIn, CalibrationOut, CareLinkIn, CareLinkOut, DeviceCreated,
                       DeviceIn, DeviceOut, EcgDetail, EcgSummary, EventOut, PatientIn, PatientOut,
                       PatientSummary, ThresholdsIO, VitalOut)
from ..security import get_current_user, new_device_key, require_patient

router = APIRouter(prefix="/api", tags=["patients"])


# =============================================================================
# Bệnh nhân
# =============================================================================
@router.get("/patients", response_model=list[PatientOut])
def list_patients(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Patient).order_by(Patient.full_name)
    if user.role != "admin":
        q = q.join(CareLink).where(CareLink.user_id == user.id)
    return list(db.scalars(q))


@router.post("/patients", response_model=PatientOut, status_code=201)
def create_patient(body: PatientIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = Patient(**body.model_dump())
    db.add(p)
    db.flush()
    db.add(CareLink(patient_id=p.id, user_id=user.id, priority=1, relation="người tạo"))
    get_thresholds(db, p.id)
    db.commit()
    return p


@router.get("/patients/{pid}", response_model=PatientSummary)
def patient_summary(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = require_patient(db, user, pid)
    latest = db.scalar(select(VitalSample).where(VitalSample.patient_id == pid)
                       .order_by(VitalSample.ts.desc()).limit(1))
    last_hr = db.scalar(select(VitalSample).where(VitalSample.patient_id == pid, VitalSample.hr.is_not(None),
                                                  VitalSample.hr > 0).order_by(VitalSample.ts.desc()).limit(1))
    last_spo2 = db.scalar(select(VitalSample).where(VitalSample.patient_id == pid, VitalSample.spo2.is_not(None))
                          .order_by(VitalSample.ts.desc()).limit(1))
    last_temp = db.scalar(select(VitalSample.skin_temp).where(VitalSample.patient_id == pid,
                                                              VitalSample.skin_temp.is_not(None))
                          .order_by(VitalSample.ts.desc()).limit(1))
    last_ecg = db.scalar(select(EcgRecord).where(EcgRecord.patient_id == pid).order_by(EcgRecord.ts.desc()).limit(1))
    open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.patient_id == pid, Alert.status == "open"))
    return PatientSummary(
        patient=PatientOut.model_validate(p),
        latest=VitalOut.model_validate(latest) if latest else None,
        last_hr=last_hr.hr if last_hr else None,
        last_spo2=last_spo2.spo2 if last_spo2 else None,
        last_spo2_at=last_spo2.ts if last_spo2 else None,
        last_temp=last_temp,
        last_ecg=EcgSummary.model_validate(last_ecg) if last_ecg else None,
        devices=[DeviceOut.model_validate(d) for d in p.devices],
        open_alerts=open_alerts or 0,
    )


@router.put("/patients/{pid}", response_model=PatientOut)
def update_patient(pid: int, body: PatientIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = require_patient(db, user, pid)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    return p


@router.delete("/patients/{pid}", status_code=204)
def delete_patient(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = require_patient(db, user, pid)
    db.delete(p)
    db.commit()


# =============================================================================
# Ngưỡng cảnh báo
# =============================================================================
@router.get("/patients/{pid}/thresholds", response_model=ThresholdsIO)
def get_th(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    th = get_thresholds(db, pid)
    db.commit()
    return th


@router.put("/patients/{pid}/thresholds", response_model=ThresholdsIO)
def put_th(pid: int, body: ThresholdsIO, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    if body.spo2_danger >= body.spo2_warning:
        raise HTTPException(422, "Ngưỡng SpO2 nguy hiểm phải thấp hơn ngưỡng cảnh báo")
    if body.hr_low >= body.hr_high:
        raise HTTPException(422, "Ngưỡng nhịp tim thấp phải nhỏ hơn ngưỡng cao")
    if body.sbp_warning >= body.sbp_danger:
        raise HTTPException(422, "Ngưỡng huyết áp cảnh báo phải nhỏ hơn ngưỡng nguy hiểm")
    if body.day_start_hour >= body.day_end_hour:
        raise HTTPException(422, "Giờ bắt đầu ban ngày phải trước giờ kết thúc")
    th = get_thresholds(db, pid)
    for k, v in body.model_dump().items():
        setattr(th, k, v)
    db.commit()
    return th


# =============================================================================
# Người nhà nhận cảnh báo
# =============================================================================
@router.get("/patients/{pid}/caregivers", response_model=list[CareLinkOut])
def list_caregivers(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    return list(db.scalars(select(CareLink).where(CareLink.patient_id == pid).order_by(CareLink.priority)))


@router.post("/patients/{pid}/caregivers", response_model=CareLinkOut, status_code=201)
def add_caregiver(pid: int, body: CareLinkIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    target = db.scalar(select(User).where(User.email == body.email.lower()))
    if target is None:
        raise HTTPException(404, "Người này chưa có tài khoản — hãy đăng ký trước trên app/web")
    link = db.scalar(select(CareLink).where(CareLink.patient_id == pid, CareLink.user_id == target.id))
    if link is None:
        link = CareLink(patient_id=pid, user_id=target.id)
        db.add(link)
    link.relation, link.priority, link.receive_sms = body.relation, body.priority, body.receive_sms
    db.commit()
    db.refresh(link)
    return link


@router.delete("/patients/{pid}/caregivers/{link_id}", status_code=204)
def remove_caregiver(pid: int, link_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    link = db.get(CareLink, link_id)
    if link and link.patient_id == pid:
        db.delete(link)
        db.commit()


# =============================================================================
# Thiết bị — API key cấp cho app gateway (điện thoại ghép với đồng hồ)
# =============================================================================
@router.get("/patients/{pid}/devices", response_model=list[DeviceOut])
def list_devices(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return require_patient(db, user, pid).devices


@router.post("/patients/{pid}/devices", response_model=DeviceCreated, status_code=201)
def create_device(pid: int, body: DeviceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    key, prefix, h = new_device_key()
    d = Device(patient_id=pid, name=body.name, serial=body.serial, api_key_prefix=prefix, api_key_hash=h)
    db.add(d)
    db.commit()
    return DeviceCreated(**DeviceOut.model_validate(d).model_dump(), api_key=key)


@router.delete("/patients/{pid}/devices/{did}", status_code=204)
def delete_device(pid: int, did: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    d = db.get(Device, did)
    if d and d.patient_id == pid:
        db.delete(d)
        db.commit()


# =============================================================================
# Dữ liệu
# =============================================================================
def _range(start: Optional[datetime], end: Optional[datetime], default_hours: int):
    end = end or utcnow()
    start = start or end - timedelta(hours=default_hours)
    return start, end


@router.get("/patients/{pid}/vitals", response_model=list[VitalOut])
def get_vitals(pid: int, start: Optional[datetime] = None, end: Optional[datetime] = None,
               bucket_s: int = Query(0, ge=0, description="gộp trung bình theo khoảng (giây), 0 = dữ liệu gốc"),
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    start, end = _range(start, end, 24)
    rows = list(db.scalars(select(VitalSample).where(VitalSample.patient_id == pid, VitalSample.ts >= start,
                                                     VitalSample.ts <= end).order_by(VitalSample.ts).limit(50000)))
    if bucket_s <= 0:
        return rows
    return _downsample(rows, bucket_s)


def _downsample(rows: list[VitalSample], bucket_s: int) -> list[VitalOut]:
    """Gộp theo khung thời gian để vẽ biểu đồ nhẹ hơn (HR/nhiệt độ: trung bình, SpO2: thấp nhất)."""
    out, cur, key = [], [], None
    for r in rows + [None]:
        k = int(r.ts.timestamp()) // bucket_s if r else None
        if cur and k != key:
            def avg(vals):
                v = [x for x in vals if x is not None]
                return sum(v) / len(v) if v else None
            hrs = [c.hr for c in cur if c.hr and (c.hr_quality or 0) >= 50]
            spo2 = [c.spo2 for c in cur if c.spo2]
            out.append(VitalOut(ts=cur[len(cur) // 2].ts, hr=avg(hrs), hr_quality=None,
                                spo2=min(spo2) if spo2 else None, spo2_quality=None,
                                skin_temp=avg([c.skin_temp for c in cur]),
                                activity=sum(c.activity or 0 for c in cur),
                                battery_pct=cur[-1].battery_pct, worn=any(c.worn for c in cur),
                                charging=cur[-1].charging))
            cur = []
        if r is not None:
            cur.append(r)
            key = k
    return out


@router.get("/patients/{pid}/events", response_model=list[EventOut])
def get_events(pid: int, start: Optional[datetime] = None, end: Optional[datetime] = None,
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    start, end = _range(start, end, 24 * 7)
    return list(db.scalars(select(DeviceEvent).where(DeviceEvent.patient_id == pid, DeviceEvent.ts >= start,
                                                     DeviceEvent.ts <= end).order_by(DeviceEvent.ts.desc())))


@router.get("/patients/{pid}/ecg", response_model=list[EcgSummary])
def list_ecg(pid: int, limit: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    return list(db.scalars(select(EcgRecord).where(EcgRecord.patient_id == pid)
                           .order_by(EcgRecord.ts.desc()).limit(limit)))


@router.get("/ecg/{eid}", response_model=EcgDetail)
def get_ecg(eid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.get(EcgRecord, eid)
    if rec is None:
        raise HTTPException(404, "Không tìm thấy bản ghi ECG")
    require_patient(db, user, rec.patient_id)
    return rec


# =============================================================================
# Hiệu chuẩn huyết áp
# =============================================================================
def current_bp_model(db: Session, pid: int):
    pts = [(c.pat_ms, c.sbp_ref, c.dbp_ref) for c in
           db.scalars(select(BpCalibration).where(BpCalibration.patient_id == pid)
                      .order_by(BpCalibration.ts.desc()).limit(10))]
    return fit_model(pts)


@router.get("/patients/{pid}/bp-calibrations", response_model=list[CalibrationOut])
def list_calibrations(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    return list(db.scalars(select(BpCalibration).where(BpCalibration.patient_id == pid)
                           .order_by(BpCalibration.ts.desc())))


@router.get("/patients/{pid}/bp-model", response_model=Optional[BpModelOut])
def get_bp_model(pid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    m = current_bp_model(db, pid)
    return BpModelOut(**m.__dict__) if m else None


@router.post("/patients/{pid}/bp-calibrations", response_model=CalibrationOut, status_code=201)
def add_calibration(pid: int, body: CalibrationIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    pat = body.pat_ms
    if body.ecg_id is not None:
        rec = db.get(EcgRecord, body.ecg_id)
        if rec is None or rec.patient_id != pid or not rec.pat_ms:
            raise HTTPException(422, "Lần đo ECG này không có PAT hợp lệ")
        pat = rec.pat_ms
    if not pat:
        raise HTTPException(422, "Cần ecg_id hoặc pat_ms")
    cal = BpCalibration(patient_id=pid, ecg_id=body.ecg_id, pat_ms=pat, sbp_ref=body.sbp_ref,
                        dbp_ref=body.dbp_ref, note=body.note)
    db.add(cal)
    db.flush()
    # cập nhật lại ước lượng cho lần đo dùng để hiệu chuẩn
    m = current_bp_model(db, pid)
    if body.ecg_id is not None and m:
        rec = db.get(EcgRecord, body.ecg_id)
        rec.sbp_est, rec.dbp_est = (round(v, 1) for v in m.estimate(rec.pat_ms))
        rec.bp_method = m.method
    db.commit()
    return cal


@router.delete("/patients/{pid}/bp-calibrations/{cid}", status_code=204)
def delete_calibration(pid: int, cid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_patient(db, user, pid)
    c = db.get(BpCalibration, cid)
    if c and c.patient_id == pid:
        db.delete(c)
        db.commit()
