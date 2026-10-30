import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:suc_khoe/dam_may.dart';
import 'package:suc_khoe/ecg.dart';
import 'package:suc_khoe/giao_thuc.dart';
import 'package:suc_khoe/luu_tru.dart';
import 'package:suc_khoe/xu_ly_canh_bao.dart';

SoDo soDo(int nhip, {bool deo = true}) => SoDo(
    dangDeo: deo, nhipTim: nhip, spo2: 97, nhietDo: 33.4, pinMv: 4000, pinPhanTram: 78, canhBaoCho: 0);

void main() {
  late List<http.Request> yeuCau;
  late int maDb;
  late DateTime now;
  late DamMay dm;

  setUp(() {
    yeuCau = [];
    maDb = 200;
    now = DateTime(2026, 10, 25, 9, 0, 5);
    dm = DamMay(
      bayGio: () => now,
      client: MockClient((r) async {
        yeuCau.add(r);
        if (r.url.host == 'identitytoolkit.googleapis.com') {
          final b = jsonDecode(r.body);
          if (b['password'] != 'dung') {
            return http.Response('{"error":{"message":"INVALID_LOGIN_CREDENTIALS"}}', 400);
          }
          return http.Response(
              '{"idToken":"tok","refreshToken":"ref","localId":"uid1","expiresIn":"3600"}', 200);
        }
        if (r.url.host == 'securetoken.googleapis.com') {
          return http.Response('{"id_token":"tok2","expires_in":"3600","user_id":"uid1"}', 200);
        }
        return http.Response('null', maDb);
      }),
    );
  });

  test('dang nhap luu uid va refresh token, thu ghi 1 lan', () async {
    final c = await dm.dangNhap(' KEY ', 'https://abc.firebasedatabase.app/', 'a@b.vn', 'dung');
    expect(c.uid, 'uid1');
    expect(c.refreshToken, 'ref');
    expect(c.dbUrl, 'https://abc.firebasedatabase.app');
    expect(yeuCau.last.url.toString(),
        'https://abc.firebasedatabase.app/nguoiDung/uid1/thongTin/dangNhapLuc.json?auth=tok');
  });

  test('sai mat khau bao loi tieng Viet', () async {
    expect(
      () => dm.dangNhap('KEY', 'https://abc', 'a@b.vn', 'sai'),
      throwsA(predicate((e) => e.toString() == 'Sai email hoặc mật khẩu')),
    );
  });

  test('chua dang nhap thi khong gui gi', () async {
    await dm.nhanSoDo(soDo(70), ketNoi: true);
    expect(yeuCau, isEmpty);
  });

  test('hienTai 10 giay/lan, lich su 1 diem/phut', () async {
    await dm.dangNhap('KEY', 'https://abc', 'a@b.vn', 'dung');
    yeuCau.clear();
    for (var i = 0; i < 60; i++) {
      await dm.nhanSoDo(soDo(i < 30 ? 60 : 80), ketNoi: true);
      now = now.add(const Duration(seconds: 1));
    }
    final hienTai = yeuCau.where((r) => r.url.path.endsWith('/hienTai.json')).toList();
    expect(hienTai.length, 6);
    expect(jsonDecode(hienTai.first.body)['nhipTim'], 60);
    final lichSu = yeuCau.where((r) => r.url.path.contains('/soDo/')).toList();
    expect(lichSu.length, 1);
    expect(lichSu.first.url.path, '/nguoiDung/uid1/soDo/202610250900.json');
    // Phut 9:00 co 55 goi (tu 9:00:05): 30 goi 60 l/p va 25 goi 80 l/p -> trung binh 69.
    expect(jsonDecode(lichSu.first.body)['nhipTim'], 69);
  });

  test('trung binh phut bo qua luc chua deo', () {
    final p = DateTime(2026, 10, 25, 9, 1);
    final d = trungBinhPhut([soDo(70), soDo(0, deo: false), soDo(80)], p);
    expect(d['nhipTim'], 75);
    expect(d['nhietDo'], 33.4);
    expect(trungBinhPhut([soDo(70, deo: false)], p)['nhipTim'], isNull);
  });

  test('canh bao mat mang thi giu lai, gui khi co mang', () async {
    await dm.dangNhap('KEY', 'https://abc', 'a@b.vn', 'dung');
    maDb = 500;
    await dm.nhanCanhBao(KetQuaCanhBao(
        const CanhBao(LoaiCanhBao.teNga, 1, 0), now, 2, 2, (21.0, 105.8), 'sms'));
    expect(dm.loi, isNotNull);
    maDb = 200;
    yeuCau.clear();
    await dm.nhanSoDo(soDo(70), ketNoi: true);
    final cb = yeuCau.where((r) => r.url.path.contains('/canhBao/')).single;
    final j = jsonDecode(cb.body);
    expect(j['ten'], 'Té ngã');
    expect(j['viDo'], 21.0);
    expect(j['soTinDaGui'], 2);
    expect(dm.loi, isNull);
  });

  test('ECG: ghi song roi tom tat, mat mang thi gui lai', () async {
    await dm.dangNhap('KEY', 'https://abc', 'a@b.vn', 'dung');
    final e = BanGhiEcg(DateTime(2026, 10, 30, 9, 5), [0, 1, 256, 4095], true, 3);
    const k = KetQuaEcg([], [1, 3], 72, 65, 80);
    maDb = 500;
    await dm.nhanEcg(e, k);
    expect(dm.loi, isNotNull);
    maDb = 200;
    yeuCau.clear();
    await dm.nhanSoDo(soDo(70), ketNoi: true);
    final khoa = e.luc.millisecondsSinceEpoch;
    final ecg = yeuCau.where((r) => r.url.path.contains('/ecg')).toList();
    expect(ecg.map((r) => r.url.path),
        ['/nguoiDung/uid1/ecgSong/$khoa.json', '/nguoiDung/uid1/ecg/$khoa.json']);
    final song = jsonDecode(ecg[0].body);
    expect(base64Decode(song['mau']), [0, 0, 1, 0, 0, 1, 0xFF, 0x0F]);
    expect(song['dinhR'], [1, 3]);
    expect(song['tanSo'], 250);
    final tt = jsonDecode(ecg[1].body);
    expect(tt['nhipTb'], 72);
    expect(tt['coTuotDienCuc'], isTrue);
    expect(tt['soMauThieu'], 3);
    // Da gui xong thi khong gui lai
    yeuCau.clear();
    await dm.nhanSoDo(soDo(70), ketNoi: true);
    expect(yeuCau.where((r) => r.url.path.contains('/ecg')), isEmpty);
  });

  test('het han token thi lam moi bang refresh token', () async {
    await dm.dangNhap('KEY', 'https://abc', 'a@b.vn', 'dung');
    now = now.add(const Duration(hours: 2));
    await dm.guiThongTin('Ba Hang');
    expect(yeuCau.any((r) => r.url.host == 'securetoken.googleapis.com'), isTrue);
    expect(yeuCau.last.url.queryParameters['auth'], 'tok2');
    expect(yeuCau.last.method, 'PATCH');
  });

  test('bi tu choi ghi bao loi Rules', () async {
    await dm.dangNhap('KEY', 'https://abc', 'a@b.vn', 'dung');
    maDb = 401;
    await dm.guiThongTin('x');
    expect(dm.loi, contains('Rules'));
  });
}
