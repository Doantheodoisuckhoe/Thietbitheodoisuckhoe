// Cac viec can quyen Android: gui SMS (code Kotlin trong MainActivity.kt), goi dien, lay GPS, xin quyen.
import 'dart:async';

import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';

const _kenh = MethodChannel('suc_khoe/dien_thoai');

/// Gui SMS truc tiep (khong mo app tin nhan), tin dai tu chia nhieu phan.
/// Tra ve true khi mang da nhan tin (chua chac nguoi nhan da doc).
Future<bool> guiSms(String so, String noiDung) async {
  if (!await Permission.sms.isGranted) return false;
  try {
    return await _kenh.invokeMethod<bool>('guiSms', {'so': so, 'noiDung': noiDung}) ?? false;
  } on PlatformException {
    return false;
  }
}

/// Goi dien truc tiep. Android chi cho mo man hinh goi khi app dang hien tren man hinh.
Future<bool> goiDien(String so) async {
  if (!await Permission.phone.isGranted) return false;
  try {
    return await _kenh.invokeMethod<bool>('goiDien', {'so': so}) ?? false;
  } on PlatformException {
    return false;
  }
}

/// Vi tri hien tai (cho toi da 15 giay), khong duoc thi lay vi tri gan nhat da biet.
Future<(double, double)?> layViTri() async {
  try {
    if (!await Geolocator.isLocationServiceEnabled()) return null;
    final quyen = await Geolocator.checkPermission();
    if (quyen == LocationPermission.denied || quyen == LocationPermission.deniedForever) return null;
    Position? p;
    try {
      p = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 15),
        ),
      );
    } on TimeoutException {
      p = await Geolocator.getLastKnownPosition();
    }
    p ??= await Geolocator.getLastKnownPosition();
    return p == null ? null : (p.latitude, p.longitude);
  } catch (_) {
    return null;
  }
}

/// Xin tat ca quyen app can. Tra ve danh sach quyen con thieu (de hien cho nguoi dung).
Future<List<String>> xinQuyen() async {
  final can = {
    Permission.bluetoothScan: 'Bluetooth (tìm đồng hồ)',
    Permission.bluetoothConnect: 'Bluetooth (kết nối)',
    Permission.locationWhenInUse: 'Vị trí (gửi kèm SMS)',
    Permission.sms: 'Gửi SMS',
    Permission.phone: 'Gọi điện',
    Permission.notification: 'Thông báo',
  };
  final kq = await can.keys.toList().request();
  return [
    for (final e in can.entries)
      if (!(kq[e.key]?.isGranted ?? false)) e.value,
  ];
}
