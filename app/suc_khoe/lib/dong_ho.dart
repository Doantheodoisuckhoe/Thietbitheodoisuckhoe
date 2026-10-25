// Ket noi BLE voi dong ho, nhan So do / Canh bao, tu ket noi lai khi mat ket noi.
import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'giao_thuc.dart';

enum TrangThai { tatBluetooth, dangTim, dangKetNoi, daKetNoi, matKetNoi }

extension MoTaTrangThai on TrangThai {
  String get moTa => switch (this) {
        TrangThai.tatBluetooth => 'Bluetooth đang tắt',
        TrangThai.dangTim => 'Đang tìm đồng hồ...',
        TrangThai.dangKetNoi => 'Đang kết nối...',
        TrangThai.daKetNoi => 'Đã kết nối',
        TrangThai.matKetNoi => 'Mất kết nối, đang thử lại...',
      };
}

class DongHo extends ChangeNotifier {
  static const _khoaId = 'dong_ho_id';
  static final _guidDichVu = Guid(uuidDichVu);

  /// Ham xu ly khi co goi Canh bao (main.dart gan vao XuLyCanhBao).
  void Function(CanhBao)? khiCoCanhBao;
  void Function(SoDo)? khiCoSoDo;
  void Function()? khiMatKetNoi;

  TrangThai trangThai = TrangThai.dangTim;
  SoDo? soDo;
  String? id;
  String? loi;

  BluetoothDevice? _thietBi;
  BluetoothCharacteristic? _dtLenh;
  final List<StreamSubscription> _dangNghe = [];
  StreamSubscription? _ngheTrangThai;
  bool _dangChay = false;
  bool _dangCaiDat = false;

  void _dat(TrangThai t) {
    trangThai = t;
    notifyListeners();
  }

  Future<void> batDau() async {
    if (_dangChay) return;
    _dangChay = true;
    final prefs = await SharedPreferences.getInstance();
    id = prefs.getString(_khoaId);

    FlutterBluePlus.adapterState.listen((s) {
      if (s == BluetoothAdapterState.on) {
        if (trangThai == TrangThai.tatBluetooth) _ketNoi();
      } else if (s == BluetoothAdapterState.off) {
        _dat(TrangThai.tatBluetooth);
      }
    });
    if (FlutterBluePlus.adapterStateNow == BluetoothAdapterState.off) {
      _dat(TrangThai.tatBluetooth);
      return;
    }
    await _ketNoi();
  }

  /// Quen dong ho da luu va tim lai tu dau (khi doi dong ho khac).
  Future<void> quenDongHo() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_khoaId);
    id = null;
    await _thietBi?.disconnect();
    _thietBi = null;
    await _ketNoi();
  }

  Future<void> _ketNoi() async {
    loi = null;
    try {
      if (id == null) {
        _dat(TrangThai.dangTim);
        final tb = await _tim();
        if (tb == null) {
          loi = 'Không thấy đồng hồ. Kiểm tra đồng hồ đã bật và ở gần điện thoại.';
          _dat(TrangThai.matKetNoi);
          Future.delayed(const Duration(seconds: 5), _ketNoi);
          return;
        }
        id = tb.remoteId.str;
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_khoaId, id!);
      }
      _dat(TrangThai.dangKetNoi);
      _thietBi = BluetoothDevice.fromId(id!);
      await _ngheTrangThai?.cancel();
      _ngheTrangThai = _thietBi!.connectionState.listen(_khiDoiTrangThai);
      // autoConnect: Android tu ket noi lai moi khi dong ho vao tam, ke ca khi app chay nen.
      // License.nonprofit: do an sinh vien (truong hoc) duoc dung mien phi theo giay phep FlutterBluePlus.
      await _thietBi!.connect(license: License.nonprofit, autoConnect: true, mtu: null);
    } catch (e) {
      loi = 'Lỗi kết nối: $e';
      _dat(TrangThai.matKetNoi);
      Future.delayed(const Duration(seconds: 5), _ketNoi);
    }
  }

  Future<BluetoothDevice?> _tim() async {
    final thay = Completer<BluetoothDevice?>();
    final sub = FlutterBluePlus.onScanResults.listen((ds) {
      for (final r in ds) {
        if (!thay.isCompleted) thay.complete(r.device);
      }
    });
    await FlutterBluePlus.startScan(
      withServices: [_guidDichVu],
      withNames: const [tenDongHo],
      timeout: const Duration(seconds: 15),
    );
    // startScan co timeout tra ve ngay; doi ket qua hoac het 15 giay.
    final tb = await thay.future.timeout(const Duration(seconds: 16), onTimeout: () => null);
    await sub.cancel();
    await FlutterBluePlus.stopScan();
    return tb;
  }

  Future<void> _khiDoiTrangThai(BluetoothConnectionState s) async {
    if (s == BluetoothConnectionState.connected) {
      await _caiDatSauKhiKetNoi();
    } else if (s == BluetoothConnectionState.disconnected) {
      for (final d in _dangNghe) {
        await d.cancel();
      }
      _dangNghe.clear();
      _dtLenh = null;
      if (trangThai != TrangThai.tatBluetooth && trangThai != TrangThai.dangKetNoi) {
        _dat(TrangThai.matKetNoi);
      }
      if (soDo != null) khiMatKetNoi?.call();
    }
  }

  Future<void> _caiDatSauKhiKetNoi() async {
    if (_dangCaiDat) return;
    _dangCaiDat = true;
    try {
      final tb = _thietBi!;
      final dsDichVu = await tb.discoverServices();
      final dv = dsDichVu.where((d) => d.uuid == _guidDichVu).firstOrNull;
      if (dv == null) {
        loi = 'Thiết bị này không phải đồng hồ của đồ án (thiếu service $uuidDichVu).';
        notifyListeners();
        return;
      }
      BluetoothCharacteristic dt(String u) => dv.characteristics.firstWhere((c) => c.uuid == Guid(u));
      final dtSoDo = dt(uuidSoDo);
      final dtCanhBao = dt(uuidCanhBao);
      _dtLenh = dt(uuidLenh);

      final s1 = dtSoDo.onValueReceived.listen((b) {
        final s = SoDo.tuByte(b);
        if (s != null) {
          soDo = s;
          khiCoSoDo?.call(s);
          notifyListeners();
        }
      });
      final s2 = dtCanhBao.onValueReceived.listen((b) {
        final c = CanhBao.tuByte(b);
        if (c != null) khiCoCanhBao?.call(c);
      });
      _dangNghe.addAll([s1, s2]);
      await dtSoDo.setNotifyValue(true);
      await dtCanhBao.setNotifyValue(true);
      loi = null;
      _dat(TrangThai.daKetNoi);

      // Canh bao xay ra luc chua ket noi: doc gia tri dang cho tren dong ho.
      final c = CanhBao.tuByte(await dtCanhBao.read());
      if (c != null) khiCoCanhBao?.call(c);
    } catch (e) {
      loi = 'Lỗi đọc dữ liệu: $e';
      notifyListeners();
    } finally {
      _dangCaiDat = false;
    }
  }

  Future<void> guiLenh(List<int> lenh) async {
    final dt = _dtLenh;
    if (dt == null) return;
    try {
      await dt.write(lenh, withoutResponse: false);
    } catch (_) {
      // Mat ket noi giua chung: dong ho se gui lai canh bao, app se xac nhan lai.
    }
  }
}
