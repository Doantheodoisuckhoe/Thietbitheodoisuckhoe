// Dieu khien mot lan do ECG 30 giay: gui lenh cho dong ho, gom cac goi ECG, phan tich va luu.
// Tach khoi giao dien de chay unit test (test/ecg_test.dart).
import 'dart:async';

import 'package:flutter/foundation.dart';

import 'ecg.dart';
import 'giao_thuc.dart';
import 'luu_tru.dart';

enum TrangThaiEcg { chuaDo, dangDo, xong, loi }

class DoEcg extends ChangeNotifier {
  final Future<void> Function(List<int>) guiLenh;
  final Future<void> Function(BanGhiEcg) luu;
  final bool Function() coEcg; // dong ho dang ket noi va co dac tinh ECG

  DoEcg({required this.guiLenh, required this.luu, required this.coEcg});

  TrangThaiEcg trangThai = TrangThaiEcg.chuaDo;
  String? loi;
  final List<int> mau = [];
  bool dangTuot = false; // goi moi nhat bao tuot dien cuc
  bool coTuot = false; // trong ca lan do co luc tuot
  int soMauBu = 0; // mau mat goi BLE, da bu bang mau truoc do
  BanGhiEcg? banGhi;
  KetQuaEcg? ketQua;

  int? _soGoiTruoc;
  Timer? _hetGio, _choGoiDau;

  static const choPhanHoi = Duration(seconds: 4);
  static const toiDa = Duration(seconds: 45);

  double get tienDo => (mau.length / soMauEcg).clamp(0, 1).toDouble();
  int get soGiay => mau.length ~/ tanSoEcg;

  Future<void> batDau() async {
    if (trangThai == TrangThaiEcg.dangDo) return;
    if (!coEcg()) {
      _baoLoi('Chưa kết nối đồng hồ, hoặc firmware đồng hồ chưa có ECG (hãy nạp bản mới).');
      return;
    }
    mau.clear();
    dangTuot = coTuot = false;
    soMauBu = 0;
    banGhi = null;
    ketQua = null;
    loi = null;
    _soGoiTruoc = null;
    trangThai = TrangThaiEcg.dangDo;
    notifyListeners();
    _choGoiDau = Timer(choPhanHoi, () {
      if (mau.isEmpty) _baoLoi('Đồng hồ không phản hồi. Thử tắt mở lại đồng hồ hoặc nạp firmware mới.');
    });
    _hetGio = Timer(toiDa, () {
      if (trangThai != TrangThaiEcg.dangDo) return;
      // Mat goi cuoi: du 10 giay thi van phan tich phan da nhan
      if (mau.length >= 10 * tanSoEcg) {
        _xong();
      } else {
        _baoLoi('Đồng hồ gửi không đủ dữ liệu (mất kết nối hoặc sóng yếu).');
      }
    });
    await guiLenh(lenhBatDauEcg);
  }

  Future<void> dung() async {
    if (trangThai != TrangThaiEcg.dangDo) return;
    _huyHen();
    trangThai = TrangThaiEcg.chuaDo;
    notifyListeners();
    await guiLenh(lenhDungEcg);
  }

  /// Goi khi dong ho mat ket noi.
  void matKetNoi() {
    if (trangThai == TrangThaiEcg.dangDo) _baoLoi('Mất kết nối đồng hồ trong lúc đo. Hãy đo lại.');
  }

  void nhanGoi(GoiEcg g) {
    if (trangThai != TrangThaiEcg.dangDo) return;
    _choGoiDau?.cancel();
    final truoc = _soGoiTruoc;
    if (truoc != null && g.mau.isNotEmpty) {
      final mat = (g.soGoi - truoc - 1) & 0xFFFF;
      if (mat > 0 && mat < 100) {
        // Bu cho dung truc thoi gian: coi goi mat co cung so mau voi goi nay
        final bu = mat * g.mau.length;
        final cuoi = mau.isEmpty ? g.mau.first : mau.last;
        for (var i = 0; i < bu && mau.length < soMauEcg; i++) {
          mau.add(cuoi);
        }
        soMauBu += bu;
      }
    }
    _soGoiTruoc = g.soGoi;
    for (final v in g.mau) {
      if (mau.length < soMauEcg) mau.add(v);
    }
    dangTuot = g.tuotDienCuc;
    if (g.tuotDienCuc) coTuot = true;
    if (g.het || mau.length >= soMauEcg) {
      _xong();
    } else {
      notifyListeners();
    }
  }

  void _xong() {
    _huyHen();
    if (mau.length < 2 * tanSoEcg) {
      _baoLoi('Quá ít dữ liệu để tính nhịp tim.');
      return;
    }
    final thieu = (soMauEcg - mau.length) + soMauBu;
    final e = BanGhiEcg(DateTime.now(), List.of(mau), coTuot, thieu);
    banGhi = e;
    ketQua = phanTichEcg(e.mau);
    trangThai = TrangThaiEcg.xong;
    notifyListeners();
    unawaited(luu(e));
  }

  void _baoLoi(String s) {
    _huyHen();
    loi = s;
    trangThai = TrangThaiEcg.loi;
    notifyListeners();
  }

  void _huyHen() {
    _hetGio?.cancel();
    _choGoiDau?.cancel();
  }

  @override
  void dispose() {
    _huyHen();
    super.dispose();
  }
}
