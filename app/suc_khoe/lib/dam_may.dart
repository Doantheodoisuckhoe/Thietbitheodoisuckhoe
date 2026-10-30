// Gui so do va canh bao len Firebase (Realtime Database) de web cho nguoi than xem.
// Dung REST API cua Firebase qua HTTP, khong can file google-services.json.
// Cau truc du lieu va luat bao mat: web/README.md
import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'ecg.dart';
import 'giao_thuc.dart';
import 'luu_tru.dart' show BanGhiEcg;
import 'xu_ly_canh_bao.dart';

class CauHinhDamMay {
  final String apiKey;
  final String dbUrl; // vd https://ten-du-an-default-rtdb.asia-southeast1.firebasedatabase.app
  final String email;
  final String refreshToken;
  final String uid;
  const CauHinhDamMay(this.apiKey, this.dbUrl, this.email, this.refreshToken, this.uid);

  bool get daDangNhap => refreshToken.isNotEmpty && uid.isNotEmpty;

  Map<String, String> toJson() =>
      {'apiKey': apiKey, 'dbUrl': dbUrl, 'email': email, 'refreshToken': refreshToken, 'uid': uid};
  factory CauHinhDamMay.fromJson(Map<String, dynamic> j) => CauHinhDamMay(
        j['apiKey'] as String? ?? '',
        j['dbUrl'] as String? ?? '',
        j['email'] as String? ?? '',
        j['refreshToken'] as String? ?? '',
        j['uid'] as String? ?? '',
      );
}

class LoiDamMay implements Exception {
  final String thongBao;
  LoiDamMay(this.thongBao);
  @override
  String toString() => thongBao;
}

String chuanHoaDbUrl(String url) {
  var u = url.trim();
  while (u.endsWith('/')) {
    u = u.substring(0, u.length - 1);
  }
  return u;
}

/// Doi ma loi Firebase sang tieng Viet de hien cho nguoi dung.
String _loiDangNhap(String ma) {
  if (ma.contains('INVALID_LOGIN_CREDENTIALS') || ma.contains('INVALID_PASSWORD') || ma.contains('EMAIL_NOT_FOUND')) {
    return 'Sai email hoặc mật khẩu';
  }
  if (ma.contains('API_KEY_INVALID') || ma.contains('API key not valid')) return 'API key sai';
  if (ma.contains('OPERATION_NOT_ALLOWED')) return 'Chưa bật đăng nhập Email/Password trong Firebase';
  if (ma.contains('TOO_MANY_ATTEMPTS')) return 'Thử sai quá nhiều lần, đợi vài phút';
  return 'Lỗi đăng nhập: $ma';
}

class DamMay {
  final http.Client _http;
  final DateTime Function() bayGio;
  CauHinhDamMay? cauHinh;
  String? _idToken;
  DateTime _hetHan = DateTime.fromMillisecondsSinceEpoch(0);

  /// Loi gan nhat (null = dang gui binh thuong), de hien tren trang Cai dat.
  String? loi;
  DateTime? lanGuiCuoi;

  // Gom so do trong 1 phut de luu lich su (1 diem/phut, 24 gio = 1440 diem).
  final List<SoDo> _trongPhut = [];
  DateTime? _phutHienTai;
  DateTime _lanGuiHienTai = DateTime.fromMillisecondsSinceEpoch(0);
  final List<Map<String, Object?>> _canhBaoCho = [];
  final List<(BanGhiEcg, KetQuaEcg)> _ecgCho = [];
  static const soEcgChoToiDa = 5; // moi lan ~20 KB, mat mang lau thi bo lan cu nhat

  DamMay({http.Client? client, DateTime Function()? bayGio})
      : _http = client ?? http.Client(),
        bayGio = bayGio ?? DateTime.now;

  bool get batDuoc => cauHinh?.daDangNhap ?? false;

  /// Dang nhap bang email/mat khau. Chi luu refreshToken, khong luu mat khau.
  Future<CauHinhDamMay> dangNhap(String apiKey, String dbUrl, String email, String matKhau) async {
    final r = await _http.post(
      Uri.parse('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${apiKey.trim()}'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email.trim(), 'password': matKhau, 'returnSecureToken': true}),
    );
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    if (r.statusCode != 200) {
      throw LoiDamMay(_loiDangNhap((j['error']?['message'] ?? r.body).toString()));
    }
    _idToken = j['idToken'] as String;
    _hetHan = bayGio().add(Duration(seconds: int.parse('${j['expiresIn'] ?? '3600'}') - 60));
    cauHinh = CauHinhDamMay(
        apiKey.trim(), chuanHoaDbUrl(dbUrl), email.trim(), j['refreshToken'] as String, j['localId'] as String);
    // Thu ghi 1 lan de bao loi sai dia chi database / sai luat ngay luc dang nhap.
    await _ghi('PUT', 'thongTin/dangNhapLuc', bayGio().millisecondsSinceEpoch);
    return cauHinh!;
  }

  void dangXuat() {
    cauHinh = null;
    _idToken = null;
  }

  Future<String> _token() async {
    final c = cauHinh!;
    if (_idToken != null && bayGio().isBefore(_hetHan)) return _idToken!;
    final r = await _http.post(
      Uri.parse('https://securetoken.googleapis.com/v1/token?key=${c.apiKey}'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'grant_type=refresh_token&refresh_token=${Uri.encodeQueryComponent(c.refreshToken)}',
    );
    if (r.statusCode != 200) throw LoiDamMay('Phiên đăng nhập hết hạn, đăng nhập lại ở trang Cài đặt');
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    _idToken = j['id_token'] as String;
    _hetHan = bayGio().add(Duration(seconds: int.parse('${j['expires_in'] ?? '3600'}') - 60));
    return _idToken!;
  }

  Future<void> _ghi(String phuongThuc, String duongDan, Object? duLieu) async {
    final c = cauHinh!;
    final url = Uri.parse('${c.dbUrl}/nguoiDung/${c.uid}/$duongDan.json?auth=${await _token()}');
    final req = http.Request(phuongThuc, url)
      ..headers['Content-Type'] = 'application/json'
      ..body = jsonEncode(duLieu);
    final r = await http.Response.fromStream(await _http.send(req));
    if (r.statusCode == 401 || r.statusCode == 403) {
      throw LoiDamMay('Firebase từ chối ghi: kiểm tra Rules của Realtime Database (web/README.md)');
    }
    if (r.statusCode == 404) throw LoiDamMay('Sai địa chỉ Realtime Database');
    if (r.statusCode != 200) throw LoiDamMay('Lỗi Firebase ${r.statusCode}: ${r.body}');
    loi = null;
    lanGuiCuoi = bayGio();
  }

  Future<void> _thu(Future<void> Function() viec) async {
    if (!batDuoc) return;
    try {
      await viec();
    } on LoiDamMay catch (e) {
      loi = e.thongBao;
    } catch (e) {
      loi = 'Không gửi được (mất mạng?): $e';
    }
  }

  Future<void> guiThongTin(String tenNguoiDeo) =>
      _thu(() => _ghi('PATCH', 'thongTin', {'tenNguoiDeo': tenNguoiDeo}));

  /// Goi moi khi co goi So do (1 lan/giay). Gui "hienTai" 10 giay/lan, lich su 1 phut/lan.
  Future<void> nhanSoDo(SoDo s, {required bool ketNoi}) async {
    if (!batDuoc) return;
    final now = bayGio();
    final phut = DateTime(now.year, now.month, now.day, now.hour, now.minute);
    final viec = <Future<void> Function()>[];

    if (_phutHienTai != null && phut != _phutHienTai && _trongPhut.isNotEmpty) {
      final diem = trungBinhPhut(_trongPhut, _phutHienTai!);
      final khoa = _khoaPhut(_phutHienTai!);
      viec.add(() => _ghi('PUT', 'soDo/$khoa', diem));
      _trongPhut.clear();
    }
    _phutHienTai = phut;
    _trongPhut.add(s);

    if (now.difference(_lanGuiHienTai) >= const Duration(seconds: 10)) {
      _lanGuiHienTai = now;
      viec.add(() => _ghi('PUT', 'hienTai', hienTaiJson(s, ketNoi: ketNoi, luc: now)));
    }
    if (_canhBaoCho.isNotEmpty) viec.add(_guiCanhBaoCho);
    if (_ecgCho.isNotEmpty) viec.add(_guiEcgCho);
    for (final v in viec) {
      await _thu(v);
    }
  }

  /// Bao web biet app mat ket noi voi dong ho.
  Future<void> baoMatKetNoi() => _thu(() => _ghi('PATCH', 'hienTai', {'ketNoi': false, 'luc': bayGio().millisecondsSinceEpoch}));

  /// Luu canh bao. Mat mang thi giu lai, gui khi co mang.
  Future<void> nhanCanhBao(KetQuaCanhBao kq) async {
    if (!batDuoc) return;
    _canhBaoCho.add(canhBaoJson(kq));
    await _thu(_guiCanhBaoCho);
  }

  Future<void> _guiCanhBaoCho() async {
    while (_canhBaoCho.isNotEmpty) {
      final cb = _canhBaoCho.first;
      // Khoa co dinh theo thoi diem -> gui lai nhieu lan cung chi ghi de 1 muc.
      await _ghi('PUT', 'canhBao/${cb['luc']}_${cb['ma']}', cb);
      _canhBaoCho.removeAt(0);
    }
  }

  /// Tai 1 lan do ECG len Firebase de nguoi than / bac si xem tren web. Mat mang thi gui lai sau.
  Future<void> nhanEcg(BanGhiEcg e, KetQuaEcg k) async {
    if (!batDuoc) return;
    _ecgCho.add((e, k));
    while (_ecgCho.length > soEcgChoToiDa) {
      _ecgCho.removeAt(0);
    }
    await _thu(_guiEcgCho);
  }

  Future<void> _guiEcgCho() async {
    while (_ecgCho.isNotEmpty) {
      final (e, k) = _ecgCho.first;
      final khoa = e.luc.millisecondsSinceEpoch;
      // Ghi song truoc, tom tat sau: web chi liet ke lan do da co du song.
      await _ghi('PUT', 'ecgSong/$khoa', ecgSongJson(e, k));
      await _ghi('PUT', 'ecg/$khoa', ecgTomTatJson(e, k));
      _ecgCho.removeAt(0);
    }
  }
}

String _hai(int n) => n.toString().padLeft(2, '0');
String _khoaPhut(DateTime p) => '${p.year}${_hai(p.month)}${_hai(p.day)}${_hai(p.hour)}${_hai(p.minute)}';

Map<String, Object?> hienTaiJson(SoDo s, {required bool ketNoi, required DateTime luc}) => {
      'nhipTim': s.dangDeo ? s.nhipTim : null,
      'spo2': s.dangDeo ? s.spo2 : null,
      'nhietDo': s.dangDeo ? s.nhietDo : null,
      'pinPhanTram': s.pinPhanTram,
      'dangDeo': s.dangDeo,
      'ketNoi': ketNoi,
      'luc': luc.millisecondsSinceEpoch,
    };

/// Trung binh cac so do hop le trong 1 phut. Gia tri null neu ca phut khong co so do hop le.
Map<String, Object?> trungBinhPhut(List<SoDo> ds, DateTime phut) {
  double? tb(Iterable<num?> xs) {
    final v = xs.whereType<num>().toList();
    return v.isEmpty ? null : v.reduce((a, b) => a + b) / v.length;
  }

  final deo = ds.where((s) => s.dangDeo);
  final nhip = tb(deo.map((s) => s.nhipTim));
  final spo2 = tb(deo.map((s) => s.spo2));
  final nhiet = tb(deo.map((s) => s.nhietDo));
  return {
    'nhipTim': nhip?.round(),
    'spo2': spo2?.round(),
    'nhietDo': nhiet == null ? null : (nhiet * 10).round() / 10,
    'luc': phut.millisecondsSinceEpoch,
  };
}

Map<String, Object?> canhBaoJson(KetQuaCanhBao kq) => {
      'ma': kq.canhBao.loai.ma,
      'ten': kq.canhBao.loai.ten,
      'khanCap': kq.canhBao.loai.khanCap,
      'giaTri': kq.canhBao.giaTri,
      'moTa': kq.canhBao.moTaGiaTri,
      'soTinDaGui': kq.soTinDaGui,
      'soNguoiThan': kq.soNguoiThan,
      'viDo': kq.viTri?.$1,
      'kinhDo': kq.viTri?.$2,
      'luc': kq.luc.millisecondsSinceEpoch,
    };

/// Tom tat 1 lan do ECG (nhe) de web liet ke: /nguoiDung/{uid}/ecg/{luc}
Map<String, Object?> ecgTomTatJson(BanGhiEcg e, KetQuaEcg k) => {
      'luc': e.luc.millisecondsSinceEpoch,
      'soGiay': (e.mau.length / tanSoEcg).round(),
      'nhipTb': k.nhipTb,
      'nhipThapNhat': k.nhipThapNhat,
      'nhipCaoNhat': k.nhipCaoNhat,
      'soNhip': k.dinhR.length,
      'coTuotDienCuc': e.coTuotDienCuc,
      'soMauThieu': e.soMauThieu,
    };

/// Song goc (ADC 12 bit, uint16 little-endian, base64) va vi tri dinh R: /nguoiDung/{uid}/ecgSong/{luc}
Map<String, Object?> ecgSongJson(BanGhiEcg e, KetQuaEcg k) => {
      'luc': e.luc.millisecondsSinceEpoch,
      'tanSo': tanSoEcg,
      'mau': e.toJson()['mau'],
      'dinhR': k.dinhR,
    };
