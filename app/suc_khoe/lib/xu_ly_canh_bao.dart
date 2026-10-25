// Viec app lam khi dong ho bao canh bao (docs/giao-thuc-ble.md, muc "Viec app can lam"):
// bo goi gui lai -> lay vi tri -> gui SMS cho tung nguoi than -> gui xac nhan ve dong ho.
// Khong phu thuoc Flutter: cac viec that (SMS, GPS, BLE) duoc truyen vao de unit test duoc.
import 'giao_thuc.dart';

class NguoiThan {
  final String ten;
  final String soDienThoai;
  const NguoiThan(this.ten, this.soDienThoai);

  Map<String, String> toJson() => {'ten': ten, 'so': soDienThoai};
  factory NguoiThan.fromJson(Map<String, dynamic> j) =>
      NguoiThan(j['ten'] as String? ?? '', j['so'] as String? ?? '');
}

class KetQuaCanhBao {
  final CanhBao canhBao;
  final DateTime luc;
  final int soTinDaGui;
  final int soNguoiThan;
  final (double, double)? viTri; // (vi do, kinh do)
  final String noiDung;
  const KetQuaCanhBao(
      this.canhBao, this.luc, this.soTinDaGui, this.soNguoiThan, this.viTri, this.noiDung);
  bool get coViTri => viTri != null;
}

typedef GuiSms = Future<bool> Function(String so, String noiDung);
typedef LayViTri = Future<(double, double)?> Function();
typedef GuiLenh = Future<void> Function(List<int> lenh);

class XuLyCanhBao {
  final GuiSms guiSms;
  final LayViTri layViTri;
  final GuiLenh guiLenh;
  final List<NguoiThan> Function() danhBa;
  final String Function() tenNguoiDeo;
  final DateTime Function() bayGio;

  /// Khoa canh bao da xu ly -> luc xu ly. Giu 10 phut: dong ho khoi dong lai thi dem lai tu 1,
  /// nen khong giu mai, de canh bao moi trung so thu tu van duoc gui.
  final Map<String, DateTime> _daXuLy = {};
  final Set<String> _dangXuLy = {};
  static const giuKhoa = Duration(minutes: 10);

  XuLyCanhBao({
    required this.guiSms,
    required this.layViTri,
    required this.guiLenh,
    required this.danhBa,
    required this.tenNguoiDeo,
    DateTime Function()? bayGio,
  }) : bayGio = bayGio ?? DateTime.now;

  /// Goi moi khi nhan goi Canh bao. Tra ve ket qua neu vua gui SMS, null neu bo qua.
  Future<KetQuaCanhBao?> nhan(CanhBao cb) async {
    final now = bayGio();
    _daXuLy.removeWhere((_, t) => now.difference(t) > giuKhoa);

    if (_daXuLy.containsKey(cb.khoa)) {
      // Goi gui lai: dong ho chua nhan duoc xac nhan (vd vua mat ket noi). Xac nhan lai, khong gui SMS.
      await guiLenh(lenhXacNhan(cb.soThuTu));
      return null;
    }
    if (!_dangXuLy.add(cb.khoa)) return null; // dang gui SMS cho canh bao nay

    try {
      final viTri = await layViTri();
      final noiDung = noiDungSms(
        canhBao: cb,
        tenNguoiDeo: tenNguoiDeo(),
        luc: now,
        viDo: viTri?.$1,
        kinhDo: viTri?.$2,
      );
      final ds = danhBa().where((n) => n.soDienThoai.trim().isNotEmpty).toList();
      var daGui = 0;
      for (final n in ds) {
        if (await guiSms(n.soDienThoai.trim(), noiDung)) daGui++;
      }
      // Chi xac nhan khi da gui duoc it nhat 1 tin. Chua gui duoc (chua co danh ba, het tien, mat song)
      // thi de dong ho gui lai sau 5 giay, app se thu lai.
      if (daGui > 0) {
        _daXuLy[cb.khoa] = now;
        await guiLenh(lenhXacNhan(cb.soThuTu));
      }
      return KetQuaCanhBao(cb, now, daGui, ds.length, viTri, noiDung);
    } finally {
      _dangXuLy.remove(cb.khoa);
    }
  }
}
