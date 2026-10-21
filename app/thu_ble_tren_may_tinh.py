"""Thu dong ho qua BLE bang may tinh (thay cho app khi app chua xong).

Cai: pip install bleak
Chay: python thu_ble_tren_may_tinh.py
In so do moi giay, in canh bao va tu gui lenh xac nhan giong app that (chi khong gui SMS).
Giao thuc: docs/giao-thuc-ble.md
"""
import asyncio
import struct
from datetime import datetime

from bleak import BleakClient, BleakScanner

TEN = "DoAn-SucKhoe"
UUID_DICH_VU = "4b3a0001-8f6e-4c2a-9d1b-3e5f7a9c0b1d"
UUID_SO_DO = "4b3a0002-8f6e-4c2a-9d1b-3e5f7a9c0b1d"
UUID_CANH_BAO = "4b3a0003-8f6e-4c2a-9d1b-3e5f7a9c0b1d"
UUID_LENH = "4b3a0004-8f6e-4c2a-9d1b-3e5f7a9c0b1d"

TEN_CANH_BAO = {1: "SOS", 2: "TE NGA", 3: "NHIP TIM CAO", 4: "NHIP TIM THAP", 5: "SPO2 THAP", 6: "SOT"}


def doc_so_do(du_lieu: bytes) -> dict:
    phien_ban, co, nhip, spo2, nhiet, pin_mv, pin_pt, cho = struct.unpack("<BBBBhHBB", du_lieu)
    return {
        "dang_deo": bool(co & 1),
        "nhip_tim": nhip or None,
        "spo2": spo2 if co & 4 else None,
        "nhiet_do": nhiet / 100 if co & 2 else None,
        "pin_mv": pin_mv,
        "pin_phan_tram": pin_pt,
        "canh_bao_cho": cho,
    }


def doc_canh_bao(du_lieu: bytes) -> tuple:
    ma, so_thu_tu, gia_tri = struct.unpack("<BBH", du_lieu)
    return ma, so_thu_tu, gia_tri


async def main():
    print(f"Dang tim {TEN}...")
    thiet_bi = await BleakScanner.find_device_by_filter(
        lambda d, adv: d.name == TEN or UUID_DICH_VU in adv.service_uuids, timeout=15)
    if thiet_bi is None:
        print("Khong thay dong ho. Kiem tra dong ho da bat, va dien thoai khong dang ket noi voi no.")
        return

    async with BleakClient(thiet_bi) as client:
        print(f"Da ket noi {thiet_bi.address}")
        da_xu_ly = set()

        def khi_co_so_do(_, du_lieu: bytearray):
            s = doc_so_do(bytes(du_lieu))
            print(f"{datetime.now():%H:%M:%S}  {s}")

        async def xu_ly_canh_bao(du_lieu: bytes):
            ma, so, gia_tri = doc_canh_bao(du_lieu)
            if ma == 0 or so in da_xu_ly:
                return  # khong co canh bao, hoac goi gui lai cua canh bao da xu ly
            da_xu_ly.add(so)
            print(f"\n!!! CANH BAO {TEN_CANH_BAO.get(ma, ma)} (so {so}, gia tri {gia_tri})")
            print("    App that se gui SMS cho nguoi than o buoc nay.")
            await client.write_gatt_char(UUID_LENH, bytes([1, so]), response=True)
            print("    Da gui xac nhan, dong ho se rung dai 1 giay.\n")

        def khi_co_canh_bao(_, du_lieu: bytearray):
            asyncio.ensure_future(xu_ly_canh_bao(bytes(du_lieu)))

        await client.start_notify(UUID_SO_DO, khi_co_so_do)
        await client.start_notify(UUID_CANH_BAO, khi_co_canh_bao)
        await xu_ly_canh_bao(bytes(await client.read_gatt_char(UUID_CANH_BAO)))  # canh bao cho tu truoc
        print("Dang nhan du lieu. Giu nut SOS 1 giay de thu canh bao. Ctrl+C de thoat.\n")
        while client.is_connected:
            await asyncio.sleep(1)
        print("Mat ket noi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
