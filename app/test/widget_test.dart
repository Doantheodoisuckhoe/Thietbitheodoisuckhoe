// Kiểm thử giải mã gói BLE (khớp với firmware/health_watch/protocol.h):  flutter test
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:health_watch_app/ble/protocol.dart';

void main() {
  test('VitalsPacket 20 byte', () {
    final b = ByteData(20)
      ..setUint8(0, 1)
      ..setUint8(1, flagWorn | flagTimeSynced)
      ..setUint16(2, 513, Endian.little)
      ..setUint32(4, 1760500000, Endian.little)
      ..setUint8(8, 72)
      ..setUint8(9, 90)
      ..setUint8(10, 97)
      ..setUint8(11, 80)
      ..setInt16(12, 3312, Endian.little)
      ..setUint16(14, 25, Endian.little)
      ..setUint8(16, 81)
      ..setUint8(17, 10)
      ..setUint16(18, 3950, Endian.little);
    final p = VitalsPacket.parse(b.buffer.asUint8List())!;
    expect(p.hr, 72);
    expect(p.spo2, 97);
    expect(p.skinTemp, closeTo(33.12, 1e-9));
    expect(p.worn, isTrue);
    expect(p.charging, isFalse);
    expect(p.time.millisecondsSinceEpoch, 1760500000 * 1000);
    expect(p.toJson()['seq'], 513);
  });

  test('VitalsPacket không có nhiệt độ / HR', () {
    final b = ByteData(20)..setInt16(12, tempNone, Endian.little);
    final p = VitalsPacket.parse(b.buffer.asUint8List())!;
    expect(p.skinTemp, isNull);
    expect(p.toJson()['hr'], isNull);
  });

  test('EventPacket té ngã', () {
    final b = ByteData(16)
      ..setUint8(1, 1)
      ..setUint16(2, 7, Endian.little)
      ..setUint32(4, 1760500000, Endian.little)
      ..setInt16(8, 420, Endian.little)
      ..setInt16(10, 80, Endian.little)
      ..setUint16(12, 1, Endian.little)
      ..setUint8(14, flagTimeSynced);
    final e = EventPacket.parse(b.buffer.asUint8List())!;
    expect(e.name, 'fall');
    expect(e.toJson()['value1'], closeTo(4.2, 1e-9));
  });

  test('EcgDataPacket', () {
    final b = ByteData(6 + 4)
      ..setUint8(0, 3)
      ..setUint8(1, 1)
      ..setUint16(2, 9, Endian.little)
      ..setUint8(4, 2)
      ..setInt16(6, -100, Endian.little)
      ..setInt16(8, 250, Endian.little);
    final p = EcgDataPacket.parse(b.buffer.asUint8List())!;
    expect(p.samples, [-100, 250]);
    expect(p.leadOff, isTrue);
  });

  test('Lệnh SET_TIME', () {
    final c = Cmd.setTime(DateTime.fromMillisecondsSinceEpoch(1760500000 * 1000));
    expect(c.length, 5);
    expect(c[0], 0x10);
    expect(ByteData.sublistView(Uint8List.fromList(c)).getUint32(1, Endian.little), 1760500000);
  });

  test('UUID khớp firmware', () {
    expect(kServiceUuid.toString().toLowerCase(), 'a7e10000-4b2c-4d8e-9f10-5c3e2a1b0d47');
    expect(kControlUuid.toString().toLowerCase(), 'a7e10005-4b2c-4d8e-9f10-5c3e2a1b0d47');
  });
}
