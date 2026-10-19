"""Vòng lặp nền: leo thang SMS (5 s), kiểm tra định kỳ (60 s), mức nền nhiệt độ (1 giờ)."""
import asyncio
import logging
import time

from .alert_engine import periodic_checks, update_temp_baselines
from .config import get_settings
from .db import SessionLocal
from .notifier import notify_new_alert, run_escalations

log = logging.getLogger("worker")


def _job(fn, *args):
    db = SessionLocal()
    try:
        return fn(db, *args)
    except Exception:  # noqa: BLE001
        log.exception("Lỗi job %s", fn.__name__)
        db.rollback()
    finally:
        db.close()


def _periodic():
    alerts = _job(periodic_checks) or []
    for a in alerts:
        notify_new_alert(a.id)


async def worker_loop(stop: asyncio.Event) -> None:
    s = get_settings()
    last_periodic = 0.0
    last_baseline = 0.0
    log.info("Worker cảnh báo đã chạy")
    while not stop.is_set():
        await asyncio.to_thread(_job, run_escalations)
        now = time.monotonic()
        if now - last_periodic >= s.periodic_check_s:
            last_periodic = now
            await asyncio.to_thread(_periodic)
        if now - last_baseline >= 3600:
            last_baseline = now
            await asyncio.to_thread(_job, update_temp_baselines)
        try:
            await asyncio.wait_for(stop.wait(), timeout=s.escalation_check_s)
        except asyncio.TimeoutError:
            pass
