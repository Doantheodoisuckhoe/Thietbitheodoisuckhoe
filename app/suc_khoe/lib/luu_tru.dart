// Luu danh ba nguoi than, ten nguoi deo va lich su canh bao tren dien thoai (shared_preferences).
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'xu_ly_canh_bao.dart';

class MucLichSu {
  final DateTime luc;
  final String loai;
  final String chiTiet;
  final bool khanCap;
  const MucLichSu(this.luc, this.loai, this.chiTiet, this.khanCap);

  Map<String, Object> toJson() =>
      {'luc': luc.toIso8601String(), 'loai': loai, 'chiTiet': chiTiet, 'khanCap': khanCap};
  factory MucLichSu.fromJson(Map<String, dynamic> j) => MucLichSu(
        DateTime.tryParse(j['luc'] as String? ?? '') ?? DateTime.now(),
        j['loai'] as String? ?? '',
        j['chiTiet'] as String? ?? '',
        j['khanCap'] as bool? ?? false,
      );
}

class LuuTru extends ChangeNotifier {
  static const _kDanhBa = 'danh_ba', _kTen = 'ten_nguoi_deo', _kLichSu = 'lich_su';
  static const soMucToiDa = 100;

  late SharedPreferences _p;
  List<NguoiThan> danhBa = [];
  String tenNguoiDeo = '';
  List<MucLichSu> lichSu = [];

  Future<void> tai() async {
    _p = await SharedPreferences.getInstance();
    danhBa = _docDs(_kDanhBa).map(NguoiThan.fromJson).toList();
    tenNguoiDeo = _p.getString(_kTen) ?? '';
    lichSu = _docDs(_kLichSu).map(MucLichSu.fromJson).toList();
    notifyListeners();
  }

  List<Map<String, dynamic>> _docDs(String k) {
    try {
      return (jsonDecode(_p.getString(k) ?? '[]') as List).cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }

  Future<void> themNguoiThan(NguoiThan n) async {
    danhBa = [...danhBa, n];
    await _p.setString(_kDanhBa, jsonEncode(danhBa.map((e) => e.toJson()).toList()));
    notifyListeners();
  }

  Future<void> xoaNguoiThan(int i) async {
    danhBa = [...danhBa]..removeAt(i);
    await _p.setString(_kDanhBa, jsonEncode(danhBa.map((e) => e.toJson()).toList()));
    notifyListeners();
  }

  Future<void> datTen(String ten) async {
    tenNguoiDeo = ten;
    await _p.setString(_kTen, ten);
    notifyListeners();
  }

  Future<void> ghiLichSu(MucLichSu m) async {
    lichSu = [m, ...lichSu].take(soMucToiDa).toList();
    await _p.setString(_kLichSu, jsonEncode(lichSu.map((e) => e.toJson()).toList()));
    notifyListeners();
  }
}
