"""Thêm quyền Bluetooth/Internet và minSdk vào project Android do `flutter create` sinh ra.

    cd app
    flutter create --platforms=android --org vn.datn.healthwatch .
    python tool/setup_android.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"

PERMS = """
    <!-- HealthWatch: Bluetooth LE + mạng + thông báo -->
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:usesPermissionFlags="neverForLocation" />
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
    <uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" android:maxSdkVersion="30" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-feature android:name="android.hardware.bluetooth_le" android:required="true" />
"""


def main():
    if not MANIFEST.exists():
        sys.exit("Chưa có thư mục android/. Chạy trước: flutter create --platforms=android .")
    m = MANIFEST.read_text(encoding="utf-8")
    if "BLUETOOTH_SCAN" not in m:
        m = m.replace("<application", PERMS + "\n    <application", 1)
    if "usesCleartextTraffic" not in m:  # cho phép http:// tới server trong mạng LAN
        m = m.replace("<application", '<application\n        android:usesCleartextTraffic="true"', 1)
    MANIFEST.write_text(m, encoding="utf-8")
    print("Đã sửa", MANIFEST)

    for name in ("build.gradle.kts", "build.gradle"):
        g = ROOT / "android/app" / name
        if not g.exists():
            continue
        s = g.read_text(encoding="utf-8")
        s2 = re.sub(r"minSdk\s*=\s*[\w.]+", "minSdk = 23", s)
        s2 = re.sub(r"minSdkVersion\s+[\w.]+", "minSdkVersion 23", s2)
        g.write_text(s2, encoding="utf-8")
        print("Đã đặt minSdk = 23 trong", g)


if __name__ == "__main__":
    main()
