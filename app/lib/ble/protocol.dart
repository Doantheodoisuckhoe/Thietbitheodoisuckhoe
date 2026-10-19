// Giao thức BLE — PHẢI khớp với firmware/health_watch/protocol.h
// Mọi số nhiều byte là little-endian.
import 'dart:typed_data';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';

String _uuid(int x) => 'a7e1${x.toRadixString(16).padLeft(4, '0')}-4b2c-4d8e-9f10-5c3e2a1b0d47';

final Guid kServiceUuid = Guid(_uuid(0x0000));
final Guid kVitalsUuid = Guid(_uuid(0x0001));
final Guid kEventUuid = Guid(_uuid(0x0002));
final Guid kEcgDataUuid = Guid(_uuid(0x0003));
final Guid kEcgResultUuid = Guid(_uuid(0x0004));
final Guid kControlUuid = Guid(_uuid(0x0005));

const int flagWorn = 0x01;
const int flagCharging = 0x02;
const int flagStill = 0x04;
const int flagTimeSynced = 0x08;
const int flagLowBattery = 0x10;
const int tempNone = -32768;

ByteData _bd(List<int> v) => ByteData.sublistView(Uint8List.fromList(v));
const _le = Endian.little;

/// Thời điểm của gói: epoch nếu đồng hồ đã đồng bộ giờ, nếu chưa thì dùng giờ nhận.
DateTime packetTime(int timestamp, int flags) => (flags & flagTimeSynced) != 0
    ? DateTime.fromMillisecondsSinceEpoch(timestamp * 1000, isUtc: true)
    : DateTime.now().toUtc();

class VitalsPacket {
  final int flags, seq, timestamp, hr, hrQuality, spo2, spo2Quality, skinTempC100, activity, batteryPct, intervalS,
      batteryMv;

  VitalsPacket(this.flags, this.seq, this.timestamp, this.hr, this.hrQuality, this.spo2, this.spo2Quality,
      this.skinTempC100, this.activity, this.batteryPct, this.intervalS, this.batteryMv);

  static VitalsPacket? parse(List<int> v) {
    if (v.length < 20) return null;
    final b = _bd(v);
    return VitalsPacket(b.getUint8(1), b.getUint16(2, _le), b.getUint32(4, _le), b.getUint8(8), b.getUint8(9),
        b.getUint8(10), b.getUint8(11), b.getInt16(12, _le), b.getUint16(14, _le), b.getUint8(16), b.getUint8(17),
        b.getUint16(18, _le));
  }

  bool get worn => (flags & flagWorn) != 0;
  bool get charging => (flags & flagCharging) != 0;
  bool get still => (flags & flagStill) != 0;
  double? get skinTemp => skinTempC100 == tempNone ? null : skinTempC100 / 100.0;
  DateTime get time => packetTime(timestamp, flags);

  Map<String, dynamic> toJson() => {
        'ts': time.toIso8601String(),
        'seq': seq,
        'hr': hr > 0 ? hr : null,
        'hr_quality': hr > 0 ? hrQuality : null,
        'spo2': spo2 > 0 ? spo2 : null,
        'spo2_quality': spo2 > 0 ? spo2Quality : null,
        'skin_temp': skinTemp,
        'activity': activity,
        'interval_s': intervalS,
        'battery_pct': batteryPct,
        'battery_mv': batteryMv,
        'worn': worn,
        'charging': charging,
        'still': still,
      };
}

const eventNames = {1: 'fall', 2: 'sos', 3: 'fall_cancelled', 4: 'low_battery', 5: 'impact'};
const eventLabels = {
  'fall': 'Té ngã',
  'sos': 'SOS',
  'fall_cancelled': 'Đã huỷ báo té ngã',
  'low_battery': 'Pin yếu',
  'impact': 'Va chạm (đang chờ 30 s)',
};

class EventPacket {
  final int type, seq, timestamp, value1, value2, value3, flags;
  EventPacket(this.type, this.seq, this.timestamp, this.value1, this.value2, this.value3, this.flags);

  static EventPacket? parse(List<int> v) {
    if (v.length < 16) return null;
    final b = _bd(v);
    return EventPacket(b.getUint8(1), b.getUint16(2, _le), b.getUint32(4, _le), b.getInt16(8, _le),
        b.getInt16(10, _le), b.getUint16(12, _le), b.getUint8(14));
  }

  String get name => eventNames[type] ?? 'unknown';
  DateTime get time => packetTime(timestamp, flags);

  Map<String, dynamic> toJson() {
    final fall = type == 1 || type == 5;
    return {
      'type': name,
      'ts': time.toIso8601String(),
      'seq': seq,
      'value1': fall ? value1 / 100.0 : value1.toDouble(), // té ngã: g
      'value2': value2.toDouble(),
      'value3': value3.toDouble(),
    };
  }
}

class EcgDataPacket {
  final int session, flags, seq;
  final List<int> samples;
  EcgDataPacket(this.session, this.flags, this.seq, this.samples);

  static EcgDataPacket? parse(List<int> v) {
    if (v.length < 6) return null;
    final b = _bd(v);
    final count = b.getUint8(4);
    if (v.length < 6 + 2 * count) return null;
    return EcgDataPacket(
        b.getUint8(0), b.getUint8(1), b.getUint16(2, _le), [for (var i = 0; i < count; i++) b.getInt16(6 + 2 * i, _le)]);
  }

  bool get leadOff => (flags & 0x01) != 0;
}

const ecgStatusText = {
  0: 'Hoàn tất',
  1: 'Không tiếp xúc điện cực — đặt ngón tay lên mặt đồng hồ',
  2: 'Đang sạc — không đo ECG khi cắm sạc (an toàn điện)',
  3: 'Tín hiệu kém — giữ yên tay và đo lại',
  4: 'Đã huỷ',
  5: 'Lỗi cảm biến ECG',
  6: 'Đồng hồ đang bận đo chỉ số khác, thử lại sau',
  7: 'Đang ghi...',
};

class EcgResultPacket {
  final int status, session, nBeats, timestamp, hr, quality, patX10, patIqrX10, nPat, flags, fsHz, nSamples, rrMs;
  EcgResultPacket(this.status, this.session, this.nBeats, this.timestamp, this.hr, this.quality, this.patX10,
      this.patIqrX10, this.nPat, this.flags, this.fsHz, this.nSamples, this.rrMs);

  static EcgResultPacket? parse(List<int> v) {
    if (v.length < 24) return null;
    final b = _bd(v);
    return EcgResultPacket(b.getUint8(1), b.getUint8(2), b.getUint8(3), b.getUint32(4, _le), b.getUint8(8),
        b.getUint8(9), b.getUint16(10, _le), b.getUint16(12, _le), b.getUint8(14), b.getUint8(15),
        b.getUint16(16, _le), b.getUint16(18, _le), b.getUint16(20, _le));
  }

  bool get started => status == 7;
  bool get finished => status != 7;
  double? get patMs => patX10 > 0 ? patX10 / 10.0 : null;
  DateTime get time => packetTime(timestamp, flags);

  Map<String, dynamic> toJson(List<int> samples) => {
        'ts': time.toIso8601String(),
        'status': status,
        'hr': hr > 0 ? hr : null,
        'quality': quality,
        'n_beats': nBeats,
        'rr_ms': rrMs > 0 ? rrMs : null,
        'pat_ms': patMs,
        'pat_iqr_ms': patIqrX10 / 10.0,
        'n_pat': nPat,
        'fs': fsHz,
        'samples': samples,
      };
}

// ------------------------------------------------------------------ lệnh
class Cmd {
  static List<int> startEcg([int seconds = 30]) => [0x01, seconds];
  static List<int> stopEcg() => [0x02];
  static List<int> startSpo2() => [0x03];
  static List<int> setTime(DateTime t) {
    final b = ByteData(5)
      ..setUint8(0, 0x10)
      ..setUint32(1, t.millisecondsSinceEpoch ~/ 1000, _le);
    return b.buffer.asUint8List();
  }

  static List<int> setInterval(int seconds) => [0x20, seconds];
  static List<int> vibrate(int ms) {
    final b = ByteData(3)
      ..setUint8(0, 0x30)
      ..setUint16(1, ms, _le);
    return b.buffer.asUint8List();
  }

  static List<int> alertAcked() => [0x31];
}
