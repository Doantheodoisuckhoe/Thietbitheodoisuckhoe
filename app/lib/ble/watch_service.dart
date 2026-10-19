import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import '../api/api_client.dart';
import '../config.dart';
import '../services/uploader.dart';
import 'protocol.dart';

/// Trạng thái 1 lần đo ECG.
class EcgSession {
  final DateTime requestedAt = DateTime.now();
  DateTime? startedAt;
  int? sessionId;
  final List<int> samples = [];
  bool leadOff = false;
  EcgResultPacket? result;
  String? error;
  bool uploading = false;
  Map<String, dynamic>? server; // kết quả server trả về (huyết áp ước lượng)

  bool get recording => startedAt != null && result == null;
  bool get done => result != null || error != null;
}

/// Quản lý kết nối BLE với đồng hồ (chế độ gateway).
class WatchService extends ChangeNotifier {
  final Uploader uploader;
  WatchService(this.uploader);

  BluetoothDevice? device;
  BluetoothConnectionState connState = BluetoothConnectionState.disconnected;
  BluetoothAdapterState adapter = BluetoothAdapterState.unknown;
  String status = 'Chưa kết nối';
  bool scanning = false;
  List<ScanResult> scanResults = [];

  VitalsPacket? lastVitals;
  DateTime? lastVitalsAt;
  int? lastSpo2;
  DateTime? lastSpo2At;
  final List<EventPacket> events = [];
  EcgSession? ecg;

  BluetoothCharacteristic? _control;
  final List<StreamSubscription> _subs = [];
  StreamSubscription? _connSub;
  bool _userDisconnect = false;
  Timer? _reconnectTimer;
  Timer? _ackTimer;
  final Set<int> _ackedAlerts = {};
  bool _ackInit = false;

  bool get connected => connState == BluetoothConnectionState.connected;

  Future<void> init() async {
    FlutterBluePlus.adapterState.listen((s) {
      adapter = s;
      notifyListeners();
      if (s == BluetoothAdapterState.on && !connected && AppConfig.watchId != null) _scheduleReconnect(0);
    });
    _ackTimer = Timer.periodic(const Duration(seconds: 15), (_) => _checkAcks());
  }

  Future<bool> _ensurePermissions() async {
    if (!Platform.isAndroid) return true;
    final res = await [Permission.bluetoothScan, Permission.bluetoothConnect, Permission.locationWhenInUse].request();
    return res[Permission.bluetoothConnect]?.isGranted ?? false;
  }

  // ---------------------------------------------------------------- quét
  Future<void> scan() async {
    if (!await _ensurePermissions()) {
      status = 'Cần cấp quyền Bluetooth';
      notifyListeners();
      return;
    }
    if (adapter != BluetoothAdapterState.on) {
      if (Platform.isAndroid) await FlutterBluePlus.turnOn();
    }
    scanResults = [];
    scanning = true;
    status = 'Đang tìm đồng hồ...';
    notifyListeners();
    final sub = FlutterBluePlus.scanResults.listen((list) {
      scanResults = list.where((r) => r.advertisementData.advName.startsWith('HealthWatch') ||
          r.advertisementData.serviceUuids.contains(kServiceUuid)).toList()
        ..sort((a, b) => b.rssi.compareTo(a.rssi));
      notifyListeners();
    });
    await FlutterBluePlus.startScan(timeout: const Duration(seconds: 8));
    await FlutterBluePlus.isScanning.where((s) => s == false).first;
    await sub.cancel();
    scanning = false;
    status = scanResults.isEmpty ? 'Không thấy đồng hồ — kiểm tra pin và để gần điện thoại' : 'Chọn đồng hồ để kết nối';
    notifyListeners();
  }

  // ---------------------------------------------------------------- kết nối
  Future<void> connect(BluetoothDevice d) async {
    _userDisconnect = false;
    _reconnectTimer?.cancel();
    await _cleanup();
    device = d;
    status = 'Đang kết nối...';
    notifyListeners();
    try {
      _connSub = d.connectionState.listen((s) {
        connState = s;
        if (s == BluetoothConnectionState.disconnected) {
          status = 'Mất kết nối — đang thử lại...';
          _control = null;
          if (ecg != null && !ecg!.done) ecg!.error = 'Mất kết nối trong lúc đo';
          if (!_userDisconnect) _scheduleReconnect(5);
        }
        notifyListeners();
      });
      await d.connect(timeout: const Duration(seconds: 15)); // Android: tự xin MTU 512
      await _setup(d);
      AppConfig.watchId = d.remoteId.str;
      status = 'Đã kết nối ${d.platformName.isEmpty ? d.remoteId.str : d.platformName}';
    } catch (e) {
      status = 'Kết nối thất bại: $e';
      if (!_userDisconnect && AppConfig.watchId != null) _scheduleReconnect(10);
    }
    notifyListeners();
  }

  Future<void> _setup(BluetoothDevice d) async {
    final services = await d.discoverServices();
    final svc = services.firstWhere((s) => s.uuid == kServiceUuid,
        orElse: () => throw Exception('Thiết bị không có dịch vụ HealthWatch'));
    BluetoothCharacteristic ch(Guid id) => svc.characteristics.firstWhere((c) => c.uuid == id);
    final vitals = ch(kVitalsUuid), event = ch(kEventUuid), ecgData = ch(kEcgDataUuid), ecgRes = ch(kEcgResultUuid);
    _control = ch(kControlUuid);

    // đăng ký lắng nghe TRƯỚC khi bật notify để không mất gói đầu
    _subs.add(vitals.onValueReceived.listen(_onVitals));
    _subs.add(event.onValueReceived.listen(_onEvent));
    _subs.add(ecgData.onValueReceived.listen(_onEcgData));
    _subs.add(ecgRes.onValueReceived.listen(_onEcgResult));
    for (final c in [vitals, event, ecgData, ecgRes]) {
      await c.setNotifyValue(true); // EVENT tự dùng indicate (đồng hồ chờ xác nhận)
    }
    await _control!.write(Cmd.setTime(DateTime.now()));
  }

  void _scheduleReconnect(int seconds) {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(seconds: seconds), () async {
      final id = AppConfig.watchId;
      if (id == null || connected || _userDisconnect || adapter != BluetoothAdapterState.on) return;
      await connect(BluetoothDevice.fromId(id));
    });
  }

  Future<void> disconnect({bool forget = false}) async {
    _userDisconnect = true;
    _reconnectTimer?.cancel();
    await device?.disconnect();
    await _cleanup();
    if (forget) AppConfig.watchId = null;
    status = 'Đã ngắt kết nối';
    notifyListeners();
  }

  Future<void> _cleanup() async {
    for (final s in _subs) {
      await s.cancel();
    }
    _subs.clear();
    await _connSub?.cancel();
    _connSub = null;
  }

  Future<void> send(List<int> cmd) async {
    if (_control == null) throw Exception('Chưa kết nối đồng hồ');
    await _control!.write(cmd);
  }

  // ---------------------------------------------------------------- dữ liệu đến
  void _onVitals(List<int> v) {
    final p = VitalsPacket.parse(v);
    if (p == null) return;
    lastVitals = p;
    lastVitalsAt = DateTime.now();
    if (p.spo2 > 0) {
      lastSpo2 = p.spo2;
      lastSpo2At = p.time.toLocal();
    }
    uploader.addVitals(p.toJson());
    notifyListeners();
  }

  void _onEvent(List<int> v) {
    final e = EventPacket.parse(v);
    if (e == null) return;
    events.insert(0, e);
    if (events.length > 50) events.removeLast();
    uploader.addEvent(e.toJson());
    notifyListeners();
  }

  void _onEcgData(List<int> v) {
    final s = ecg;
    final p = EcgDataPacket.parse(v);
    if (s == null || p == null || s.done) return;
    s.sessionId ??= p.session;
    if (p.session != s.sessionId) return;
    s.samples.addAll(p.samples);
    s.leadOff = p.leadOff;
    notifyListeners();
  }

  void _onEcgResult(List<int> v) {
    final s = ecg;
    final r = EcgResultPacket.parse(v);
    if (s == null || r == null || s.done) return;
    if (r.started) {
      s.startedAt = DateTime.now();
      s.sessionId = r.session;
      s.samples.clear();
    } else {
      s.result = r;
      if (r.status == 0 || r.status == 3) {
        _uploadEcg(s);
      } else {
        s.error = ecgStatusText[r.status] ?? 'Lỗi ${r.status}';
      }
    }
    notifyListeners();
  }

  Future<void> _uploadEcg(EcgSession s) async {
    s.uploading = true;
    notifyListeners();
    try {
      s.server = await Api.sendEcg(s.result!.toJson(s.samples));
    } catch (e) {
      s.error = 'Đo xong nhưng chưa gửi được lên server: $e';
    }
    s.uploading = false;
    notifyListeners();
  }

  Future<void> startEcg() async {
    ecg = EcgSession();
    notifyListeners();
    try {
      await send(Cmd.startEcg(30));
    } catch (e) {
      ecg!.error = e.toString();
      notifyListeners();
    }
  }

  Future<void> cancelEcg() async {
    try {
      await send(Cmd.stopEcg());
    } catch (_) {}
  }

  // ---------------------------------------------------------------- người nhà đã xác nhận -> rung đồng hồ
  Future<void> _checkAcks() async {
    if (AppConfig.mode != AppMode.gateway || AppConfig.deviceKey.isEmpty) return;
    try {
      final alerts = await Api.gatewayAlerts();
      for (final a in alerts) {
        final id = a['id'] as int;
        if (a['status'] == 'open' || _ackedAlerts.contains(id)) continue;
        _ackedAlerts.add(id);
        if (_ackInit && connected && (a['level'] == 'danger' || a['level'] == 'warning')) {
          await send(Cmd.alertAcked());
        }
      }
      _ackInit = true;
    } catch (_) {}
  }

  @override
  void dispose() {
    _ackTimer?.cancel();
    _reconnectTimer?.cancel();
    _cleanup();
    super.dispose();
  }
}
