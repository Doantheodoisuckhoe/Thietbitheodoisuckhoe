"""Luu du lieu IMU tu XIAO (sketch firmware/ghi_imu) thanh file CSV, moi lan ghi mot file co nhan.

Cai thu vien:  pip install pyserial
Chay:          python ghi_du_lieu.py COM5
Moi lan ghi:   nhap nhan (vd: nga, di_bo, ngoi_xuong), dem nguoc 3 giay, ghi trong so giay da chon.
File luu o:    data/imu/<nhan>_<ngay-gio>.csv (tinh tu thu muc goc cua repo)
Nho dong Serial Monitor cua Arduino IDE truoc khi chay (moi luc chi mot chuong trinh mo duoc cong COM).
"""
import sys
import time
from datetime import datetime
from pathlib import Path

import serial

THU_MUC = Path(__file__).resolve().parents[2] / "data" / "imu"
TIEU_DE = "t_ms,ax,ay,az,gx,gy,gz"


def ghi_mot_lan(cong, nhan, so_giay):
    THU_MUC.mkdir(parents=True, exist_ok=True)
    ten = THU_MUC / f"{nhan}_{datetime.now():%Y%m%d_%H%M%S}.csv"
    for i in (3, 2, 1):
        print(f"  {i}...")
        time.sleep(1)
    cong.reset_input_buffer()
    print(f"  DANG GHI {so_giay} giay: thuc hien dong tac '{nhan}' ngay")
    so_dong = 0
    het_gio = time.time() + so_giay
    with open(ten, "w", newline="") as f:
        f.write(TIEU_DE + "\n")
        while time.time() < het_gio:
            dong = cong.readline().decode(errors="ignore").strip()
            if dong and dong[0].isdigit() and dong.count(",") == 6:
                f.write(dong + "\n")
                so_dong += 1
    print(f"  Xong: {so_dong} mau -> {ten}")
    if so_dong < so_giay * 80:
        print("  CANH BAO: it mau hon du kien (100 mau/giay). Kiem tra cong COM va sketch ghi_imu.")


def main():
    if len(sys.argv) < 2:
        print("Cach dung: python ghi_du_lieu.py <cong COM, vd COM5>")
        sys.exit(1)
    cong = serial.Serial(sys.argv[1], 115200, timeout=1)
    time.sleep(2)
    print(f"Da mo {sys.argv[1]}. Luu vao {THU_MUC}")
    while True:
        nhan = input("\nNhan (vd: nga, di_bo, ngoi_xuong; Enter de thoat): ").strip()
        if not nhan:
            break
        giay = input("So giay ghi [10]: ").strip()
        ghi_mot_lan(cong, nhan, int(giay) if giay else 10)
    cong.close()


if __name__ == "__main__":
    main()
