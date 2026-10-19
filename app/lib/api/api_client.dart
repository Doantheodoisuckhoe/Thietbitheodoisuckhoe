import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';

class ApiException implements Exception {
  final int status;
  final String message;
  ApiException(this.status, this.message);
  @override
  String toString() => message;
}

/// Gọi API server. Gateway dùng header X-Device-Key, người nhà dùng JWT.
class Api {
  static const _timeout = Duration(seconds: 15);

  static Map<String, String> _headers({bool device = false}) => {
        'Content-Type': 'application/json',
        if (device) 'X-Device-Key': AppConfig.deviceKey,
        if (!device && AppConfig.userToken.isNotEmpty) 'Authorization': 'Bearer ${AppConfig.userToken}',
      };

  static Uri _u(String path) => Uri.parse('${AppConfig.serverUrl}$path');

  static dynamic _decode(http.Response r) {
    final body = r.body.isEmpty ? null : jsonDecode(utf8.decode(r.bodyBytes));
    if (r.statusCode >= 300) {
      final d = body is Map ? body['detail'] : null;
      throw ApiException(r.statusCode, d is String ? d : 'Lỗi máy chủ (${r.statusCode})');
    }
    return body;
  }

  static Future<dynamic> get(String path, {bool device = false}) async =>
      _decode(await http.get(_u(path), headers: _headers(device: device)).timeout(_timeout));

  static Future<dynamic> post(String path, Object? body, {bool device = false}) async => _decode(
      await http.post(_u(path), headers: _headers(device: device), body: jsonEncode(body)).timeout(_timeout));

  // ---------------------------------------------------------------- gateway
  static Future<Map<String, dynamic>> deviceInfo() async => (await get('/api/ingest/me', device: true)) as Map<String, dynamic>;
  static Future<void> sendVitals(List<Map<String, dynamic>> samples) =>
      post('/api/ingest/vitals', {'samples': samples}, device: true);
  static Future<void> sendEvents(List<Map<String, dynamic>> events) =>
      post('/api/ingest/events', {'events': events}, device: true);
  static Future<Map<String, dynamic>> sendEcg(Map<String, dynamic> ecg) async =>
      (await post('/api/ingest/ecg', ecg, device: true)) as Map<String, dynamic>;
  static Future<List<dynamic>> gatewayAlerts() async => (await get('/api/ingest/alerts', device: true)) as List;

  // ---------------------------------------------------------------- người nhà
  static Future<void> login(String email, String password) async {
    final r = await http.post(_u('/api/auth/login'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {'username': email, 'password': password}).timeout(_timeout);
    final data = _decode(r) as Map<String, dynamic>;
    AppConfig.userToken = data['access_token'] as String;
  }

  static Future<void> registerPushToken(String token) =>
      post('/api/auth/push-token', {'token': token, 'platform': 'android'});
  static Future<List<dynamic>> alerts({String? status}) async =>
      (await get('/api/alerts?limit=50${status != null ? '&status=$status' : ''}')) as List;
  static Future<List<dynamic>> patients() async => (await get('/api/patients')) as List;
  static Future<Map<String, dynamic>> patientSummary(int id) async =>
      (await get('/api/patients/$id')) as Map<String, dynamic>;
  static Future<void> ackAlert(int id) => post('/api/alerts/$id/ack', {});
  static Future<void> resolveAlert(int id) => post('/api/alerts/$id/resolve', {});
  static Future<void> markDelivered(int id) => post('/api/alerts/$id/delivered', {});
}
