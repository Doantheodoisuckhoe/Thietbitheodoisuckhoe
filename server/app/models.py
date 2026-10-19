"""Bảng CSDL."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (JSON, Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, UTCDateTime, utcnow


class User(Base):
    """Người dùng web/app: người nhà, nhân viên y tế, quản trị."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(16), default="caregiver")  # admin | caregiver
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Patient(Base):
    """Người cao tuổi được theo dõi."""
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(16))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    temp_baseline: Mapped[Optional[float]] = mapped_column(Float)  # nhiệt độ da nền (cập nhật mỗi giờ)
    temp_baseline_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    thresholds: Mapped["Thresholds"] = relationship(back_populates="patient", uselist=False,
                                                    cascade="all, delete-orphan")
    devices: Mapped[list["Device"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    care_links: Mapped[list["CareLink"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class CareLink(Base):
    """Ai được nhận cảnh báo của bệnh nhân nào, theo thứ tự ưu tiên."""
    __tablename__ = "care_links"
    __table_args__ = (UniqueConstraint("patient_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    relation: Mapped[Optional[str]] = mapped_column(String(64))
    priority: Mapped[int] = mapped_column(Integer, default=1)
    receive_sms: Mapped[bool] = mapped_column(Boolean, default=True)

    patient: Mapped[Patient] = relationship(back_populates="care_links")
    user: Mapped[User] = relationship()


class Thresholds(Base):
    """Ngưỡng cảnh báo — mặc định theo đề cương cho người cao tuổi, chỉnh được trên web."""
    __tablename__ = "thresholds"
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    spo2_warning: Mapped[float] = mapped_column(Float, default=94)
    spo2_danger: Mapped[float] = mapped_column(Float, default=90)
    spo2_consecutive: Mapped[int] = mapped_column(Integer, default=2)
    hr_low: Mapped[float] = mapped_column(Float, default=50)
    hr_high: Mapped[float] = mapped_column(Float, default=120)
    hr_persist_s: Mapped[int] = mapped_column(Integer, default=300)
    temp_rise: Mapped[float] = mapped_column(Float, default=1.0)
    temp_persist_s: Mapped[int] = mapped_column(Integer, default=1800)
    sbp_warning: Mapped[float] = mapped_column(Float, default=140)
    sbp_danger: Mapped[float] = mapped_column(Float, default=180)
    bp_trend_days: Mapped[int] = mapped_column(Integer, default=3)
    inactivity_hours: Mapped[float] = mapped_column(Float, default=3.0)
    day_start_hour: Mapped[int] = mapped_column(Integer, default=7)
    day_end_hour: Mapped[int] = mapped_column(Integer, default=21)
    fall_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_danger_s: Mapped[int] = mapped_column(Integer, default=30)
    escalation_warning_s: Mapped[int] = mapped_column(Integer, default=300)
    cooldown_min: Mapped[int] = mapped_column(Integer, default=30)

    patient: Mapped[Patient] = relationship(back_populates="thresholds")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64), default="HealthWatch")
    serial: Mapped[Optional[str]] = mapped_column(String(64))
    api_key_prefix: Mapped[str] = mapped_column(String(16), index=True)
    api_key_hash: Mapped[str] = mapped_column(String(128))
    firmware: Mapped[Optional[str]] = mapped_column(String(32))
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    last_battery: Mapped[Optional[int]] = mapped_column(Integer)
    last_charging: Mapped[Optional[bool]] = mapped_column(Boolean)
    last_worn: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    patient: Mapped[Patient] = relationship(back_populates="devices")


class VitalSample(Base):
    """1 gói VITALS từ đồng hồ (mặc định 10 s/gói)."""
    __tablename__ = "vital_samples"
    __table_args__ = (UniqueConstraint("device_id", "ts", "seq"), Index("ix_vitals_patient_ts", "patient_id", "ts"))
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    ts: Mapped[datetime] = mapped_column(UTCDateTime)
    seq: Mapped[int] = mapped_column(Integer, default=0)
    hr: Mapped[Optional[float]] = mapped_column(Float)
    hr_quality: Mapped[Optional[int]] = mapped_column(Integer)
    spo2: Mapped[Optional[float]] = mapped_column(Float)
    spo2_quality: Mapped[Optional[int]] = mapped_column(Integer)
    skin_temp: Mapped[Optional[float]] = mapped_column(Float)
    activity: Mapped[Optional[int]] = mapped_column(Integer)
    interval_s: Mapped[int] = mapped_column(Integer, default=10)
    battery_pct: Mapped[Optional[int]] = mapped_column(Integer)
    battery_mv: Mapped[Optional[int]] = mapped_column(Integer)
    worn: Mapped[bool] = mapped_column(Boolean, default=True)
    charging: Mapped[bool] = mapped_column(Boolean, default=False)
    still: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class DeviceEvent(Base):
    """Sự kiện từ đồng hồ: té ngã, SOS, huỷ, pin yếu, va chạm."""
    __tablename__ = "device_events"
    __table_args__ = (UniqueConstraint("device_id", "seq", "ts"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(32))
    ts: Mapped[datetime] = mapped_column(UTCDateTime)
    seq: Mapped[int] = mapped_column(Integer)
    value1: Mapped[Optional[float]] = mapped_column(Float)
    value2: Mapped[Optional[float]] = mapped_column(Float)
    value3: Mapped[Optional[float]] = mapped_column(Float)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class EcgRecord(Base):
    __tablename__ = "ecg_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"))
    ts: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[int] = mapped_column(Integer, default=0)
    hr: Mapped[Optional[float]] = mapped_column(Float)
    quality: Mapped[Optional[int]] = mapped_column(Integer)
    n_beats: Mapped[Optional[int]] = mapped_column(Integer)
    rr_ms: Mapped[Optional[float]] = mapped_column(Float)
    pat_ms: Mapped[Optional[float]] = mapped_column(Float)
    pat_iqr_ms: Mapped[Optional[float]] = mapped_column(Float)
    n_pat: Mapped[Optional[int]] = mapped_column(Integer)
    fs: Mapped[float] = mapped_column(Float, default=256)
    samples: Mapped[Optional[list]] = mapped_column(JSON)
    sbp_est: Mapped[Optional[float]] = mapped_column(Float)
    dbp_est: Mapped[Optional[float]] = mapped_column(Float)
    bp_method: Mapped[Optional[str]] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class BpCalibration(Base):
    """1 điểm hiệu chuẩn: PAT đo bằng đồng hồ + huyết áp máy vòng bít cùng lúc."""
    __tablename__ = "bp_calibrations"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    ecg_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ecg_records.id", ondelete="SET NULL"))
    ts: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    pat_ms: Mapped[float] = mapped_column(Float)
    sbp_ref: Mapped[float] = mapped_column(Float)
    dbp_ref: Mapped[float] = mapped_column(Float)
    note: Mapped[Optional[str]] = mapped_column(String(255))


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    level: Mapped[str] = mapped_column(String(16))  # info | warning | danger
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    value: Mapped[Optional[float]] = mapped_column(Float)
    event_ts: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)  # thời điểm xảy ra (theo đồng hồ)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | acknowledged | resolved
    acknowledged_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    push_sent_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)  # app người nhà báo đã nhận
    sms_sent_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)

    patient: Mapped[Patient] = relationship()
    deliveries: Mapped[list["AlertDelivery"]] = relationship(cascade="all, delete-orphan",
                                                             order_by="AlertDelivery.id")


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(16))  # push | sms
    recipient: Mapped[str] = mapped_column(String(255))
    sent_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[Optional[str]] = mapped_column(Text)


class PushToken(Base):
    __tablename__ = "push_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True)
    platform: Mapped[Optional[str]] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
