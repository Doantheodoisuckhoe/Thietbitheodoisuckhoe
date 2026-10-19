import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import '../ble/protocol.dart';
import '../ble/watch_service.dart';

/// Đo ECG 30 giây: hướng dẫn -> ghi (vẽ sóng trực tiếp) -> kết quả + huyết áp ước lượng từ server.
class EcgScreen extends StatefulWidget {
  final WatchService watch;
  const EcgScreen({super.key, required this.watch});

  @override
  State<EcgScreen> createState() => _EcgScreenState();
}

class _EcgScreenState extends State<EcgScreen> {
  Timer? _tick;

  @override
  void initState() {
    super.initState();
    widget.watch.startEcg();
    _tick = Timer.periodic(const Duration(milliseconds: 250), (_) => setState(() {}));
  }

  @override
  void dispose() {
    _tick?.cancel();
    final s = widget.watch.ecg;
    if (s != null && !s.done) widget.watch.cancelEcg();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.watch.ecg;
    return Scaffold(
      appBar: AppBar(title: const Text('Đo điện tim (ECG)')),
      body: s == null ? const SizedBox() : Padding(padding: const EdgeInsets.all(16), child: _body(context, s)),
    );
  }

  Widget _body(BuildContext context, EcgSession s) {
    final children = <Widget>[];
    if (s.startedAt == null && !s.done) {
      children.addAll([
        const Icon(Icons.touch_app, size: 64),
        const SizedBox(height: 12),
        const Text('Đặt một ngón tay của tay kia lên điện cực trên mặt đồng hồ và giữ yên.',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 20)),
        const SizedBox(height: 8),
        const Text('Không đo khi đồng hồ đang cắm sạc.', textAlign: TextAlign.center),
        const SizedBox(height: 24),
        const CircularProgressIndicator(),
      ]);
    } else {
      const total = 30.0;
      final elapsed = s.startedAt == null ? total : DateTime.now().difference(s.startedAt!).inMilliseconds / 1000;
      final fs = (s.result?.fsHz ?? 256).toDouble();
      children.addAll([
        if (s.recording) ...[
          Text(s.leadOff ? 'Mất tiếp xúc — giữ ngón tay trên điện cực!' : 'Đang ghi... giữ yên tay',
              style: TextStyle(fontSize: 18, color: s.leadOff ? Colors.red : null)),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: min(1.0, elapsed / total)),
          const SizedBox(height: 4),
          Text('${min(total, elapsed).toStringAsFixed(0)} / ${total.toStringAsFixed(0)} giây'),
        ],
        const SizedBox(height: 12),
        SizedBox(height: 220, child: CustomPaint(painter: EcgPainter(s.samples, fs: fs), size: Size.infinite)),
      ]);
    }
    if (s.done) children.add(_result(context, s));
    children.add(const Spacer());
    children.add(Row(children: [
      if (!s.done) Expanded(child: OutlinedButton(onPressed: widget.watch.cancelEcg, child: const Text('Huỷ'))),
      if (s.done) ...[
        Expanded(child: OutlinedButton(onPressed: () => Navigator.pop(context), child: const Text('Đóng'))),
        const SizedBox(width: 12),
        Expanded(child: FilledButton(onPressed: widget.watch.startEcg, child: const Text('Đo lại'))),
      ],
    ]));
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: children);
  }

  Widget _result(BuildContext context, EcgSession s) {
    final r = s.result;
    final server = s.server;
    final rows = <Widget>[];
    if (r != null) {
      rows.add(Text(ecgStatusText[r.status] ?? '', style: Theme.of(context).textTheme.titleMedium));
      if (r.hr > 0) rows.add(_kv('Nhịp tim (ECG)', '${r.hr} lần/phút · ${r.nBeats} nhịp'));
      if (r.patMs != null) rows.add(_kv('PAT', '${r.patMs!.toStringAsFixed(1)} ms'));
    }
    if (s.uploading) rows.add(const Padding(padding: EdgeInsets.all(8), child: LinearProgressIndicator()));
    if (server != null) {
      if (server['sbp_est'] != null) {
        rows.add(_kv('Huyết áp ước lượng', '${(server['sbp_est'] as num).round()}/${(server['dbp_est'] as num).round()} mmHg'));
        rows.add(const Text('Chỉ mang tính tham khảo. Nếu cao bất thường hãy đo lại bằng máy vòng bít.',
            style: TextStyle(fontStyle: FontStyle.italic)));
      } else if (server['calibrated'] == false) {
        rows.add(const Text('Chưa hiệu chuẩn huyết áp: nhờ người nhà nhập kết quả máy vòng bít trên web.'));
      }
    }
    if (s.error != null) rows.add(Text(s.error!, style: const TextStyle(color: Colors.red, fontSize: 16)));
    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: rows)));
  }

  Widget _kv(String k, String v) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [Expanded(child: Text(k)), Text(v, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold))]));
}

/// Vẽ 5 giây ECG gần nhất.
class EcgPainter extends CustomPainter {
  final List<int> samples;
  final double fs;
  EcgPainter(this.samples, {this.fs = 256});

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()
      ..color = const Color(0x1FF44336) // đỏ nhạt (lưới giấy ECG)
      ..strokeWidth = 1;
    for (var x = 0.0; x < size.width; x += size.width / 25) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), grid);
    }
    for (var y = 0.0; y < size.height; y += size.width / 25) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }
    final n = min(samples.length, (5 * fs).round());
    if (n < 2) return;
    final data = samples.sublist(samples.length - n);
    var lo = data.reduce(min).toDouble(), hi = data.reduce(max).toDouble();
    if (hi - lo < 1) hi = lo + 1;
    final path = Path();
    for (var i = 0; i < n; i++) {
      final x = i / (5 * fs) * size.width;
      final y = size.height - (data[i] - lo) / (hi - lo) * (size.height * 0.9) - size.height * 0.05;
      i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
    }
    canvas.drawPath(
        path,
        Paint()
          ..color = Colors.red
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5);
  }

  @override
  bool shouldRepaint(EcgPainter old) => true;
}
