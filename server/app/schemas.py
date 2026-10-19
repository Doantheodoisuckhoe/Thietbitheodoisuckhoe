"""Kiểu dữ liệu vào/ra của API (Pydantic v2)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- người dùng
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserOut(ORM):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PushTokenIn(BaseModel):
    token: str
    platform: Optional[str] = "android"


# ---------------------------------------------------------------- bệnh nhân
class PatientIn(BaseModel):
    full_name: str
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class PatientOut(ORM):
    id: int
    full_name: str
    birth_year: Optional[int]
    gender: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    temp_baseline: Optional[float]


class ThresholdsIO(ORM):
    spo2_warning: float = 94
    spo2_danger: float = 90
    spo2_consecutive: int = Field(2, ge=1, le=10)
    hr_low: float = 50
    hr_high: float = 120
    hr_persist_s: int = Field(300, ge=30)
    temp_rise: float = 1.0
    temp_persist_s: int = Field(1800, ge=60)
    sbp_warning: float = 140
    sbp_danger: float = 180
    bp_trend_days: int = Field(3, ge=1, le=14)
    inactivity_hours: float = Field(3.0, gt=0)
    day_start_hour: int = Field(7, ge=0, le=23)
    day_end_hour: int = Field(21, ge=1, le=24)
    fall_enabled: bool = True
    escalation_danger_s: int = Field(30, ge=5)
    escalation_warning_s: int = Field(300, ge=5)
    cooldown_min: int = Field(30, ge=1)


class CareLinkIn(BaseModel):
    email: EmailStr
    relation: Optional[str] = None
    priority: int = 1
    receive_sms: bool = True


class CareLinkOut(ORM):
    id: int
    user_id: int
    relation: Optional[str]
    priority: int
    receive_sms: bool
    user: UserOut


class DeviceIn(BaseModel):
    name: str = "HealthWatch"
    serial: Optional[str] = None


class DeviceOut(ORM):
    id: int
    patient_id: int
    name: str
    serial: Optional[str]
    firmware: Optional[str]
    last_seen_at: Optional[datetime]
    last_battery: Optional[int]
    last_charging: Optional[bool]
    last_worn: Optional[bool]


class DeviceCreated(DeviceOut):
    api_key: str


# ---------------------------------------------------------------- dữ liệu từ thiết bị
class VitalIn(BaseModel):
    ts: datetime
    seq: int = 0
    hr: Optional[float] = None
    hr_quality: Optional[int] = None
    spo2: Optional[float] = None
    spo2_quality: Optional[int] = None
    skin_temp: Optional[float] = None
    activity: Optional[int] = None
    interval_s: int = 10
    battery_pct: Optional[int] = None
    battery_mv: Optional[int] = None
    worn: bool = True
    charging: bool = False
    still: bool = False


class VitalsBatch(BaseModel):
    samples: list[VitalIn]
    firmware: Optional[str] = None


class VitalOut(ORM):
    ts: datetime
    hr: Optional[float]
    hr_quality: Optional[int]
    spo2: Optional[float]
    spo2_quality: Optional[int]
    skin_temp: Optional[float]
    activity: Optional[int]
    battery_pct: Optional[int]
    worn: bool
    charging: bool


class EventIn(BaseModel):
    type: str  # fall | sos | fall_cancelled | low_battery | impact
    ts: datetime
    seq: int
    value1: Optional[float] = None
    value2: Optional[float] = None
    value3: Optional[float] = None


class EventsBatch(BaseModel):
    events: list[EventIn]


class EventOut(ORM):
    id: int
    type: str
    ts: datetime
    value1: Optional[float]
    value2: Optional[float]
    value3: Optional[float]


class EcgIn(BaseModel):
    ts: datetime
    status: int = 0
    hr: Optional[float] = None
    quality: Optional[int] = None
    n_beats: Optional[int] = None
    rr_ms: Optional[float] = None
    pat_ms: Optional[float] = None
    pat_iqr_ms: Optional[float] = None
    n_pat: Optional[int] = None
    fs: float = 256
    samples: Optional[list[int]] = None


class EcgSummary(ORM):
    id: int
    ts: datetime
    status: int
    hr: Optional[float]
    quality: Optional[int]
    n_beats: Optional[int]
    pat_ms: Optional[float]
    pat_iqr_ms: Optional[float]
    sbp_est: Optional[float]
    dbp_est: Optional[float]
    bp_method: Optional[str]
    fs: float


class EcgDetail(EcgSummary):
    rr_ms: Optional[float]
    n_pat: Optional[int]
    samples: Optional[list[int]]


class CalibrationIn(BaseModel):
    sbp_ref: float = Field(gt=50, lt=260)
    dbp_ref: float = Field(gt=30, lt=160)
    ecg_id: Optional[int] = None   # dùng PAT của lần đo ECG này...
    pat_ms: Optional[float] = None  # ...hoặc nhập PAT trực tiếp
    note: Optional[str] = None


class CalibrationOut(ORM):
    id: int
    ts: datetime
    pat_ms: float
    sbp_ref: float
    dbp_ref: float
    ecg_id: Optional[int]
    note: Optional[str]


class BpModelOut(BaseModel):
    a_sbp: float
    b_sbp: float
    a_dbp: float
    b_dbp: float
    n_points: int
    method: str


# ---------------------------------------------------------------- cảnh báo
class DeliveryOut(ORM):
    channel: str
    recipient: str
    sent_at: datetime
    success: bool
    error: Optional[str]


class AlertOut(ORM):
    id: int
    patient_id: int
    type: str
    level: str
    title: str
    message: str
    value: Optional[float]
    event_ts: Optional[datetime]
    created_at: datetime
    status: str
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    push_sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    sms_sent_at: Optional[datetime]


class AlertDetail(AlertOut):
    deliveries: list[DeliveryOut]
    patient_name: Optional[str] = None
    latency_s: dict = {}


class PatientSummary(BaseModel):
    patient: PatientOut
    latest: Optional[VitalOut]
    last_hr: Optional[float]
    last_spo2: Optional[float]
    last_spo2_at: Optional[datetime]
    last_temp: Optional[float]
    last_ecg: Optional[EcgSummary]
    devices: list[DeviceOut]
    open_alerts: int
