import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../config.dart';

/// Khi app ở nền, Android tự hiển thị thông báo (payload "notification" từ server).
@pragma('vm:entry-point')
Future<void> firebaseBackgroundHandler(RemoteMessage message) async {}

/// Nhận push cảnh báo (chế độ người nhà). Nếu chưa cấu hình Firebase
/// (thiếu google-services.json) app vẫn chạy, chỉ là không có push.
class PushService {
  static bool available = false;
  static final _controller = StreamController<RemoteMessage>.broadcast();
  static Stream<RemoteMessage> get messages => _controller.stream;

  static Future<void> init() async {
    try {
      await Firebase.initializeApp();
      available = true;
    } catch (e) {
      debugPrint('Firebase chưa cấu hình: $e');
      return;
    }
    FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);
    FirebaseMessaging.onMessage.listen(_handle);
    FirebaseMessaging.onMessageOpenedApp.listen(_handle);
    final initial = await FirebaseMessaging.instance.getInitialMessage();
    if (initial != null) _handle(initial);
  }

  static void _handle(RemoteMessage m) {
    _markDelivered(m);
    _controller.add(m);
  }

  /// Báo server "đã nhận" để đo độ trễ đầu-cuối (chỉ đo được khi app đang mở
  /// hoặc người dùng chạm vào thông báo).
  static Future<void> _markDelivered(RemoteMessage m) async {
    final id = int.tryParse(m.data['alert_id']?.toString() ?? '');
    if (id == null || AppConfig.userToken.isEmpty) return;
    try {
      await Api.markDelivered(id);
    } catch (_) {}
  }

  static Future<void> registerCaregiver() async {
    if (!available) return;
    await FirebaseMessaging.instance.requestPermission(alert: true, sound: true, badge: true);
    final token = await FirebaseMessaging.instance.getToken();
    if (token != null) await Api.registerPushToken(token);
    FirebaseMessaging.instance.onTokenRefresh.listen((t) async {
      try {
        await Api.registerPushToken(t);
      } catch (_) {}
    });
  }
}
