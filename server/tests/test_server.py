"""Kiểm thử server:  cd server && python -m pytest -q"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.alert_engine import periodic_checks, update_temp_baselines
from app.db import utcnow
from app.models import Alert, AlertDelivery, Device, VitalSample
from app.notifier import run_escalations, strip_accents

from .conftest import register

T0 = (int(utcnow().timestamp()) - 3600) // 60 * 60  # căn đầu phút để số khung gộp cố định


def vitals(client, dh, rows):
    r = client.post("/api/ingest/vitals", json={"samples": rows}, headers=dh)
    assert r.status_code == 200, r.text
    return r.json()


def v(ts, **kw):
    base = {"ts": ts, "seq": ts % 65536, "hr": 72, "hr_quality": 90, "skin_temp": 33.0, "activity": 0,
            "interval_s": 10, "battery_pct": 80, "worn": True}
    base.update(kw)
    return base


def alerts_of(client, h, pid):
    return client.get(f"/api/alerts?patient_id={pid}", headers=h).json()


# ---------------------------------------------------------------- tài khoản & quyền
def test_auth_and_roles(client):
    h1 = register(client)
    assert client.get("/api/auth/me", headers=h1).json()["role"] == "admin"
    h2 = register(client, "khac@example.com")
    assert client.get("/api/auth/me", headers=h2).json()["role"] == "caregiver"
    r = client.post("/api/auth/login", data={"username": "nguoinha@example.com", "password": "matkhau123"})
    assert r.status_code == 200
    assert client.post("/api/auth/login", data={"username": "nguoinha@example.com", "password": "sai"}).status_code == 401
    pid = client.post("/api/patients", json={"full_name": "Ông B"}, headers=h2).json()["id"]
    h3 = register(client, "nguoila@example.com")
    assert client.get(f"/api/patients/{pid}", headers=h3).status_code == 404
    assert client.get(f"/api/patients/{pid}", headers=h1).status_code == 200  # admin xem được


def test_bad_device_key(client, setup):
    r = client.post("/api/ingest/vitals", json={"samples": []}, headers={"X-Device-Key": "hw_sai"})
    assert r.status_code == 401


def test_thresholds_defaults_and_validation(client, setup):
    h, pid, _ = setup
    th = client.get(f"/api/patients/{pid}/thresholds", headers=h).json()
    assert (th["spo2_warning"], th["spo2_danger"], th["hr_low"], th["hr_high"]) == (94, 90, 50, 120)
    th["spo2_danger"] = 95
    assert client.put(f"/api/patients/{pid}/thresholds", json=th, headers=h).status_code == 422
    th["spo2_danger"] = 88
    assert client.put(f"/api/patients/{pid}/thresholds", json=th, headers=h).json()["spo2_danger"] == 88


# ---------------------------------------------------------------- dữ liệu & SpO2
def test_normal_vitals_no_alert_and_dedupe(client, setup):
    h, pid, dh = setup
    rows = [v(T0 + 10 * i) for i in range(30)]
    assert vitals(client, dh, rows)["accepted"] == 30
    assert vitals(client, dh, rows)["duplicates"] == 30
    assert alerts_of(client, h, pid) == []
    s = client.get(f"/api/patients/{pid}", headers=h).json()
    assert s["last_hr"] == 72 and s["devices"][0]["last_battery"] == 80
    assert len(client.get(f"/api/patients/{pid}/vitals?bucket_s=60&start=2000-01-01T00:00:00Z",
                          headers=h).json()) == 5


def test_spo2_requires_consecutive_then_escalates_level(client, setup):
    h, pid, dh = setup
    vitals(client, dh, [v(T0, spo2=92, spo2_quality=80)])
    assert alerts_of(client, h, pid) == []  # 1 lần thấp chưa đủ
    r = vitals(client, dh, [v(T0 + 120, spo2=91, spo2_quality=80)])
    a = alerts_of(client, h, pid)
    assert len(a) == 1 and a[0]["level"] == "warning" and a[0]["type"] == "spo2_low"
    vitals(client, dh, [v(T0 + 240, spo2=91, spo2_quality=80)])
    assert len(alerts_of(client, h, pid)) == 1  # cooldown: không lặp
    vitals(client, dh, [v(T0 + 360, spo2=89, spo2_quality=80)])
    vitals(client, dh, [v(T0 + 480, spo2=88, spo2_quality=80)])
    a = alerts_of(client, h, pid)
    assert [x["level"] for x in a] == ["danger", "warning"]
    assert r["alerts"]


def test_low_quality_spo2_ignored(client, setup):
    h, pid, dh = setup
    vitals(client, dh, [v(T0, spo2=85, spo2_quality=10), v(T0 + 10, spo2=84, spo2_quality=10)])
    assert alerts_of(client, h, pid) == []


# ---------------------------------------------------------------- nhịp tim
def test_hr_sustained_at_rest(client, setup):
    h, pid, dh = setup
    vitals(client, dh, [v(T0 + 10 * i, hr=130) for i in range(15)])  # 2,5 phút: chưa đủ
    assert alerts_of(client, h, pid) == []
    vitals(client, dh, [v(T0 + 10 * i, hr=130) for i in range(15, 31)])
    a = alerts_of(client, h, pid)
    assert len(a) == 1 and a[0]["type"] == "hr_abnormal" and a[0]["level"] == "warning"


def test_hr_while_moving_is_ignored(client, setup):
    h, pid, dh = setup
    vitals(client, dh, [v(T0 + 10 * i, hr=130, activity=600) for i in range(31)])
    assert alerts_of(client, h, pid) == []


def test_hr_with_low_spo2_is_danger(client, setup):
    h, pid, dh = setup
    vitals(client, dh, [v(T0 + 10 * i, hr=45, spo2=(92 if i in (3, 15) else None), spo2_quality=80)
                        for i in range(31)])
    types = {(x["type"], x["level"]) for x in alerts_of(client, h, pid)}
    assert ("hr_abnormal", "danger") in types


# ---------------------------------------------------------------- té ngã, SOS, push/SMS
def test_fall_event_creates_danger_and_sms_without_push_token(client, setup, db):
    h, pid, dh = setup
    ev = {"type": "fall", "ts": T0, "seq": 7, "value1": 4.2, "value2": 80}
    r = client.post("/api/ingest/events", json={"events": [ev]}, headers=dh).json()
    assert r["accepted"] == 1 and len(r["alerts"]) == 1
    r2 = client.post("/api/ingest/events", json={"events": [ev]}, headers=dh).json()
    assert r2["duplicates"] == 1 and r2["alerts"] == []
    a = client.get(f"/api/alerts/{r['alerts'][0]}", headers=h).json()
    assert a["level"] == "danger" and a["type"] == "fall"
    # chưa có app nào đăng ký push -> SMS gửi ngay
    assert a["sms_sent_at"] is not None
    assert [d["channel"] for d in a["deliveries"]] == ["sms"]
    assert a["deliveries"][0]["recipient"] == "+84900000001"


def test_push_then_escalate_to_sms(client, setup, db):
    h, pid, dh = setup
    client.post("/api/auth/push-token", json={"token": "fcm-token-abc"}, headers=h)
    r = client.post("/api/ingest/events", json={"events": [{"type": "sos", "ts": T0, "seq": 1}]}, headers=dh).json()
    aid = r["alerts"][0]
    a = client.get(f"/api/alerts/{aid}", headers=h).json()
    assert a["push_sent_at"] and a["sms_sent_at"] is None
    assert run_escalations(db) == 0  # chưa đủ 30 s
    row = db.get(Alert, aid)
    row.created_at = utcnow() - timedelta(seconds=31)
    db.commit()
    assert run_escalations(db) == 1
    chans = [d.channel for d in db.scalars(select(AlertDelivery).where(AlertDelivery.alert_id == aid))]
    assert chans == ["push", "sms"]
    assert run_escalations(db) == 0  # không gửi lặp


def test_ack_stops_escalation(client, setup, db):
    h, pid, dh = setup
    client.post("/api/auth/push-token", json={"token": "fcm-token-xyz"}, headers=h)
    aid = client.post("/api/ingest/events", json={"events": [{"type": "sos", "ts": T0, "seq": 2}]},
                      headers=dh).json()["alerts"][0]
    client.post(f"/api/alerts/{aid}/delivered", headers=h)
    assert client.post(f"/api/alerts/{aid}/ack", headers=h).json()["status"] == "acknowledged"
    db.get(Alert, aid).created_at = utcnow() - timedelta(seconds=120)
    db.commit()
    assert run_escalations(db) == 0
    lat = client.get(f"/api/alerts/{aid}", headers=h).json()["latency_s"]
    assert lat["push_delivered"] is not None and lat["sms_sent"] is None
    stats = client.get("/api/alerts/latency-stats", headers=h).json()
    assert stats["push_sent"]["n"] == 1
    # gateway thấy trạng thái đã xác nhận
    g = client.get("/api/ingest/alerts", headers=dh).json()
    assert g[0]["status"] == "acknowledged"


def test_fall_cancelled_and_impact_do_not_alert(client, setup):
    h, pid, dh = setup
    evs = [{"type": "impact", "ts": T0, "seq": 1, "value1": 3.5}, {"type": "fall_cancelled", "ts": T0 + 5, "seq": 2}]
    client.post("/api/ingest/events", json={"events": evs}, headers=dh)
    assert alerts_of(client, h, pid) == []
    assert len(client.get(f"/api/patients/{pid}/events?start=2000-01-01T00:00:00Z", headers=h).json()) == 2


# ---------------------------------------------------------------- huyết áp
def test_bp_calibration_and_alerts(client, setup):
    h, pid, dh = setup
    r = client.post("/api/ingest/ecg", json={"ts": T0, "hr": 70, "pat_ms": 250, "samples": [1, 2, 3]},
                    headers=dh).json()
    assert r["calibrated"] is False and r["sbp_est"] is None
    cal = client.post(f"/api/patients/{pid}/bp-calibrations", json={"ecg_id": r["id"], "sbp_ref": 130,
                                                                    "dbp_ref": 80}, headers=h)
    assert cal.status_code == 201
    ecg = client.get(f"/api/ecg/{r['id']}", headers=h).json()
    assert abs(ecg["sbp_est"] - 130) < 0.1 and ecg["samples"] == [1, 2, 3]
    r2 = client.post("/api/ingest/ecg", json={"ts": T0 + 600, "pat_ms": 220}, headers=dh).json()
    assert r2["calibrated"] and r2["sbp_est"] > 130
    r3 = client.post("/api/ingest/ecg", json={"ts": T0 + 900, "pat_ms": 150}, headers=dh).json()
    assert r3["sbp_est"] >= 180 and r3["alerts"]
    assert client.get(f"/api/patients/{pid}/bp-model", headers=h).json()["method"] == "offset"


def test_bp_trend_three_days(client, setup):
    h, pid, dh = setup
    client.post(f"/api/patients/{pid}/bp-calibrations", json={"pat_ms": 250, "sbp_ref": 120, "dbp_ref": 75},
                headers=h)
    now = int(utcnow().timestamp())
    for d in (2, 1):
        client.post("/api/ingest/ecg", json={"ts": now - d * 86400, "pat_ms": 210}, headers=dh)
    assert not [a for a in alerts_of(client, h, pid) if a["type"] == "bp_trend"]
    r = client.post("/api/ingest/ecg", json={"ts": now, "pat_ms": 210}, headers=dh).json()
    assert 140 <= r["sbp_est"] < 180
    assert [a for a in alerts_of(client, h, pid) if a["type"] == "bp_trend"]


# ---------------------------------------------------------------- kiểm tra định kỳ
def _local(h, m=0):
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    return datetime(2026, 10, 14, h, m, tzinfo=tz).astimezone(timezone.utc)


def _fill(db, pid, did, start, end, **kw):
    t = start
    while t <= end:
        db.add(VitalSample(patient_id=pid, device_id=did, ts=t, seq=int(t.timestamp()) % 65536, hr=70,
                           hr_quality=90, interval_s=10, worn=True, **kw))
        t += timedelta(seconds=10)
    db.commit()


def test_inactivity_daytime(client, setup, db):
    h, pid, dh = setup
    did = db.scalar(select(Device.id))
    db.get(Device, did).last_seen_at = _local(14)
    db.commit()
    _fill(db, pid, did, _local(10, 50), _local(14), activity=0)
    assert [a.type for a in periodic_checks(db, now=_local(14))] == ["inactivity"]
    # cửa sổ lấn sang ban đêm (7h sáng - 3 giờ = 4h) -> không cảnh báo
    assert periodic_checks(db, now=_local(8)) == []


def test_inactivity_not_triggered_when_moving(client, setup, db):
    h, pid, dh = setup
    did = db.scalar(select(Device.id))
    db.get(Device, did).last_seen_at = _local(14)
    db.commit()
    _fill(db, pid, did, _local(10, 50), _local(14), activity=40)
    assert periodic_checks(db, now=_local(14)) == []


def test_device_offline_once(client, setup, db):
    h, pid, dh = setup
    vitals(client, dh, [v(T0)])
    later = utcnow() + timedelta(minutes=45)
    assert [a.type for a in periodic_checks(db, now=later)] == ["device_offline"]
    assert periodic_checks(db, now=later + timedelta(minutes=5)) == []


def test_temp_rise_against_baseline(client, setup, db):
    h, pid, dh = setup
    did = db.scalar(select(Device.id))
    now = utcnow()
    _fill(db, pid, did, now - timedelta(hours=8), now - timedelta(hours=2), skin_temp=33.0, activity=0)
    update_temp_baselines(db, now=now)
    assert client.get(f"/api/patients/{pid}", headers=h).json()["patient"]["temp_baseline"] == 33.0
    t = int((now - timedelta(minutes=31)).timestamp())
    vitals(client, dh, [v(t + 10 * i, skin_temp=34.3) for i in range(187)])
    assert [a["type"] for a in alerts_of(client, h, pid)] == ["temp_rise"]


def test_strip_accents():
    assert strip_accents("Phát hiện té ngã – Bà Đào") == "Phat hien te nga – Ba Dao"
