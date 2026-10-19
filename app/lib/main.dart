import 'package:flutter/material.dart';

import 'config.dart';
import 'screens/caregiver_home.dart';
import 'screens/gateway_home.dart';
import 'screens/setup_screen.dart';
import 'services/push_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppConfig.load();
  await PushService.init();
  runApp(const HealthWatchApp());
}

class HealthWatchApp extends StatelessWidget {
  const HealthWatchApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HealthWatch',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.teal, useMaterial3: true),
      darkTheme: ThemeData(colorSchemeSeed: Colors.teal, useMaterial3: true, brightness: Brightness.dark),
      home: const RootScreen(),
    );
  }
}

/// Chọn màn hình theo chế độ đã lưu.
class RootScreen extends StatelessWidget {
  const RootScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return switch (AppConfig.mode) {
      AppMode.gateway => const GatewayHome(),
      AppMode.caregiver => const CaregiverHome(),
      AppMode.none => const SetupScreen(),
    };
  }
}

/// Về màn hình cài đặt ban đầu (đổi chế độ / server).
Future<void> resetApp(BuildContext context) async {
  await AppConfig.reset();
  if (!context.mounted) return;
  Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const SetupScreen()), (route) => false);
}
