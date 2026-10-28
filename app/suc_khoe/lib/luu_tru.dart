// Luu danh ba nguoi than, ten nguoi deo va lich su canh bao tren dien thoai (shared_preferences).
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'dam_may.dart';
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

/// Mot lan do ECG 30 giay luu tren dien thoai.
class BanGhiEcg {
  final DateTime luc;
  final List<int> mau; // ADC 12 bit, 250 mau/giay
  final bool coTuotDienCuc;
  final int soMauThieu;
  const BanGhiEcg(this.luc, this.mau, this.coTuotDienCuc, this.soMauThieu);

  Map<String, Object> toJson() {
    final b = <int>[]; // uint16 little-endian
    for (final v in mau) {
      b..add(v & 0xFF)..add((v >> 8) & 0xFF);
    }
    return {
      'luc': luc.toIso8601String(),
      'mau': base64Encode(b),
      'tuot': coTuotDienCuc,
      'thieu': soMauThieu,
    };
  }

  factory BanGhiEcg.fromJson(Map<String, dynamic> j) {
    final b = base64Decode(j['mau'] as String? ?? '');
    return BanGhiEcg(
      DateTime.tryParse(j['luc'] as String? ?? '') ?? DateTime.now(),
      [for (var i = 0; i + 1 < b.length; i += 2) b[i] | (b[i + 1] << 8)],
      j['tuot'] as bool? ?? false,
      j['thieu'] as int? ?? 0,
    );
  }
}

class LuuTru extends ChangeNotifier {
  static const _kDanhBa = 'danh_ba', _kTen = 'ten_nguoi_deo', _kLichSu = 'lich_su', _kDamMay = 'dam_may';
  static const _kEcg = 'ecg';
  static const soMucToiDa = 100;
  static const soEcgToiDa = 10; // moi lan ~20 KB

  late SharedPreferences _p;
  List<NguoiThan> danhBa = [];
  String tenNguoiDeo = '';
  List<MucLichSu> lichSu = [];
  CauHinhDamMay? damMay;
  List<BanGhiEcg> dsEcg = [];

  Future<void> tai() async {
    _p = await SharedPreferences.getInstance();
    danhBa = _docDs(_kDanhBa).map(NguoiThan.fromJson).toList();
    tenNguoiDeo = _p.getString(_kTen) ?? '';
    lichSu = _docDs(_kLichSu).map(MucLichSu.fromJson).toList();
    try {
      dsEcg = _docDs(_kEcg).map(BanGhiEcg.fromJson).toList();
    } catch (_) {
      dsEcg = []; // du lieu ECG hong thi bo, khong lam app khong mo duoc
    }
    try {
      final j = _p.getString(_kDamMay);
      damMay = j == null ? null : CauHinhDamMay.fromJson(jsonDecode(j) as Map<String, dynamic>);
    } catch (_) {
      damMay = null;
    }
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

  Future<void> luuEcg(BanGhiEcg e) async {
    dsEcg = [e, ...dsEcg].take(soEcgToiDa).toList();
    await _p.setString(_kEcg, jsonEncode(dsEcg.map((x) => x.toJson()).toList()));
    notifyListeners();
  }

  Future<void> xoaEcg(BanGhiEcg e) async {
    dsEcg = dsEcg.where((x) => !identical(x, e)).toList();
    await _p.setString(_kEcg, jsonEncode(dsEcg.map((x) => x.toJson()).toList()));
    notifyListeners();
  }

  Future<void> luuDamMay(CauHinhDamMay? c) async {
    damMay = c;
    if (c == null) {
      await _p.remove(_kDamMay);
    } else {
      await _p.setString(_kDamMay, jsonEncode(c.toJson()));
    }
    notifyListeners();
  }
}
