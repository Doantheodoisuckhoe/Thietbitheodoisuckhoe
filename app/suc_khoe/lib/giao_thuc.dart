// Doc va tao goi du lieu BLE theo docs/giao-thuc-ble.md.
// File nay khong phu thuoc Flutter de chay duoc unit test (test/giao_thuc_test.dart).
import 'dart:typed_data';

const tenDongHo = 'DoAn-SucKhoe';
const uuidDichVu = '4b3a0001-8f6e-4c2a-9d1b-3e5f7a9c0b1d';
const uuidSoDo = '4b3a0002-8f6e-4c2a-9d1b-3e5f7a9c0b1d';
const uuidCanhBao = '4b3a0003-8f6e-4c2a-9d1b-3e5f7a9c0b1d';
const uuidLenh = '4b3a0004-8f6e-4c2a-9d1b-3e5f7a9c0b1d';
const uuidEcg = '4b3a0005-8f6e-4c2a-9d1b-3e5f7a9c0b1d';

/// Mot goi "So do" (10 byte, dong ho gui moi giay).
class SoDo {
  final bool dangDeo;
  final int? nhipTim; // lan/phut
  final int? spo2; // %
  final double? nhietDo; // do C
  final int pinMv;
  final int pinPhanTram;
  final int canhBaoCho; // 0 = khong co
  final DateTime luc;

  SoDo({
    required this.dangDeo,
    required this.nhipTim,
    required this.spo2,
    required this.nhietDo,
    required this.pinMv,
    required this.pinPhanTram,
    required this.canhBaoCho,
    DateTime? luc,
  }) : luc = luc ?? DateTime.now();

  /// Tra ve null neu goi sai do dai hoac sai phien ban.
  static SoDo? tuByte(List<int> b) {
    if (b.length != 10 || b[0] != 1) return null;
    final d = ByteData.sublistView(Uint8List.fromList(b));
    final co = b[1];
    return SoDo(
      dangDeo: co & 1 != 0,
      nhipTim: b[2] == 0 ? null : b[2],
      spo2: (co & 4 != 0 && b[3] != 0) ? b[3] : null,
      nhietDo: co & 2 != 0 ? d.getInt16(4, Endian.little) / 100 : null,
      pinMv: d.getUint16(6, Endian.little),
      pinPhanTram: b[8],
      canhBaoCho: b[9],
    );
  }
}

enum LoaiCanhBao {
  sos(1, 'SOS', 'SOS - NGUOI DEO BAM NUT CAU CUU', true),
  teNga(2, 'Té ngã', 'TE NGA', true),
  nhipTimCao(3, 'Nhịp tim cao', 'NHIP TIM CAO', false),
  nhipTimThap(4, 'Nhịp tim thấp', 'NHIP TIM THAP', false),
  spo2Thap(5, 'SpO2 thấp', 'SPO2 THAP', false),
  sot(6, 'Sốt', 'SOT', false);

  final int ma;
  final String ten; // hien tren app (co dau)
  final String tenSms; // trong SMS (khong dau)
  final bool khanCap;
  const LoaiCanhBao(this.ma, this.ten, this.tenSms, this.khanCap);

  static LoaiCanhBao? tuMa(int ma) {
    for (final l in values) {
      if (l.ma == ma) return l;
    }
    return null;
  }
}

/// Mot goi "Canh bao" (4 byte).
class CanhBao {
  final LoaiCanhBao loai;
  final int soThuTu;
  final int giaTri;

  const CanhBao(this.loai, this.soThuTu, this.giaTri);

  /// Tra ve null khi goi rong (ma 0 = khong co canh bao) hoac ma la.
  static CanhBao? tuByte(List<int> b) {
    if (b.length != 4) return null;
    final loai = LoaiCanhBao.tuMa(b[0]);
    if (loai == null || b[1] == 0) return null;
    return CanhBao(loai, b[1], b[2] | (b[3] << 8));
  }

  /// Gia tri doc duoc, vd "135 lan/phut". Rong voi SOS va te nga.
  String get moTaGiaTri {
    switch (loai) {
      case LoaiCanhBao.nhipTimCao:
      case LoaiCanhBao.nhipTimThap:
        return '$giaTri lan/phut';
      case LoaiCanhBao.spo2Thap:
        return 'SpO2 $giaTri%';
      case LoaiCanhBao.sot:
        return '${(giaTri / 100).toStringAsFixed(1)} do C';
      default:
        return '';
    }
  }

  /// Khoa de nhan ra goi gui lai cua cung mot canh bao.
  String get khoa => '${loai.ma}-$soThuTu';
}

List<int> lenhXacNhan(int soThuTu) => [1, soThuTu];
const lenhTimDongHo = [2];
const lenhBatDauEcg = [3];
const lenhDungEcg = [4];

/// Dat gio cho dong ho: 05 + so giay tu 1/1/2000 00:00 theo gio dia phuong (uint32 little-endian).
/// App gui moi lan ket noi; dong ho khong co pin RTC rieng nen mat nguon thi cho lan ket noi sau.
List<int> lenhDatGio(DateTime luc) {
  final giay = DateTime.utc(luc.year, luc.month, luc.day, luc.hour, luc.minute, luc.second)
      .difference(DateTime.utc(2000))
      .inSeconds;
  return [5, giay & 0xFF, (giay >> 8) & 0xFF, (giay >> 16) & 0xFF, (giay >> 24) & 0xFF];
}

/// ECG: dong ho lay mau 250 lan/giay trong 30 giay.
const tanSoEcg = 250;
const soGiayEcg = 30;
const soMauEcg = tanSoEcg * soGiayEcg;

/// Mot goi ECG: 4 byte dau (so goi uint16, co, so mau n) + n mau uint16 (ADC 12 bit).
class GoiEcg {
  final int soGoi;
  final bool tuotDienCuc; // co it nhat 1 mau trong goi bi tuot dien cuc
  final bool het; // goi cuoi cua lan do
  final List<int> mau;

  const GoiEcg(this.soGoi, this.tuotDienCuc, this.het, this.mau);

  static GoiEcg? tuByte(List<int> b) {
    if (b.length < 4) return null;
    final n = b[3];
    if (b.length != 4 + 2 * n) return null;
    return GoiEcg(
      b[0] | (b[1] << 8),
      b[2] & 1 != 0,
      b[2] & 2 != 0,
      [for (var i = 0; i < n; i++) b[4 + 2 * i] | ((b[5 + 2 * i] & 0x0F) << 8)],
    );
  }
}

String _hai(int n) => n.toString().padLeft(2, '0');

/// Noi dung SMS, viet khong dau de 1 tin chua duoc 160 ky tu.
String noiDungSms({
  required CanhBao canhBao,
  required String tenNguoiDeo,
  required DateTime luc,
  double? viDo,
  double? kinhDo,
}) {
  final ten = boDau(tenNguoiDeo.trim()).isEmpty ? 'Nguoi than' : boDau(tenNguoiDeo.trim());
  final gio = '${_hai(luc.hour)}:${_hai(luc.minute)} ${_hai(luc.day)}/${_hai(luc.month)}';
  final giaTri = canhBao.moTaGiaTri.isEmpty ? '' : ' (${canhBao.moTaGiaTri})';
  final viTri = (viDo != null && kinhDo != null)
      ? ' Vi tri: https://maps.google.com/?q=${viDo.toStringAsFixed(5)},${kinhDo.toStringAsFixed(5)}'
      : ' Khong lay duoc vi tri.';
  return '[Dong ho suc khoe] $ten: ${canhBao.loai.tenSms}$giaTri luc $gio.$viTri';
}

const _coDau = 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'
    'ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ';
const _khongDau = 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd'
    'AAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD';

String boDau(String s) {
  final kq = StringBuffer();
  for (final r in s.runes) {
    final c = String.fromCharCode(r);
    final i = _coDau.indexOf(c);
    kq.write(i >= 0 ? _khongDau[i] : c);
  }
  return kq.toString();
}
