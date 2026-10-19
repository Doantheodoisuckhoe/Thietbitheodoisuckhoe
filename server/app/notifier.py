"""Gửi cảnh báo: push (Firebase Cloud Messaging) và SMS, leo thang push -> SMS.

Luồng:
  1. Có cảnh báo mới -> gửi push NGAY cho mọi người nhà liên kết (mục tiêu < 30 s).
  2. Không ai bấm "Đã nhận" sau escalation_danger_s (30 s) / escalation_warning_s (5 phút)
     -> gửi SMS theo thứ tự ưu tiên (mục tiêu < 60 s cho mức nguy hiểm).
  3. Không gửi được push cho ai (chưa cài app / lỗi FCM) -> gửi SMS ngay.
  Cảnh báo mức "info" chỉ gửi push.
Mỗi lần gửi được ghi vào bảng alert_deliveries để đo độ trễ khi kiểm chứng.
"""
from __future__ import annotations

import logging
import unicodedata
from datetime import timedelta
from functools import lru_cache
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .alert_engine import LEVEL_LABEL, get_thresholds
from .config import get_settings
from .db import SessionLocal, utcnow
from .models import Alert, AlertDelivery, CareLink, PushToken, User

log = logging.getLogger("notifier")


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


# =============================================================================
# Nhà cung cấp push
# =============================================================================
class ConsolePush:
    name = "console"

    def send(self, tokens: list[str], title: str, body: str, data: dict) -> list[tuple[str, bool, Optional[str]]]:
        for t in tokens:
            log.warning("[PUSH -> %s…] %s | %s", t[:12], title, body)
        return [(t, True, None) for t in tokens]


class FcmPush:
    name = "fcm"

    def __init__(self, cred_path: str):
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(cred_path))

    def send(self, tokens, title, body, data):
        from firebase_admin import messaging

        msg = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in data.items()},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(channel_id="alerts", sound="default",
                                                           default_vibrate_timings=True)),
        )
        resp = messaging.send_each_for_multicast(msg)
        out = []
        for t, r in zip(tokens, resp.responses):
            err = None if r.success else f"{type(r.exception).__name__}: {r.exception}"
            out.append((t, r.success, err))
        return out


# =============================================================================
# Nhà cung cấp SMS — thêm nhà mạng Việt Nam (eSMS, SpeedSMS...) bằng cách viết
# 1 lớp có hàm send(phone, text) -> (ok, error) rồi đăng ký trong get_sms().
# =============================================================================
class ConsoleSms:
    name = "console"

    def send(self, phone: str, text: str) -> tuple[bool, Optional[str]]:
        log.warning("[SMS -> %s] %s", phone, text)
        return True, None


class TwilioSms:
    name = "twilio"

    def __init__(self, sid: str, token: str, sender: str):
        self.sid, self.token, self.sender = sid, token, sender

    def send(self, phone: str, text: str):
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json"
        try:
            r = httpx.post(url, data={"From": self.sender, "To": phone, "Body": text},
                           auth=(self.sid, self.token), timeout=15)
            if r.status_code >= 300:
                return False, f"HTTP {r.status_code}: {r.text[:200]}"
            return True, None
        except httpx.HTTPError as e:
            return False, str(e)


@lru_cache
def get_push():
    s = get_settings()
    if s.firebase_credentials:
        try:
            return FcmPush(s.firebase_credentials)
        except Exception as e:  # noqa: BLE001
            log.error("Không khởi tạo được Firebase (%s) — dùng console", e)
    return ConsolePush()


@lru_cache
def get_sms():
    s = get_settings()
    if s.sms_provider == "twilio":
        return TwilioSms(s.twilio_account_sid, s.twilio_auth_token, s.twilio_from)
    return ConsoleSms()


# =============================================================================
def _recipients(db: Session, patient_id: int) -> list[tuple[CareLink, User]]:
    rows = db.execute(select(CareLink, User).join(User, User.id == CareLink.user_id)
                      .where(CareLink.patient_id == patient_id).order_by(CareLink.priority))
    return [(c, u) for c, u in rows]


def send_push_for_alert(db: Session, alert: Alert) -> int:
    """Gửi push cho tất cả người nhà. Trả về số token gửi thành công."""
    users = [u for _, u in _recipients(db, alert.patient_id)]
    tokens = list(db.scalars(select(PushToken).where(PushToken.user_id.in_([u.id for u in users])))) if users else []
    if not tokens:
        return 0
    title = f"[{LEVEL_LABEL[alert.level]}] {alert.title} – {alert.patient.full_name}"
    data = {"alert_id": alert.id, "patient_id": alert.patient_id, "level": alert.level, "type": alert.type}
    try:
        results = get_push().send([t.token for t in tokens], title, alert.message, data)
    except Exception as e:  # noqa: BLE001
        log.exception("Lỗi gửi push")
        results = [(t.token, False, str(e)) for t in tokens]
    owner = {t.token: t for t in tokens}
    ok = 0
    for token, success, err in results:
        db.add(AlertDelivery(alert_id=alert.id, channel="push", recipient=f"user:{owner[token].user_id}",
                             success=success, error=err))
        ok += success
        if not success and err and ("NotRegistered" in err or "Unregistered" in err or "not registered" in err):
            db.delete(owner[token])  # token hết hạn
    if ok:
        alert.push_sent_at = utcnow()
    return ok


def send_sms_for_alert(db: Session, alert: Alert) -> int:
    s = get_settings()
    text = (f"{LEVEL_LABEL[alert.level].upper()}: {alert.title} - {alert.patient.full_name}. "
            f"{alert.message}. Xac nhan tai {s.public_base_url}/dashboard")
    if s.sms_ascii:
        text = strip_accents(text)
    ok = 0
    for link, user in _recipients(db, alert.patient_id):
        if not link.receive_sms or not user.phone:
            continue
        success, err = get_sms().send(user.phone, text)
        db.add(AlertDelivery(alert_id=alert.id, channel="sms", recipient=user.phone, success=success, error=err))
        ok += success
    alert.sms_sent_at = utcnow()  # đánh dấu đã leo thang (kể cả lỗi) để không gửi lặp
    return ok


def notify_new_alert(alert_id: int) -> None:
    """Chạy nền ngay sau khi tạo cảnh báo (FastAPI BackgroundTasks)."""
    db = SessionLocal()
    try:
        alert = db.get(Alert, alert_id)
        if alert is None or alert.status != "open":
            return
        sent = send_push_for_alert(db, alert)
        if sent == 0 and alert.level in ("warning", "danger") and alert.sms_sent_at is None:
            log.warning("Alert #%s: không gửi được push -> gửi SMS ngay", alert.id)
            send_sms_for_alert(db, alert)
        db.commit()
    except Exception:  # noqa: BLE001
        log.exception("notify_new_alert lỗi")
        db.rollback()
    finally:
        db.close()


def run_escalations(db: Session) -> int:
    """Leo thang sang SMS các cảnh báo chưa ai xác nhận. Gọi mỗi vài giây."""
    now = utcnow()
    count = 0
    pending = db.scalars(select(Alert).where(Alert.status == "open", Alert.level.in_(("warning", "danger")),
                                             Alert.sms_sent_at.is_(None)))
    for a in pending:
        th = get_thresholds(db, a.patient_id)
        wait = th.escalation_danger_s if a.level == "danger" else th.escalation_warning_s
        if now - a.created_at >= timedelta(seconds=wait):
            log.warning("Alert #%s chưa được xác nhận sau %ss -> SMS", a.id, wait)
            send_sms_for_alert(db, a)
            count += 1
    db.commit()
    return count
