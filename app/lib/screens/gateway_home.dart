import 'package:flutter/material.dart';

import '../ble/protocol.dart';
import '../ble/watch_service.dart';
import '../main.dart';
import '../services/uploader.dart';
import 'ecg_screen.dart';

/// Màn hình điện thoại của người cao tuổi: kết nối đồng hồ, hiển thị chỉ số, chuyển dữ liệu lên server.
/// Chữ to, nút lớn cho người lớn tuổi. Nên để app luôn mở (không tắt hẳn) để dữ liệu được gửi liên tục.
class GatewayHome extends StatefulWidget {
  const GatewayHome({super.key});

  @override
  State<GatewayHome> createState() => _GatewayHomeState();
}

class _GatewayHomeState extends State<GatewayHome> {
  late final Uploader uploader;
  late final WatchService watch;

  @override
  void initState() {
    super.initState();
    uploader = Uploader()..start();
    watch = WatchService(uploader)..init();
  }

  @override
  void dispose() {
    watch.dispose();
    uploader.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([watch, uploader]),
      builder: (context, _) {
        final v = watch.lastVitals;
        return Scaffold(
          appBar: AppBar(title: const Text('Đồng hồ sức khỏe'), actions: [
            PopupMenuButton<String>(
              onSelected: (s) async {
                if (s == 'forget') await watch.disconnect(forget: true);
                if (s == 'reset' && context.mounted) resetApp(context);
              },
              itemBuilder: (_) => const [
                PopupMenuItem(value: 'forget', child: Text('Quên đồng hồ này')),
                PopupMenuItem(value: 'reset', child: Text('Đổi chế độ / server')),
              ],
            ),
          ]),
          body: RefreshIndicator(
            onRefresh: uploader.flush,
            child: ListView(padding: const EdgeInsets.all(16), children: [
              _connectionCard(context),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                childAspectRatio: 1.5,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                children: [
                  _metric(context, 'Nhịp tim', v != null && v.hr > 0 ? '${v.hr}' : '–', 'lần/phút', Icons.favorite,
                      Colors.red),
                  _metric(context, 'SpO2', watch.lastSpo2 != null ? '${watch.lastSpo2}%' : '–',
                      watch.lastSpo2At != null ? 'lúc ${_hm(watch.lastSpo2At!)}' : 'đo khi ngồi yên', Icons.air,
                      Colors.blue),
                  _metric(context, 'Nhiệt độ da', v?.skinTemp != null ? v!.skinTemp!.toStringAsFixed(1) : '–', '°C',
                      Icons.thermostat, Colors.orange),
                  _metric(context, 'Pin đồng hồ', v != null ? '${v.batteryPct}%' : '–',
                      v == null ? '' : (v.charging ? 'đang sạc' : (v.worn ? 'đang đeo' : 'chưa đeo')),
                      Icons.battery_std, Colors.green),
                ],
              ),
              const SizedBox(height: 16),
              Row(children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: watch.connected
                        ? () => Navigator.push(context, MaterialPageRoute(builder: (_) => EcgScreen(watch: watch)))
                        : null,
                    icon: const Icon(Icons.monitor_heart),
                    label: const Padding(padding: EdgeInsets.all(14), child: Text('Đo ECG', style: TextStyle(fontSize: 18))),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: watch.connected ? () => _spo2(context) : null,
                    icon: const Icon(Icons.air),
                    label: const Padding(padding: EdgeInsets.all(14), child: Text('Đo SpO2', style: TextStyle(fontSize: 18))),
                  ),
                ),
              ]),
              const SizedBox(height: 16),
              Text('Sự kiện gần đây', style: Theme.of(context).textTheme.titleMedium),
              if (watch.events.isEmpty) const Padding(padding: EdgeInsets.all(8), child: Text('Chưa có sự kiện')),
              ...watch.events.take(10).map((e) => ListTile(
                    dense: true,
                    leading: Icon(e.type == 1 || e.type == 2 ? Icons.warning : Icons.info_outline,
                        color: e.type == 1 || e.type == 2 ? Colors.red : null),
                    title: Text(eventLabels[e.name] ?? e.name),
                    subtitle: Text(_hm(e.time.toLocal())),
                  )),
              const Divider(),
              Text(
                'Gửi lên server: ${uploader.pending} gói đang chờ'
                '${uploader.lastSuccess != null ? ' · lần cuối ${_hm(uploader.lastSuccess!)}' : ''}'
                '${uploader.lastError != null ? '\nLỗi: ${uploader.lastError}' : ''}',
                style: TextStyle(color: uploader.lastError != null ? Colors.red : Theme.of(context).colorScheme.outline),
              ),
            ]),
          ),
        );
      },
    );
  }

  Widget _connectionCard(BuildContext context) {
    final ok = watch.connected;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(ok ? Icons.bluetooth_connected : Icons.bluetooth_disabled, color: ok ? Colors.green : Colors.grey),
            const SizedBox(width: 8),
            Expanded(child: Text(watch.status, style: const TextStyle(fontSize: 16))),
            if (!ok)
              TextButton(
                  onPressed: watch.scanning ? null : watch.scan,
                  child: Text(watch.scanning ? 'Đang tìm...' : 'Tìm đồng hồ')),
          ]),
          if (!ok)
            ...watch.scanResults.map((r) => ListTile(
                  leading: const Icon(Icons.watch),
                  title: Text(r.advertisementData.advName.isEmpty ? r.device.remoteId.str : r.advertisementData.advName),
                  subtitle: Text('Tín hiệu ${r.rssi} dBm'),
                  trailing: const Icon(Icons.link),
                  onTap: () => watch.connect(r.device),
                )),
        ]),
      ),
    );
  }

  Future<void> _spo2(BuildContext context) async {
    await watch.send(Cmd.startSpo2());
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Đang đo SpO2 trong 30 giây — giữ yên tay. Kết quả sẽ hiện ở ô SpO2.')));
  }

  Widget _metric(BuildContext context, String label, String value, String sub, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Icon(icon, color: color, size: 20), const SizedBox(width: 6), Text(label)]),
          const Spacer(),
          Text(value, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
          Text(sub, style: TextStyle(color: Theme.of(context).colorScheme.outline)),
        ]),
      ),
    );
  }
}

String _hm(DateTime t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
