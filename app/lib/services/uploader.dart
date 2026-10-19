import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../config.dart';

/// Hàng đợi gửi dữ liệu lên server, có lưu lại khi mất mạng.
/// Sự kiện (té ngã, SOS) được gửi ngay và ưu tiên trước chỉ số.
class Uploader extends ChangeNotifier {
  final List<Map<String, dynamic>> _vitals = [];
  final List<Map<String, dynamic>> _events = [];
  Timer? _timer;
  bool _busy = false;
  String? lastError;
  DateTime? lastSuccess;

  int get pending => _vitals.length + _events.length;

  void start() {
    _restore();
    _timer ??= Timer.periodic(const Duration(seconds: 5), (_) => flush());
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
  }

  void addVitals(Map<String, dynamic> v) {
    _vitals.add(v);
    if (_vitals.length > 5000) _vitals.removeRange(0, _vitals.length - 5000);
    _persist();
  }

  void addEvent(Map<String, dynamic> e) {
    _events.add(e);
    _persist();
    flush();
  }

  Future<void> flush() async {
    if (_busy || pending == 0 || AppConfig.deviceKey.isEmpty) return;
    _busy = true;
    try {
      if (_events.isNotEmpty) {
        final batch = List<Map<String, dynamic>>.of(_events);
        await Api.sendEvents(batch);
        _events.removeRange(0, batch.length);
      }
      while (_vitals.isNotEmpty) {
        final n = min(200, _vitals.length);
        await Api.sendVitals(_vitals.sublist(0, n));
        _vitals.removeRange(0, n);
      }
      lastSuccess = DateTime.now();
      lastError = null;
    } catch (e) {
      lastError = e.toString();
    } finally {
      _busy = false;
      _persist();
      notifyListeners();
    }
    // có sự kiện mới đến trong lúc đang gửi -> gửi tiếp ngay
    if (lastError == null && _events.isNotEmpty) unawaited(flush());
  }

  void _persist() {
    AppConfig.setString('queue_vitals', jsonEncode(_vitals));
    AppConfig.setString('queue_events', jsonEncode(_events));
  }

  void _restore() {
    for (final (key, list) in [('queue_vitals', _vitals), ('queue_events', _events)]) {
      final s = AppConfig.getString(key);
      if (s == null || list.isNotEmpty) continue;
      try {
        list.addAll((jsonDecode(s) as List).cast<Map<String, dynamic>>());
      } catch (_) {}
    }
  }
}
