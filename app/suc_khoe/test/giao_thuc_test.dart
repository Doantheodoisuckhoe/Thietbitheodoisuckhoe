import 'package:flutter_test/flutter_test.dart';
import 'package:suc_khoe/giao_thuc.dart';
import 'package:suc_khoe/xu_ly_canh_bao.dart';

List<int> hex(String s) => [
      for (final p in s.split(' ')) int.parse(p, radix: 16),
    ];

void main() {
  group('Goi So do', () {
    test('vi du trong docs/giao-thuc-ble.md', () {
      final s = SoDo.tuByte(hex('01 07 48 61 42 0E 68 10 50 00'))!;
      expect(s.dangDeo, isTrue);
      expect(s.nhipTim, 72);
      expect(s.spo2, 97);
      expect(s.nhietDo, closeTo(36.5, 1e-9));
      expect(s.pinMv, 4200);
      expect(s.pinPhanTram, 80);
      expect(s.canhBaoCho, 0);
    });

    test('chua deo: khong co nhip tim, SpO2, nhiet do', () {
      final s = SoDo.tuByte(hex('01 08 00 00 00 00 10 0F 22 03'))!;
      expect(s.dangDeo, isFalse);
      expect(s.nhipTim, isNull);
      expect(s.spo2, isNull);
      expect(s.nhietDo, isNull);
      expect(s.canhBaoCho, 3);
    });

    test('nhiet do am doc dung dau', () {
      final s = SoDo.tuByte(hex('01 02 00 00 18 FC 00 00 00 00'))!; // -1000 = -10,00 C
      expect(s.nhietDo, closeTo(-10.0, 1e-9));
    });

    test('sai do dai hoac phien ban thi bo', () {
      expect(SoDo.tuByte(hex('01 07 48')), isNull);
      expect(SoDo.tuByte(hex('02 07 48 61 42 0E 68 10 50 00')), isNull);
    });
  });

  group('Goi Canh bao', () {
    test('doc ma, so thu tu, gia tri', () {
      final c = CanhBao.tuByte(hex('03 05 87 00'))!;
      expect(c.loai, LoaiCanhBao.nhipTimCao);
      expect(c.soThuTu, 5);
      expect(c.giaTri, 135);
      expect(c.moTaGiaTri, '135 lan/phut');
    });

    test('ma 0 la khong co canh bao', () {
      expect(CanhBao.tuByte(hex('00 00 00 00')), isNull);
      expect(CanhBao.tuByte(hex('09 01 00 00')), isNull);
    });

    test('sot hien 1 chu so le', () {
      expect(CanhBao.tuByte(hex('06 01 D4 0E'))!.moTaGiaTri, '38.0 do C');
    });
  });

  test('lenh xac nhan', () {
    expect(lenhXacNhan(7), [1, 7]);
    expect(lenhTimDongHo, [2]);
  });

  test('lenh dat gio: giay tu 1/1/2000 theo gio dia phuong', () {
    expect(lenhDatGio(DateTime(2000, 1, 1, 0, 1, 5)), [5, 65, 0, 0, 0]);
    // 30/10/2026 12:34:56 = 846 678 896 giay = 0x3277_4B70
    expect(lenhDatGio(DateTime(2026, 10, 30, 12, 34, 56)), [5, 0x70, 0x4B, 0x77, 0x32]);
  });

  group('Noi dung SMS', () {
    final luc = DateTime(2026, 10, 21, 14, 32);
    test('te nga co vi tri, bo dau ten', () {
      final s = noiDungSms(
        canhBao: const CanhBao(LoaiCanhBao.teNga, 1, 0),
        tenNguoiDeo: 'Bà Nguyễn Thị Hằng',
        luc: luc,
        viDo: 21.0285,
        kinhDo: 105.8542,
      );
      expect(s,
          '[Dong ho suc khoe] Ba Nguyen Thi Hang: TE NGA luc 14:32 21/10. Vi tri: https://maps.google.com/?q=21.02850,105.85420');
      expect(s.length, lessThanOrEqualTo(160));
      expect(s.codeUnits.every((c) => c < 128), isTrue);
    });

    test('khong co vi tri', () {
      final s = noiDungSms(
        canhBao: const CanhBao(LoaiCanhBao.spo2Thap, 2, 88),
        tenNguoiDeo: '',
        luc: luc,
      );
      expect(s, '[Dong ho suc khoe] Nguoi than: SPO2 THAP (SpO2 88%) luc 14:32 21/10. Khong lay duoc vi tri.');
    });

    test('bang bo dau day du', () {
      expect(boDau('Đặng Ưng Ỷ Ốc ồ ữ'), 'Dang Ung Y Oc o u');
    });
  });

  group('Xu ly canh bao', () {
    late List<(String, String)> tin;
    late List<List<int>> lenh;
    late bool smsThanhCong;
    late List<NguoiThan> danhBa;
    late DateTime now;
    late XuLyCanhBao xl;

    setUp(() {
      tin = [];
      lenh = [];
      smsThanhCong = true;
      danhBa = const [NguoiThan('Con trai', '0901234567'), NguoiThan('Con gai', '0912345678')];
      now = DateTime(2026, 10, 25, 9, 0);
      xl = XuLyCanhBao(
        guiSms: (so, nd) async {
          tin.add((so, nd));
          return smsThanhCong;
        },
        layViTri: () async => (21.0, 105.8),
        guiLenh: (l) async => lenh.add(l),
        danhBa: () => danhBa,
        tenNguoiDeo: () => 'Ong Minh',
        bayGio: () => now,
      );
    });

    test('gui SMS cho tung nguoi than roi xac nhan', () async {
      final kq = await xl.nhan(const CanhBao(LoaiCanhBao.sos, 1, 0));
      expect(tin.map((t) => t.$1), ['0901234567', '0912345678']);
      expect(kq!.soTinDaGui, 2);
      expect(lenh, [
        [1, 1]
      ]);
    });

    test('goi gui lai khong gui SMS lan 2 nhung van xac nhan', () async {
      await xl.nhan(const CanhBao(LoaiCanhBao.sos, 1, 0));
      final kq = await xl.nhan(const CanhBao(LoaiCanhBao.sos, 1, 0));
      expect(kq, isNull);
      expect(tin.length, 2);
      expect(lenh.length, 2);
    });

    test('SMS loi thi khong xac nhan, lan sau thu lai', () async {
      smsThanhCong = false;
      final kq = await xl.nhan(const CanhBao(LoaiCanhBao.teNga, 3, 0));
      expect(kq!.soTinDaGui, 0);
      expect(lenh, isEmpty);
      smsThanhCong = true;
      await xl.nhan(const CanhBao(LoaiCanhBao.teNga, 3, 0));
      expect(lenh, [
        [1, 3]
      ]);
    });

    test('chua co danh ba thi khong xac nhan', () async {
      danhBa = [];
      final kq = await xl.nhan(const CanhBao(LoaiCanhBao.sos, 1, 0));
      expect(kq!.soNguoiThan, 0);
      expect(lenh, isEmpty);
    });

    test('sau 10 phut cung so thu tu la canh bao moi (dong ho khoi dong lai)', () async {
      await xl.nhan(const CanhBao(LoaiCanhBao.sos, 1, 0));
      now = now.add(const Duration(minutes: 11));
      final kq = await xl.nhan(const CanhBao(LoaiCanhBao.sos, 1, 0));
      expect(kq, isNotNull);
      expect(tin.length, 4);
    });
  });
}
