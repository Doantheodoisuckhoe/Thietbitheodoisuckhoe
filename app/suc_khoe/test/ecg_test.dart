import 'dart:math' as math;

import 'package:flutter_test/flutter_test.dart';
import 'package:suc_khoe/do_ecg.dart';
import 'package:suc_khoe/ecg.dart';
import 'package:suc_khoe/giao_thuc.dart';
import 'package:suc_khoe/luu_tru.dart';

/// Song ECG gia giong algorithm/ecg/phan_tich_ecg.py: P-QRS-T + troi nen 0,3 Hz + nhieu 50 Hz.
List<int> taoEcg(int bpm, {int giay = 30, bool dao = false}) {
  final r = math.Random(1);
  final t0 = 60 / bpm;
  double g(double ph, double tam, double rong) => math.exp(-math.pow((ph - tam) / rong, 2));
  final x = <int>[];
  for (var i = 0; i < giay * tanSoEcg; i++) {
    final t = i / tanSoEcg, ph = t % t0;
    var v = 0.12 * g(ph, 0.15, 0.03) - 0.1 * g(ph, 0.26, 0.008) + g(ph, 0.28, 0.01) -
        0.25 * g(ph, 0.30, 0.01) + 0.3 * g(ph, 0.5, 0.05);
    if (dao) v = -v;
    v += 0.6 * math.sin(2 * math.pi * 0.3 * t) + 0.15 * math.sin(2 * math.pi * 50 * t) +
        (r.nextDouble() - 0.5) * 0.12;
    x.add((1900 + 300 * v).round());
  }
  return x;
}

/// Dong goi giong firmware: so goi, co, n, n mau uint16 little-endian.
List<int> dongGoi(int so, List<int> mau, {bool tuot = false, bool het = false}) => [
      so & 0xFF,
      so >> 8,
      (tuot ? 1 : 0) | (het ? 2 : 0),
      mau.length,
      for (final v in mau) ...[v & 0xFF, v >> 8],
    ];

void main() {
  group('Goi ECG', () {
    test('goi 25 mau (MTU lon)', () {
      final mau = [for (var i = 0; i < 25; i++) 4000 + i * 3];
      final g = GoiEcg.tuByte(dongGoi(300, mau, tuot: true))!;
      expect(g.soGoi, 300);
      expect(g.tuotDienCuc, isTrue);
      expect(g.het, isFalse);
      expect(g.mau, mau);
    });

    test('goi 8 mau va goi rong cuoi', () {
      final g = GoiEcg.tuByte(dongGoi(7, [0, 1, 2, 4095, 2048, 5, 6, 7]))!;
      expect(g.mau, [0, 1, 2, 4095, 2048, 5, 6, 7]);
      final cuoi = GoiEcg.tuByte(dongGoi(8, [], het: true))!;
      expect(cuoi.het, isTrue);
      expect(cuoi.mau, isEmpty);
    });

    test('sai do dai thi bo', () {
      expect(GoiEcg.tuByte([1, 0, 0]), isNull);
      expect(GoiEcg.tuByte([1, 0, 0, 2, 5, 0]), isNull);
    });
  });

  group('Phan tich ECG', () {
    for (final bpm in [45, 72, 110, 150]) {
      for (final dao in [false, true]) {
        test('$bpm lan/phut${dao ? ' (dao cuc)' : ''}', () {
          final k = phanTichEcg(taoEcg(bpm, dao: dao));
          expect(k.nhipTb, closeTo(bpm, 2));
          expect(k.dinhR.length, closeTo(bpm / 2, 2)); // 30 giay
          expect(k.nhipThapNhat! <= k.nhipTb! && k.nhipTb! <= k.nhipCaoNhat!, isTrue);
        });
      }
    }

    test('song phang: khong co nhip', () {
      final k = phanTichEcg(List.filled(soMauEcg, 2000));
      expect(k.nhipTb, isNull);
    });
  });

  group('Mot lan do', () {
    late List<List<int>> lenh;
    late List<BanGhiEcg> daLuu;
    late DoEcg d;

    setUp(() {
      lenh = [];
      daLuu = [];
      d = DoEcg(
        guiLenh: (l) async => lenh.add(l),
        luu: (e) async => daLuu.add(e),
        coEcg: () => true,
      );
    });

    tearDown(() => d.dispose());

    test('nhan du 30 giay thi phan tich va luu', () async {
      await d.batDau();
      expect(lenh.single, lenhBatDauEcg);
      expect(d.trangThai, TrangThaiEcg.dangDo);
      final song = taoEcg(72);
      var so = 0;
      for (var i = 0; i < song.length; i += 25) {
        d.nhanGoi(GoiEcg.tuByte(dongGoi(so++, song.sublist(i, i + 25)))!);
      }
      expect(d.trangThai, TrangThaiEcg.xong);
      expect(d.ketQua!.nhipTb, closeTo(72, 2));
      expect(daLuu.single.mau.length, soMauEcg);
      expect(daLuu.single.soMauThieu, 0);
    });

    test('mat goi: bu mau cho dung thoi gian, bao tuot dien cuc', () async {
      await d.batDau();
      d.nhanGoi(GoiEcg.tuByte(dongGoi(0, List.filled(25, 2000)))!);
      d.nhanGoi(GoiEcg.tuByte(dongGoi(3, List.filled(25, 2100), tuot: true))!); // mat goi 1, 2
      expect(d.mau.length, 100);
      expect(d.soMauBu, 50);
      expect(d.dangTuot, isTrue);
      d.nhanGoi(GoiEcg.tuByte(dongGoi(4, List.filled(25, 2000)))!);
      expect(d.dangTuot, isFalse);
      expect(d.coTuot, isTrue);
    });

    test('dong ho khong co ECG thi bao loi, khong gui lenh', () async {
      final khong = DoEcg(guiLenh: (l) async => lenh.add(l), luu: (e) async {}, coEcg: () => false);
      await khong.batDau();
      expect(khong.trangThai, TrangThaiEcg.loi);
      expect(lenh, isEmpty);
      khong.dispose();
    });

    test('dung giua chung gui lenh dung', () async {
      await d.batDau();
      await d.dung();
      expect(lenh, [lenhBatDauEcg, lenhDungEcg]);
      expect(d.trangThai, TrangThaiEcg.chuaDo);
    });
  });

  test('ban ghi ECG luu va doc lai', () {
    final e = BanGhiEcg(DateTime(2026, 10, 28, 9, 5), [0, 1, 255, 256, 4095], true, 12);
    final l = BanGhiEcg.fromJson(e.toJson());
    expect(l.luc, e.luc);
    expect(l.mau, e.mau);
    expect(l.coTuotDienCuc, isTrue);
    expect(l.soMauThieu, 12);
  });
}
