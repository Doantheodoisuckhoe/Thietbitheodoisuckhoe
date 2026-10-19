"""Giả lập app gateway + đồng hồ gửi dữ liệu lên server (thử dashboard/cảnh báo khi chưa có phần cứng).

    python scripts/simulate_device.py --key hw_xxx                     # bình thường, 10 s/gói
    python scripts/simulate_device.py --key hw_xxx --scenario low_spo2
    python scripts/simulate_device.py --key hw_xxx --scenario fall
    python scripts/simulate_device.py --key hw_xxx --scenario tachycardia --fast
    python scripts/simulate_device.py --key hw_xxx --backfill 24       # đổ 24 giờ dữ liệu quá khứ

Kịch bản: normal | low_spo2 | tachycardia | fall | sos | ecg
"""
import argparse
import math
import random
import time

import httpx


def vital(ts, seq, hr=72.0, spo2=None, temp=33.2, activity=None, battery=80):
    return {"ts": int(ts), "seq": seq % 65536, "hr": round(hr + random.gauss(0, 1.5), 1), "hr_quality": 85,
            "spo2": spo2, "spo2_quality": 80 if spo2 else None, "skin_temp": round(temp + random.gauss(0, 0.05), 2),
            "activity": activity if activity is not None else random.choice([0, 0, 3, 20, 150]),
            "interval_s": 10, "battery_pct": battery, "worn": True, "charging": False}


def fake_ecg(fs=256, seconds=30, hr=72):
    out = []
    rr = 60 / hr
    for i in range(int(fs * seconds)):
        t = (i / fs) % rr
        v = 1200 * math.exp(-((t - 0.2) / 0.012) ** 2) + 250 * math.exp(-((t - 0.48) / 0.05) ** 2)
        out.append(int(v + random.gauss(0, 20)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--key", required=True, help="API key thiết bị (tạo trên dashboard)")
    ap.add_argument("--scenario", default="normal")
    ap.add_argument("--fast", action="store_true", help="gửi 1 gói/giây thay vì 10 s")
    ap.add_argument("--backfill", type=float, default=0, help="số giờ dữ liệu quá khứ cần đổ vào")
    args = ap.parse_args()
    c = httpx.Client(base_url=args.url, headers={"X-Device-Key": args.key}, timeout=15)
    print("Thiết bị:", c.get("/api/ingest/me").json())

    seq = random.randint(0, 1000)
    if args.backfill:
        now = time.time()
        start = now - args.backfill * 3600
        batch = []
        t = start
        while t < now:
            hour = time.localtime(t).tm_hour
            hr = 62 if hour < 6 else 75
            spo2 = random.choice([96, 97, 98]) if seq % 90 == 0 else None
            batch.append(vital(t, seq, hr=hr, spo2=spo2, temp=33.0 + 0.4 * math.sin(t / 7200)))
            seq += 1
            t += 10
            if len(batch) == 500:
                c.post("/api/ingest/vitals", json={"samples": batch}).raise_for_status()
                batch = []
        if batch:
            c.post("/api/ingest/vitals", json={"samples": batch}).raise_for_status()
        print(f"Đã đổ {args.backfill} giờ dữ liệu")
        return

    if args.scenario in ("fall", "sos"):
        r = c.post("/api/ingest/events", json={"events": [
            {"type": args.scenario, "ts": int(time.time()) - 1, "seq": seq, "value1": 4.3, "value2": 75}]})
        print(r.json())
        return
    if args.scenario == "ecg":
        r = c.post("/api/ingest/ecg", json={"ts": int(time.time()), "status": 0, "hr": 72, "quality": 95,
                                            "n_beats": 36, "rr_ms": 833, "pat_ms": 245 + random.gauss(0, 5),
                                            "pat_iqr_ms": 6, "n_pat": 34, "fs": 256, "samples": fake_ecg()})
        print(r.json())
        return

    period = 1 if args.fast else 10
    i = 0
    while True:
        hr, spo2, act = 72.0, None, None
        if args.scenario == "low_spo2" and i % 3 == 0:
            spo2 = random.choice([89, 91, 92])
        elif i % 90 == 0:
            spo2 = random.choice([96, 97, 98])
        if args.scenario == "tachycardia":
            hr, act = 128.0, 0
        r = c.post("/api/ingest/vitals", json={"samples": [vital(time.time(), seq, hr, spo2, activity=act)]})
        print(time.strftime("%H:%M:%S"), r.json())
        seq += 1
        i += 1
        time.sleep(period)


if __name__ == "__main__":
    main()
