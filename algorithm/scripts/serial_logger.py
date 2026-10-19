"""Ghi dữ liệu thô từ thiết bị qua USB (firmware bật RAW_STREAM trong config.h).

Firmware in ra các dòng:
    G,t_ms,green               PPG xanh (nhịp tim liên tục)
    S,t_ms,red,ir              PPG đỏ + IR (đo SpO2)
    E,t_ms,ecg                 ECG (AD8232, ADC 12 bit)
    P,t_ms,green               PPG trong lúc đo ECG (tính PAT)
    A,t_ms,ax_mg,ay_mg,az_mg   gia tốc
    T,t_ms,temp_c              nhiệt độ da
    #...                       dòng log

    pip install pyserial
    python scripts/serial_logger.py --port COM5 --out data/session_01
    python scripts/serial_logger.py --port /dev/ttyACM0 --out data/fall_01 --seconds 60

Nhấn Ctrl+C để dừng. Mỗi loại dữ liệu ghi ra 1 file CSV trong thư mục --out.
"""
import argparse
import os
import time

HEADERS = {
    "G": "t_ms,green",
    "S": "t_ms,red,ir",
    "E": "t_ms,ecg",
    "P": "t_ms,green",
    "A": "t_ms,ax_mg,ay_mg,az_mg",
    "T": "t_ms,temp_c",
}


def main():
    import serial  # pyserial

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=0, help="0 = chạy đến khi Ctrl+C")
    ap.add_argument("--command", default=None,
                    help="gửi lệnh khi bắt đầu, vd 'ecg' hoặc 'spo2' (firmware hỗ trợ lệnh qua USB)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    files = {}
    counts = {k: 0 for k in HEADERS}
    ser = serial.Serial(args.port, args.baud, timeout=1)
    if args.command:
        time.sleep(0.5)
        ser.write((args.command + "\n").encode())
    t0 = time.time()
    try:
        while not args.seconds or time.time() - t0 < args.seconds:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            if line.startswith("#"):
                print(line)
                continue
            kind = line[0]
            if kind not in HEADERS or len(line) < 3 or line[1] != ",":
                continue
            if kind not in files:
                f = open(os.path.join(args.out, f"{kind}.csv"), "w", encoding="utf-8")
                f.write(HEADERS[kind] + "\n")
                files[kind] = f
            files[kind].write(line[2:] + "\n")
            counts[kind] += 1
    except KeyboardInterrupt:
        pass
    finally:
        for f in files.values():
            f.close()
        ser.close()
    dur = time.time() - t0
    print(f"Đã ghi {dur:.1f} s vào {args.out}:")
    for k, c in counts.items():
        if c:
            print(f"  {k}.csv  {c} mẫu  (~{c / dur:.1f} Hz)")


if __name__ == "__main__":
    main()
