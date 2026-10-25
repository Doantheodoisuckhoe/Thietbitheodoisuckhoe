// App dong ho suc khoe: nhan so do tu dong ho qua BLE, gui SMS cho nguoi than khi co canh bao.
// Giao thuc: docs/giao-thuc-ble.md. Huong dan build va cai: app/suc_khoe/README.md
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:permission_handler/permission_handler.dart';

import 'dam_may.dart';
import 'dich_vu_dien_thoai.dart' as dt;
import 'dong_ho.dart';
import 'giao_thuc.dart';
import 'luu_tru.dart';
import 'xu_ly_canh_bao.dart';

final dongHo = DongHo();
final luuTru = LuuTru();
final damMay = DamMay();
late final XuLyCanhBao xuLy;
final _thongBao = GlobalKey<ScaffoldMessengerState>();
final _dieuHuong = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  FlutterForegroundTask.initCommunicationPort();
  await luuTru.tai();
  xuLy = XuLyCanhBao(
    guiSms: dt.guiSms,
    layViTri: dt.layViTri,
    guiLenh: dongHo.guiLenh,
    danhBa: () => luuTru.danhBa,
    tenNguoiDeo: () => luuTru.tenNguoiDeo,
  );
  dongHo.khiCoCanhBao = _khiCoCanhBao;
  damMay.cauHinh = luuTru.damMay;
  dongHo.khiCoSoDo = (s) => damMay.nhanSoDo(s, ketNoi: true);
  dongHo.khiMatKetNoi = damMay.baoMatKetNoi;
  runApp(const UngDung());
}

String? _khoaLoiCuoi; // de khong ghi lich su lap lai moi 5 giay khi gui SMS that bai

Future<void> _khiCoCanhBao(CanhBao cb) async {
  final kq = await xuLy.nhan(cb);
  if (kq == null) return;
  final ok = kq.soTinDaGui > 0;
  if (!ok && _khoaLoiCuoi == cb.khoa) return;
  _khoaLoiCuoi = ok ? null : cb.khoa;

  final chiTiet = [
    if (cb.moTaGiaTri.isNotEmpty) cb.moTaGiaTri,
    ok
        ? 'Đã gửi SMS cho ${kq.soTinDaGui}/${kq.soNguoiThan} người thân'
        : (kq.soNguoiThan == 0
            ? 'CHƯA GỬI: chưa có số người thân'
            : 'CHƯA GỬI ĐƯỢC SMS, đang thử lại (kiểm tra quyền SMS, sóng, tài khoản)'),
    if (!kq.coViTri) 'không lấy được vị trí',
  ].join(' · ');
  await luuTru.ghiLichSu(MucLichSu(kq.luc, cb.loai.ten, chiTiet, cb.loai.khanCap));
  unawaited(damMay.nhanCanhBao(kq));
  FlutterForegroundTask.updateService(
    notificationTitle: 'CẢNH BÁO: ${cb.loai.ten}',
    notificationText: chiTiet,
  );
  _dieuHuong.currentState?.push(MaterialPageRoute(
    builder: (_) => ManHinhCanhBao(canhBao: cb, chiTiet: chiTiet),
  ));

  // SOS / te nga: goi luon cho nguoi than dau tien (Android chi cho goi khi app dang mo tren man hinh).
  if (ok && cb.loai.khanCap && luuTru.danhBa.isNotEmpty) {
    if (await FlutterForegroundTask.isAppOnForeground) {
      await dt.goiDien(luuTru.danhBa.first.soDienThoai);
    }
  }
}

Future<void> _chayNen() async {
  FlutterForegroundTask.init(
    androidNotificationOptions: AndroidNotificationOptions(
      channelId: 'theo_doi',
      channelName: 'Theo dõi đồng hồ',
      channelDescription: 'Giữ kết nối với đồng hồ để gửi cảnh báo khi tắt màn hình',
    ),
    iosNotificationOptions: const IOSNotificationOptions(),
    foregroundTaskOptions: ForegroundTaskOptions(
      eventAction: ForegroundTaskEventAction.nothing(),
      allowWakeLock: true,
    ),
  );
  if (await FlutterForegroundTask.isRunningService) return;
  final coViTri = await Permission.locationWhenInUse.isGranted;
  await FlutterForegroundTask.startService(
    serviceId: 100,
    serviceTypes: [
      ForegroundServiceTypes.connectedDevice,
      if (coViTri) ForegroundServiceTypes.location,
    ],
    notificationTitle: 'Đang theo dõi đồng hồ sức khỏe',
    notificationText: 'Cảnh báo sẽ được gửi SMS cho người thân',
  );
}

class UngDung extends StatelessWidget {
  const UngDung({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sức khỏe',
      navigatorKey: _dieuHuong,
      scaffoldMessengerKey: _thongBao,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.teal,
        useMaterial3: true,
        textTheme: Typography.blackMountainView.apply(fontSizeFactor: 1.1),
      ),
      home: const ManHinhChinh(),
    );
  }
}

class ManHinhChinh extends StatefulWidget {
  const ManHinhChinh({super.key});
  @override
  State<ManHinhChinh> createState() => _ManHinhChinhState();
}

class _ManHinhChinhState extends State<ManHinhChinh> {
  int _tab = 0;
  List<String> _thieuQuyen = [];

  @override
  void initState() {
    super.initState();
    _khoiDong();
  }

  Future<void> _khoiDong() async {
    _thieuQuyen = await dt.xinQuyen();
    if (mounted) setState(() {});
    await FlutterForegroundTask.requestIgnoreBatteryOptimization();
    await _chayNen();
    await dongHo.batDau();
  }

  @override
  Widget build(BuildContext context) {
    final trang = [const TrangSoDo(), const TrangNguoiThan(), const TrangLichSu(), const TrangCaiDat()][_tab];
    return WithForegroundTask(
      child: Scaffold(
        appBar: AppBar(title: const Text('Đồng hồ sức khỏe')),
        body: Column(children: [
          if (_thieuQuyen.isNotEmpty)
            MaterialBanner(
              backgroundColor: Colors.orange.shade100,
              content: Text('Thiếu quyền: ${_thieuQuyen.join(', ')}. App cần đủ quyền để gửi cảnh báo.'),
              actions: [
                TextButton(onPressed: openAppSettings, child: const Text('Mở cài đặt')),
                TextButton(
                  onPressed: () async {
                    _thieuQuyen = await dt.xinQuyen();
                    setState(() {});
                  },
                  child: const Text('Kiểm tra lại'),
                ),
              ],
            ),
          Expanded(child: trang),
        ]),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _tab,
          onDestinationSelected: (i) => setState(() => _tab = i),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.favorite), label: 'Số đo'),
            NavigationDestination(icon: Icon(Icons.contacts), label: 'Người thân'),
            NavigationDestination(icon: Icon(Icons.history), label: 'Lịch sử'),
            NavigationDestination(icon: Icon(Icons.cloud_outlined), label: 'Web'),
          ],
        ),
      ),
    );
  }
}

// ---------------- Trang so do ----------------
class TrangSoDo extends StatelessWidget {
  const TrangSoDo({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: dongHo,
      builder: (context, _) {
        final s = dongHo.soDo;
        final ketNoi = dongHo.trangThai == TrangThai.daKetNoi;
        final cu = s == null || DateTime.now().difference(s.luc) > const Duration(seconds: 10);
        String hien(Object? v, String donVi) => (v == null || cu || !s.dangDeo) ? '--' : '$v $donVi';

        return ListView(padding: const EdgeInsets.all(16), children: [
          Card(
            color: ketNoi ? Colors.green.shade50 : Colors.orange.shade50,
            child: ListTile(
              leading: Icon(ketNoi ? Icons.bluetooth_connected : Icons.bluetooth_searching,
                  color: ketNoi ? Colors.green : Colors.orange, size: 36),
              title: Text(dongHo.trangThai.moTa),
              subtitle: Text([
                if (ketNoi && s != null) (s.dangDeo ? 'Đang đeo' : 'Chưa đeo đồng hồ'),
                if (dongHo.loi != null) dongHo.loi!,
              ].join('\n')),
            ),
          ),
          const SizedBox(height: 8),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            childAspectRatio: 1.3,
            children: [
              _O(Icons.favorite, Colors.red, 'Nhịp tim', hien(s?.nhipTim, 'l/p')),
              _O(Icons.air, Colors.blue, 'SpO2', hien(s?.spo2, '%')),
              _O(Icons.thermostat, Colors.orange, 'Nhiệt độ da', hien(s?.nhietDo?.toStringAsFixed(1), '°C')),
              _O(Icons.battery_std, Colors.green, 'Pin đồng hồ',
                  (s == null || cu) ? '--' : '${s.pinPhanTram} %'),
            ],
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: ketNoi ? () => dongHo.guiLenh(lenhTimDongHo) : null,
            icon: const Icon(Icons.vibration),
            label: const Text('Tìm đồng hồ (rung 2 giây)'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () => _guiThu(context),
            icon: const Icon(Icons.sms),
            label: const Text('Gửi thử SMS cho người thân'),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: dongHo.quenDongHo,
            child: const Text('Đổi đồng hồ khác (tìm lại)'),
          ),
          const SizedBox(height: 8),
          Text(
            'SpO2 chưa hiệu chuẩn; nhiệt độ là nhiệt độ da cổ tay, thấp hơn thân nhiệt. '
            'Chỉ dùng để theo dõi, không thay thiết bị y tế.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ]);
      },
    );
  }

  Future<void> _guiThu(BuildContext context) async {
    if (luuTru.danhBa.isEmpty) {
      _thongBao.currentState?.showSnackBar(const SnackBar(content: Text('Chưa có số người thân')));
      return;
    }
    final vt = await dt.layViTri();
    final noiDung = '[Dong ho suc khoe] Tin nhan thu tu app, khong phai canh bao.'
        '${vt == null ? ' Khong lay duoc vi tri.' : ' Vi tri: https://maps.google.com/?q=${vt.$1.toStringAsFixed(5)},${vt.$2.toStringAsFixed(5)}'}';
    var ok = 0;
    for (final n in luuTru.danhBa) {
      if (await dt.guiSms(n.soDienThoai, noiDung)) ok++;
    }
    _thongBao.currentState?.showSnackBar(
        SnackBar(content: Text('Đã gửi $ok/${luuTru.danhBa.length} tin${vt == null ? ', không lấy được vị trí' : ''}')));
  }
}

class _O extends StatelessWidget {
  final IconData icon;
  final Color mau;
  final String ten, giaTri;
  const _O(this.icon, this.mau, this.ten, this.giaTri);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Icon(icon, color: mau),
            const SizedBox(width: 6),
            Text(ten),
          ]),
          const SizedBox(height: 8),
          FittedBox(
            child: Text(giaTri, style: const TextStyle(fontSize: 34, fontWeight: FontWeight.bold)),
          ),
        ]),
      ),
    );
  }
}

// ---------------- Trang nguoi than ----------------
Timer? _henGuiTen;

class TrangNguoiThan extends StatelessWidget {
  const TrangNguoiThan({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: luuTru,
      builder: (context, _) => ListView(padding: const EdgeInsets.all(16), children: [
        TextFormField(
          initialValue: luuTru.tenNguoiDeo,
          decoration: const InputDecoration(
            labelText: 'Tên người đeo đồng hồ (ghi trong SMS)',
            hintText: 'VD: Ba Nguyen Thi Hang',
            border: OutlineInputBorder(),
          ),
          onChanged: (t) {
            luuTru.datTen(t);
            _henGuiTen?.cancel();
            _henGuiTen = Timer(const Duration(seconds: 2), () => damMay.guiThongTin(t));
          },
        ),
        const SizedBox(height: 16),
        Text('Người thân nhận SMS', style: Theme.of(context).textTheme.titleMedium),
        const Text('Khi có SOS hoặc té ngã, app gọi điện cho người đầu tiên trong danh sách.'),
        const SizedBox(height: 8),
        if (luuTru.danhBa.isEmpty)
          const Card(child: ListTile(title: Text('Chưa có ai. Bấm nút + để thêm.'))),
        for (var i = 0; i < luuTru.danhBa.length; i++)
          Card(
            child: ListTile(
              leading: CircleAvatar(child: Text('${i + 1}')),
              title: Text(luuTru.danhBa[i].ten),
              subtitle: Text(luuTru.danhBa[i].soDienThoai),
              trailing: IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: () => luuTru.xoaNguoiThan(i),
              ),
            ),
          ),
        const SizedBox(height: 8),
        FilledButton.icon(
          onPressed: () => _them(context),
          icon: const Icon(Icons.add),
          label: const Text('Thêm người thân'),
        ),
      ]),
    );
  }

  Future<void> _them(BuildContext context) async {
    final ten = TextEditingController(), so = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Thêm người thân'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: ten, decoration: const InputDecoration(labelText: 'Tên')),
          TextField(
            controller: so,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(labelText: 'Số điện thoại'),
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Hủy')),
          FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Lưu')),
        ],
      ),
    );
    final s = so.text.replaceAll(RegExp(r'[^0-9+]'), '');
    if (ok == true && s.length >= 9) {
      await luuTru.themNguoiThan(NguoiThan(ten.text.trim().isEmpty ? s : ten.text.trim(), s));
    } else if (ok == true) {
      _thongBao.currentState?.showSnackBar(const SnackBar(content: Text('Số điện thoại không hợp lệ')));
    }
  }
}

// ---------------- Trang lich su ----------------
class TrangLichSu extends StatelessWidget {
  const TrangLichSu({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: luuTru,
      builder: (context, _) {
        if (luuTru.lichSu.isEmpty) {
          return const Center(child: Text('Chưa có cảnh báo nào'));
        }
        return ListView.builder(
          itemCount: luuTru.lichSu.length,
          itemBuilder: (context, i) {
            final m = luuTru.lichSu[i];
            final l = m.luc;
            String h(int n) => n.toString().padLeft(2, '0');
            return ListTile(
              leading: Icon(m.khanCap ? Icons.warning : Icons.info_outline,
                  color: m.khanCap ? Colors.red : Colors.orange),
              title: Text('${m.loai}  ·  ${h(l.hour)}:${h(l.minute)} ${h(l.day)}/${h(l.month)}'),
              subtitle: Text(m.chiTiet),
            );
          },
        );
      },
    );
  }
}

// ---------------- Man hinh canh bao ----------------
class ManHinhCanhBao extends StatelessWidget {
  final CanhBao canhBao;
  final String chiTiet;
  const ManHinhCanhBao({super.key, required this.canhBao, required this.chiTiet});

  @override
  Widget build(BuildContext context) {
    final mau = canhBao.loai.khanCap ? Colors.red : Colors.orange;
    return Scaffold(
      backgroundColor: mau.shade50,
      appBar: AppBar(title: const Text('Cảnh báo'), backgroundColor: mau.shade100),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Icon(Icons.warning_amber_rounded, size: 96, color: mau),
          Text(canhBao.loai.ten.toUpperCase(),
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: mau.shade900)),
          const SizedBox(height: 16),
          Text(chiTiet, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18)),
          const Spacer(),
          for (final n in luuTru.danhBa)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: FilledButton.icon(
                style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(56)),
                onPressed: () => dt.goiDien(n.soDienThoai),
                icon: const Icon(Icons.call),
                label: Text('Gọi ${n.ten}'),
              ),
            ),
          OutlinedButton(
            style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(56)),
            onPressed: () => Navigator.pop(context),
            child: const Text('Đóng'),
          ),
        ]),
      ),
    );
  }
}

// ---------------- Trang cai dat web (Firebase) ----------------
class TrangCaiDat extends StatefulWidget {
  const TrangCaiDat({super.key});
  @override
  State<TrangCaiDat> createState() => _TrangCaiDatState();
}

class _TrangCaiDatState extends State<TrangCaiDat> {
  final _apiKey = TextEditingController();
  final _dbUrl = TextEditingController();
  final _email = TextEditingController();
  final _matKhau = TextEditingController();
  bool _dangChay = false;
  String? _loi;
  Timer? _capNhat;

  @override
  void initState() {
    super.initState();
    final c = luuTru.damMay;
    _apiKey.text = c?.apiKey ?? '';
    _dbUrl.text = c?.dbUrl ?? '';
    _email.text = c?.email ?? '';
    // Cap nhat dong "lan gui cuoi" moi 5 giay.
    _capNhat = Timer.periodic(const Duration(seconds: 5), (_) => setState(() {}));
  }

  @override
  void dispose() {
    _capNhat?.cancel();
    super.dispose();
  }

  Future<void> _dangNhap() async {
    setState(() {
      _dangChay = true;
      _loi = null;
    });
    try {
      final c = await damMay.dangNhap(_apiKey.text, _dbUrl.text, _email.text, _matKhau.text);
      await luuTru.luuDamMay(c);
      await damMay.guiThongTin(luuTru.tenNguoiDeo);
      _matKhau.clear();
    } catch (e) {
      damMay.dangXuat();
      _loi = e.toString();
    }
    if (mounted) setState(() => _dangChay = false);
  }

  Future<void> _dangXuat() async {
    damMay.dangXuat();
    await luuTru.luuDamMay(null);
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final c = luuTru.damMay;
    String h(int n) => n.toString().padLeft(2, '0');
    final cuoi = damMay.lanGuiCuoi;
    return ListView(padding: const EdgeInsets.all(16), children: [
      const Text('Gửi số đo và cảnh báo lên Firebase để người thân xem trên web. '
          'Cách tạo Firebase và lấy các thông tin dưới đây: web/README.md trong repo.'),
      const SizedBox(height: 16),
      if (c != null && c.daDangNhap) ...[
        Card(
          color: damMay.loi == null ? Colors.green.shade50 : Colors.orange.shade50,
          child: ListTile(
            leading: Icon(damMay.loi == null ? Icons.cloud_done : Icons.cloud_off,
                color: damMay.loi == null ? Colors.green : Colors.orange, size: 36),
            title: Text('Đã đăng nhập: ${c.email}'),
            subtitle: Text([
              if (cuoi != null) 'Lần gửi cuối: ${h(cuoi.hour)}:${h(cuoi.minute)}:${h(cuoi.second)}',
              if (cuoi == null) 'Chưa gửi gì (chờ đồng hồ kết nối)',
              if (damMay.loi != null) damMay.loi!,
            ].join('\n')),
          ),
        ),
        const SizedBox(height: 8),
        OutlinedButton(onPressed: _dangXuat, child: const Text('Đăng xuất (ngừng gửi lên web)')),
      ] else ...[
        TextField(
          controller: _apiKey,
          decoration: const InputDecoration(labelText: 'Web API key', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _dbUrl,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(
            labelText: 'Địa chỉ Realtime Database',
            hintText: 'https://...firebasedatabase.app',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(labelText: 'Email tài khoản gia đình', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _matKhau,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Mật khẩu', border: OutlineInputBorder()),
        ),
        if (_loi != null) ...[
          const SizedBox(height: 8),
          Text(_loi!, style: const TextStyle(color: Colors.red)),
        ],
        const SizedBox(height: 16),
        FilledButton(
          onPressed: _dangChay ? null : _dangNhap,
          child: Text(_dangChay ? 'Đang đăng nhập...' : 'Đăng nhập và bắt đầu gửi'),
        ),
        const SizedBox(height: 8),
        const Text('App chỉ lưu mã đăng nhập, không lưu mật khẩu. Người thân dùng cùng email '
            'và mật khẩu này để đăng nhập trên web.'),
      ],
    ]);
  }
}
