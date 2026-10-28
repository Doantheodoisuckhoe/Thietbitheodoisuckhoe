// Xu ly song ECG 30 giay: loc nhieu va tim dinh R de tinh nhip tim.
// Thuat toan rut gon tu Pan-Tompkins; ban Python de thu: algorithm/ecg/phan_tich_ecg.py
// File nay khong phu thuoc Flutter de chay unit test (test/ecg_test.dart).
import 'giao_thuc.dart';

/// Trung binh truot can giua, cua so [w] mau (le). O hai dau cua so tu thu nho.
List<double> trungBinhTruot(List<double> x, int w) {
  final n = x.length, h = w ~/ 2;
  final tong = List<double>.filled(n + 1, 0);
  for (var i = 0; i < n; i++) {
    tong[i + 1] = tong[i] + x[i];
  }
  final kq = List<double>.filled(n, 0);
  for (var i = 0; i < n; i++) {
    final a = i - h < 0 ? 0 : i - h;
    final b = i + h + 1 > n ? n : i + h + 1;
    kq[i] = (tong[b] - tong[a]) / (b - a);
  }
  return kq;
}

/// Loc song de hien thi va tim dinh:
/// trung binh 5 mau (20 ms) triet nhieu dien luoi 50 Hz, tru trung binh 0,6 giay de bo troi nen.
List<double> locEcg(List<int> mau) {
  final s = trungBinhTruot([for (final v in mau) v.toDouble()], 5);
  final nen = trungBinhTruot(s, 151);
  return [for (var i = 0; i < s.length; i++) s[i] - nen[i]];
}

/// Vi tri cac dinh R (chi so mau) trong song da loc [y].
List<int> timDinhR(List<double> y) {
  final n = y.length;
  if (n < tanSoEcg) return [];
  final d = List<double>.filled(n, 0);
  for (var i = 2; i < n - 2; i++) {
    final v = y[i + 2] - y[i - 2];
    d[i] = v * v;
  }
  final m = trungBinhTruot(d, 37); // tich phan cua so 150 ms
  const bo = tanSoEcg ~/ 2;
  final giua = (n > 2 * bo + 10 ? m.sublist(bo, n - bo) : [...m])..sort();
  final p98 = giua[(0.98 * (giua.length - 1)).floor()];
  if (p98 <= 0) return [];
  final nguong = 0.3 * p98;
  const tro = tanSoEcg ~/ 10; // tim R trong +-100 ms quanh dinh nang luong
  const khoangNghi = tanSoEcg * 0.25; // 2 nhip cach nhau it nhat 250 ms

  final dinh = <int>[];
  var i = 0;
  while (i < n) {
    if (m[i] <= nguong) {
      i++;
      continue;
    }
    var j = i, tot = i;
    while (j < n && m[j] > nguong) {
      if (m[j] > m[tot]) tot = j;
      j++;
    }
    final a = tot - tro < 0 ? 0 : tot - tro;
    final b = tot + tro > n ? n : tot + tro;
    var r = a;
    for (var k = a; k < b; k++) {
      if (y[k].abs() > y[r].abs()) r = k;
    }
    if (dinh.isNotEmpty && r - dinh.last < khoangNghi) {
      if (y[r].abs() > y[dinh.last].abs()) dinh[dinh.length - 1] = r;
    } else {
      dinh.add(r);
    }
    i = j;
  }
  return dinh;
}

class KetQuaEcg {
  final List<double> daLoc;
  final List<int> dinhR;
  final int? nhipTb; // lan/phut, tinh tu trung vi khoang R-R
  final int? nhipThapNhat;
  final int? nhipCaoNhat;
  const KetQuaEcg(this.daLoc, this.dinhR, this.nhipTb, this.nhipThapNhat, this.nhipCaoNhat);
}

KetQuaEcg phanTichEcg(List<int> mau) {
  final y = locEcg(mau);
  final dinh = timDinhR(y);
  final rr = <double>[
    for (var i = 0; i + 1 < dinh.length; i++) (dinh[i + 1] - dinh[i]) / tanSoEcg,
  ].where((v) => v >= 0.3 && v <= 2.0).toList()
    ..sort();
  if (rr.length < 2) return KetQuaEcg(y, dinh, null, null, null);
  return KetQuaEcg(
    y,
    dinh,
    (60 / rr[rr.length ~/ 2]).round(),
    (60 / rr.last).round(),
    (60 / rr.first).round(),
  );
}
