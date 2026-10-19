import 'package:shared_preferences/shared_preferences.dart';

enum AppMode { none, gateway, caregiver }

/// Cấu hình lưu trên máy.
class AppConfig {
  static late SharedPreferences _p;

  static Future<void> load() async => _p = await SharedPreferences.getInstance();

  static AppMode get mode => AppMode.values[_p.getInt('mode') ?? 0];
  static set mode(AppMode m) => _p.setInt('mode', m.index);

  /// vd http://192.168.1.10:8000 (máy chạy server cùng mạng Wi-Fi)
  static String get serverUrl => _p.getString('server_url') ?? 'http://192.168.1.10:8000';
  static set serverUrl(String v) => _p.setString('server_url', v.trim().replaceAll(RegExp(r'/+$'), ''));

  // gateway (điện thoại của người cao tuổi)
  static String get deviceKey => _p.getString('device_key') ?? '';
  static set deviceKey(String v) => _p.setString('device_key', v.trim());
  static String? get watchId => _p.getString('watch_id');
  static set watchId(String? v) => v == null ? _p.remove('watch_id') : _p.setString('watch_id', v);

  // người nhà
  static String get userToken => _p.getString('user_token') ?? '';
  static set userToken(String v) => _p.setString('user_token', v);

  static String? getString(String k) => _p.getString(k);
  static Future<void> setString(String k, String v) => _p.setString(k, v);

  static Future<void> reset() async {
    await _p.clear();
  }
}
