import 'dart:async';

import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../main.dart';
import '../services/push_service.dart';

const _levelText = {'info': 'Thông tin', 'warning': 'Cảnh báo', 'danger': 'NGUY HIỂM'};
const _levelColor = {'info': Colors.blue, 'warning': Colors.orange, 'danger': Colors.red};

/// Màn hình người nhà: danh sách cảnh báo (bấm "Đã nhận" để dừng leo thang SMS) và tình trạng người thân.
class CaregiverHome extends StatefulWidget {
  const CaregiverHome({super.key});

  @override
  State<CaregiverHome> createState() => _CaregiverHomeState();
}

class _CaregiverHomeState extends State<CaregiverHome> {
  int _tab = 0;
  List<dynamic> _alerts = [];
  List<Map<String, dynamic>> _summaries = [];
  Map<int, String> _names = {};
  String? _error;
  Timer? _timer;
  StreamSubscription? _pushSub;

  @override
  void initState() {
    super.initState();
    _load();
    _timer = Timer.periodic(const Duration(seconds: 20), (_) => _load());
    _pushSub = PushService.messages.listen((m) {
      _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          backgroundColor: m.data['level'] == 'danger' ? Colors.red : null,
          content: Text('${m.notification?.title ?? 'Cảnh báo mới'}\n${m.notification?.body ?? ''}')));
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pushSub?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final patients = await Api.patients();
      final alerts = await Api.alerts();
      final sums = <Map<String, dynamic>>[];
      for (final p in patients) {
        sums.add(await Api.patientSummary(p['id'] as int));
      }
      if (!mounted) return;
      setState(() {
        _names = {for (final p in patients) p['id'] as int: p['full_name'] as String};
        _alerts = alerts;
        _summaries = sums;
        _error = null;
      });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  Future<void> _act(int id, bool resolve) async {
    try {
      resolve ? await Api.resolveAlert(id) : await Api.ackAlert(id);
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final open = _alerts.where((a) => a['status'] == 'open').length;
    return Scaffold(
      appBar: AppBar(title: const Text('HealthWatch — Người nhà'), actions: [
        IconButton(onPressed: _load, icon: const Icon(Icons.refresh)),
        IconButton(onPressed: () => resetApp(context), icon: const Icon(Icons.logout)),
      ]),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(padding: const EdgeInsets.all(12), children: [
          if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
          if (_tab == 0) ..._alertList() else ..._patientCards(),
        ]),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: [
          NavigationDestination(
              icon: Badge(isLabelVisible: open > 0, label: Text('$open'), child: const Icon(Icons.notifications)),
              label: 'Cảnh báo'),
          const NavigationDestination(icon: Icon(Icons.elderly), label: 'Người thân'),
        ],
      ),
    );
  }

  List<Widget> _alertList() {
    if (_alerts.isEmpty) return [const Padding(padding: EdgeInsets.all(24), child: Text('Chưa có cảnh báo nào.'))];
    return _alerts.map((a) {
      final level = a['level'] as String;
      final color = _levelColor[level] ?? Colors.grey;
      final t = DateTime.parse((a['event_ts'] ?? a['created_at']) as String).toLocal();
      final status = a['status'] as String;
      return Card(
        shape: RoundedRectangleBorder(
            side: BorderSide(color: status == 'open' ? color : Colors.transparent, width: 2),
            borderRadius: BorderRadius.circular(12)),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(10)),
                  child: Text(_levelText[level] ?? level, style: const TextStyle(color: Colors.white))),
              const SizedBox(width: 8),
              Expanded(child: Text(_names[a['patient_id']] ?? '', style: const TextStyle(fontWeight: FontWeight.bold))),
              Text('${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')} ${t.day}/${t.month}'),
            ]),
            const SizedBox(height: 6),
            Text(a['title'] as String, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
            Text(a['message'] as String),
            const SizedBox(height: 6),
            Row(children: [
              Text(status == 'open' ? 'Chưa ai xác nhận' : (status == 'acknowledged' ? 'Đã có người nhận' : 'Đã xử lý'),
                  style: TextStyle(color: status == 'open' ? color : Colors.grey)),
              const Spacer(),
              if (status == 'open') FilledButton(onPressed: () => _act(a['id'] as int, false), child: const Text('Đã nhận')),
              if (status != 'resolved')
                TextButton(onPressed: () => _act(a['id'] as int, true), child: const Text('Đã xử lý')),
            ]),
          ]),
        ),
      );
    }).toList();
  }

  List<Widget> _patientCards() {
    if (_summaries.isEmpty) return [const Padding(padding: EdgeInsets.all(24), child: Text('Chưa được liên kết với ai.'))];
    return _summaries.map((s) {
      final p = s['patient'] as Map<String, dynamic>;
      final latest = s['latest'] as Map<String, dynamic>?;
      final devices = (s['devices'] as List).cast<Map<String, dynamic>>();
      final seen = devices.isNotEmpty && devices.first['last_seen_at'] != null
          ? DateTime.parse(devices.first['last_seen_at'] as String).toLocal()
          : null;
      String fmt(dynamic v, [int digits = 0]) => v == null ? '–' : (v as num).toStringAsFixed(digits);
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(p['full_name'] as String, style: Theme.of(context).textTheme.titleLarge),
            Text(seen == null ? 'Chưa có dữ liệu' : 'Cập nhật ${seen.hour}:${seen.minute.toString().padLeft(2, '0')}'
                ' · pin ${devices.first['last_battery'] ?? '–'}%'),
            const Divider(),
            Wrap(spacing: 24, runSpacing: 8, children: [
              _kv('Nhịp tim', '${fmt(s['last_hr'])} bpm'),
              _kv('SpO2', '${fmt(s['last_spo2'])}%'),
              _kv('Nhiệt độ da', '${fmt(s['last_temp'], 1)}°C'),
              _kv('Huyết áp', s['last_ecg']?['sbp_est'] == null
                  ? '–'
                  : '${fmt(s['last_ecg']['sbp_est'])}/${fmt(s['last_ecg']['dbp_est'])}'),
              _kv('Đang đeo', latest == null ? '–' : (latest['worn'] == true ? 'Có' : 'Không')),
            ]),
          ]),
        ),
      );
    }).toList();
  }

  Widget _kv(String k, String v) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(k, style: TextStyle(color: Theme.of(context).colorScheme.outline)),
        Text(v, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
      ]);
}
