import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../config.dart';
import '../services/push_service.dart';
import 'caregiver_home.dart';
import 'gateway_home.dart';

/// Cài đặt lần đầu: chọn vai trò của điện thoại này.
class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  AppMode _mode = AppMode.gateway;
  final _server = TextEditingController(text: AppConfig.serverUrl);
  final _key = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    AppConfig.serverUrl = _server.text;
    try {
      Widget next;
      if (_mode == AppMode.gateway) {
        AppConfig.deviceKey = _key.text;
        final info = await Api.deviceInfo();
        if (!mounted) return;
        await showDialog(
            context: context,
            builder: (c) => AlertDialog(
                  title: const Text('Kết nối thành công'),
                  content: Text('Điện thoại này sẽ chuyển dữ liệu đồng hồ của:\n${info['patient_name']}'),
                  actions: [TextButton(onPressed: () => Navigator.pop(c), child: const Text('OK'))],
                ));
        next = const GatewayHome();
      } else {
        await Api.login(_email.text.trim(), _password.text);
        await PushService.registerCaregiver();
        next = const CaregiverHome();
      }
      AppConfig.mode = _mode;
      if (!mounted) return;
      Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => next));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cài đặt HealthWatch')),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        const Text('Điện thoại này dùng để:', style: TextStyle(fontSize: 16)),
        const SizedBox(height: 8),
        SegmentedButton<AppMode>(
          segments: const [
            ButtonSegment(value: AppMode.gateway, label: Text('Kết nối đồng hồ'), icon: Icon(Icons.watch)),
            ButtonSegment(value: AppMode.caregiver, label: Text('Người nhà'), icon: Icon(Icons.family_restroom)),
          ],
          selected: {_mode},
          onSelectionChanged: (s) => setState(() => _mode = s.first),
        ),
        const SizedBox(height: 8),
        Text(
          _mode == AppMode.gateway
              ? 'Điện thoại của người cao tuổi: nhận dữ liệu từ đồng hồ qua Bluetooth và gửi lên server.'
              : 'Điện thoại của người nhà: nhận thông báo cảnh báo và xác nhận đã nhận.',
          style: TextStyle(color: Theme.of(context).colorScheme.outline),
        ),
        const SizedBox(height: 20),
        TextField(
            controller: _server,
            decoration: const InputDecoration(labelText: 'Địa chỉ server', hintText: 'http://192.168.1.10:8000'),
            keyboardType: TextInputType.url),
        const SizedBox(height: 12),
        if (_mode == AppMode.gateway)
          TextField(
              controller: _key,
              decoration: const InputDecoration(
                  labelText: 'API key thiết bị', helperText: 'Lấy trên web dashboard: Cài đặt > Đăng ký thiết bị')),
        if (_mode == AppMode.caregiver) ...[
          TextField(controller: _email, decoration: const InputDecoration(labelText: 'Email'),
              keyboardType: TextInputType.emailAddress),
          const SizedBox(height: 12),
          TextField(controller: _password, decoration: const InputDecoration(labelText: 'Mật khẩu'), obscureText: true),
          const SizedBox(height: 8),
          if (!PushService.available)
            const Text('Chưa cấu hình Firebase — app vẫn xem được cảnh báo nhưng không nhận thông báo đẩy.',
                style: TextStyle(color: Colors.orange)),
        ],
        const SizedBox(height: 20),
        FilledButton(
            onPressed: _busy ? null : _submit,
            child: Padding(
                padding: const EdgeInsets.all(12),
                child: _busy ? const CircularProgressIndicator() : const Text('Tiếp tục', style: TextStyle(fontSize: 18)))),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
      ]),
    );
  }
}
