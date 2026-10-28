// Man hinh do dien tim (ECG) 30 giay: huong dan dat dien cuc, song chay truc tiep,
// ket qua nhip tim, 6 dai song 5 giay tren nen giay ECG va danh sach cac lan do da luu.
import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'do_ecg.dart';
import 'dong_ho.dart';
import 'ecg.dart';
import 'giao_thuc.dart';
import 'luu_tru.dart';

final _boNhoKetQua = Expando<KetQuaEcg>();

/// Ket qua phan tich cua mot ban ghi (tinh mot lan roi giu lai).
KetQuaEcg ketQuaCua(BanGhiEcg e) => _boNhoKetQua[e] ??= phanTichEcg(e.mau);

String _ngayGio(DateTime t) {
  String h(int n) => n.toString().padLeft(2, '0');
  return '${h(t.hour)}:${h(t.minute)} ${h(t.day)}/${h(t.month)}/${t.year}';
}

class ManHinhEcg extends StatefulWidget {
  final DoEcg doEcg;
  final DongHo dongHo;
  final LuuTru luuTru;
  const ManHinhEcg({super.key, required this.doEcg, required this.dongHo, required this.luuTru});

  @override
  State<ManHinhEcg> createState() => _ManHinhEcgState();
}

class _ManHinhEcgState extends State<ManHinhEcg> {
  late final Listenable _nghe = Listenable.merge([widget.doEcg, widget.dongHo, widget.luuTru]);

  @override
  void dispose() {
    widget.doEcg.dung(); // roi man hinh giua chung thi bao dong ho dung
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final d = widget.doEcg;
    return Scaffold(
      appBar: AppBar(title: const Text('Điện tim (ECG) 30 giây')),
      body: ListenableBuilder(
        listenable: _nghe,
        builder: (context, _) => ListView(padding: const EdgeInsets.all(16), children: [
          if (d.trangThai != TrangThaiEcg.dangDo) const _HuongDan(),
          const SizedBox(height: 8),
          _nutDo(context, d),
          if (d.trangThai == TrangThaiEcg.dangDo) ..._dangDo(context, d),
          if (d.trangThai == TrangThaiEcg.loi)
            Card(
              color: Colors.red.shade50,
              child: ListTile(
                leading: const Icon(Icons.error_outline, color: Colors.red),
                title: Text(d.loi ?? 'Lỗi'),
              ),
            ),
          if (d.trangThai == TrangThaiEcg.xong && d.banGhi != null) ...[
            const SizedBox(height: 12),
            Text('Kết quả vừa đo', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            KetQuaBanGhi(banGhi: d.banGhi!),
          ],
          const SizedBox(height: 16),
          _danhSach(context),
          const SizedBox(height: 8),
          Text(
            'Chỉ để theo dõi, không dùng để chẩn đoán bệnh tim. '
            'Nhịp tim tính từ khoảng cách giữa các đỉnh R.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ]),
      ),
    );
  }

  Widget _nutDo(BuildContext context, DoEcg d) {
    if (d.trangThai == TrangThaiEcg.dangDo) {
      return OutlinedButton.icon(
        onPressed: d.dung,
        icon: const Icon(Icons.stop),
        label: const Text('Dừng đo'),
      );
    }
    final ketNoi = widget.dongHo.trangThai == TrangThai.daKetNoi;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      FilledButton.icon(
        onPressed: widget.dongHo.coEcg ? d.batDau : null,
        icon: const Icon(Icons.monitor_heart),
        label: Text(d.trangThai == TrangThaiEcg.chuaDo ? 'Đo ECG 30 giây' : 'Đo lại'),
      ),
      if (!ketNoi)
        const Padding(
          padding: EdgeInsets.only(top: 4),
          child: Text('Chưa kết nối đồng hồ.', textAlign: TextAlign.center),
        )
      else if (!widget.dongHo.coEcg)
        const Padding(
          padding: EdgeInsets.only(top: 4),
          child: Text('Firmware đồng hồ chưa có ECG: hãy nạp bản ble_suc_khoe mới.',
              textAlign: TextAlign.center),
        ),
    ]);
  }

  List<Widget> _dangDo(BuildContext context, DoEcg d) {
    // Loc 6 giay cuoi roi ve 5 giay cuoi (bo 1 giay dau de bo loc on dinh)
    final tu = math.max(0, d.mau.length - 6 * tanSoEcg);
    final loc = locEcg(d.mau.sublist(tu));
    final hien = loc.length > 5 * tanSoEcg ? loc.sublist(loc.length - 5 * tanSoEcg) : loc;
    return [
      const SizedBox(height: 12),
      LinearProgressIndicator(value: d.tienDo, minHeight: 8),
      const SizedBox(height: 4),
      Text('Đang đo: ${d.soGiay}/$soGiayEcg giây. Ngồi yên, không nói chuyện.',
          textAlign: TextAlign.center),
      const SizedBox(height: 8),
      if (d.dangTuot)
        Card(
          color: Colors.orange.shade100,
          child: const ListTile(
            leading: Icon(Icons.warning_amber, color: Colors.deepOrange),
            title: Text('Điện cực bị tuột hoặc ngón tay chưa chạm'),
            subtitle: Text('Kiểm tra lại 3 điện cực / chạm ngón tay vào điện cực đồng hồ.'),
          ),
        ),
      DaiEcg(song: hien, soGiay: 5, cao: 180),
    ];
  }

  Widget _danhSach(BuildContext context) {
    final ds = widget.luuTru.dsEcg;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Text('Các lần đo đã lưu (${ds.length}/${LuuTru.soEcgToiDa})',
          style: Theme.of(context).textTheme.titleMedium),
      if (ds.isEmpty) const Card(child: ListTile(title: Text('Chưa có lần đo nào.'))),
      for (final e in ds)
        Card(
          child: ListTile(
            leading: const Icon(Icons.monitor_heart, color: Colors.red),
            title: Text(_ngayGio(e.luc)),
            subtitle: Text(_tomTat(e)),
            trailing: IconButton(
              icon: const Icon(Icons.delete_outline),
              onPressed: () => _xoa(context, e),
            ),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => Scaffold(
                appBar: AppBar(title: Text('ECG ${_ngayGio(e.luc)}')),
                body: ListView(padding: const EdgeInsets.all(16), children: [KetQuaBanGhi(banGhi: e)]),
              ),
            )),
          ),
        ),
    ]);
  }

  String _tomTat(BanGhiEcg e) {
    final k = ketQuaCua(e);
    return [
      k.nhipTb == null ? 'Không tính được nhịp' : 'Nhịp TB ${k.nhipTb} l/p',
      '${e.mau.length ~/ tanSoEcg} giây',
      if (e.coTuotDienCuc) 'có lúc tuột điện cực',
    ].join(' · ');
  }

  Future<void> _xoa(BuildContext context, BanGhiEcg e) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Xóa lần đo này?'),
        content: Text(_ngayGio(e.luc)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Không')),
          FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Xóa')),
        ],
      ),
    );
    if (ok == true) await widget.luuTru.xoaEcg(e);
  }
}

class _HuongDan extends StatelessWidget {
  const _HuongDan();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Cách đo', style: TextStyle(fontWeight: FontWeight.bold)),
          SizedBox(height: 4),
          Text('Đồng hồ hoàn chỉnh: đeo ở tay trái, dùng một ngón tay phải chạm và giữ vào vít kim loại '
              'ở mép đồng hồ (điện cực RA).'),
          SizedBox(height: 4),
          Text('Dùng cáp 3 dây (breadboard): dán 3 miếng điện cực, dây đỏ (RA) ngực phải, '
              'dây xanh lá (LA) ngực trái, dây vàng (RL) bụng dưới bên phải.'),
          SizedBox(height: 4),
          Text('Ngồi yên, thả lỏng tay, không nói chuyện trong 30 giây.'),
        ]),
      ),
    );
  }
}

/// Ket qua cua mot lan do: nhip tim, canh bao, 6 dai song 5 giay co danh dau dinh R.
class KetQuaBanGhi extends StatelessWidget {
  final BanGhiEcg banGhi;
  const KetQuaBanGhi({super.key, required this.banGhi});

  @override
  Widget build(BuildContext context) {
    final k = ketQuaCua(banGhi);
    final n = k.daLoc.length;
    const moiDai = 5 * tanSoEcg;
    final bienDo = _bienDo(k.daLoc);
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Row(children: [
        _So('Nhịp TB', k.nhipTb),
        _So('Thấp nhất', k.nhipThapNhat),
        _So('Cao nhất', k.nhipCaoNhat),
      ]),
      Text('${k.dinhR.length} nhịp trong ${(n / tanSoEcg).toStringAsFixed(0)} giây',
          textAlign: TextAlign.center),
      if (k.nhipTb == null)
        const _CanhBao('Không tìm được đủ đỉnh R. Kiểm tra điện cực rồi đo lại.'),
      if (banGhi.coTuotDienCuc) const _CanhBao('Có lúc điện cực bị tuột, đoạn sóng đó không tin được.'),
      if (banGhi.soMauThieu > tanSoEcg ~/ 2)
        _CanhBao('Thiếu ${(banGhi.soMauThieu / tanSoEcg).toStringAsFixed(1)} giây dữ liệu do Bluetooth.'),
      const SizedBox(height: 8),
      for (var a = 0; a < n; a += moiDai)
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${a ~/ tanSoEcg}–${math.min(n, a + moiDai) ~/ tanSoEcg} giây',
                style: Theme.of(context).textTheme.bodySmall),
            DaiEcg(
              song: k.daLoc.sublist(a, math.min(n, a + moiDai)),
              soGiay: 5,
              cao: 120,
              bienDo: bienDo,
              dinh: [for (final r in k.dinhR) if (r >= a && r < a + moiDai) r - a],
            ),
          ]),
        ),
    ]);
  }
}

/// Bien do de chia truc dung: phan vi 99 cua |song|, de vai mau nhieu khong lam song be lai.
double _bienDo(List<double> y) {
  if (y.isEmpty) return 1;
  final a = [for (final v in y) v.abs()]..sort();
  return math.max(a[(0.99 * (a.length - 1)).floor()], 1);
}

class _So extends StatelessWidget {
  final String ten;
  final int? giaTri;
  const _So(this.ten, this.giaTri);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Column(children: [
            Text(ten),
            Text(giaTri?.toString() ?? '--',
                style: const TextStyle(fontSize: 30, fontWeight: FontWeight.bold)),
            const Text('lần/phút', style: TextStyle(fontSize: 12)),
          ]),
        ),
      ),
    );
  }
}

class _CanhBao extends StatelessWidget {
  final String noiDung;
  const _CanhBao(this.noiDung);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(children: [
        const Icon(Icons.warning_amber, color: Colors.deepOrange, size: 20),
        const SizedBox(width: 6),
        Expanded(child: Text(noiDung)),
      ]),
    );
  }
}

/// Mot dai song ECG [soGiay] giay tren nen giay ECG (o nho 0,04 giay, o lon 0,2 giay).
class DaiEcg extends StatelessWidget {
  final List<double> song;
  final int soGiay;
  final double cao;
  final double? bienDo; // null: tu tinh theo dai nay
  final List<int> dinh;
  const DaiEcg({
    super.key,
    required this.song,
    required this.soGiay,
    required this.cao,
    this.bienDo,
    this.dinh = const [],
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: cao,
      decoration: BoxDecoration(border: Border.all(color: const Color(0xFFE8A0A0))),
      child: CustomPaint(
        size: Size.infinite,
        painter: _VeEcg(song, soGiay, bienDo ?? _bienDo(song), dinh),
      ),
    );
  }
}

class _VeEcg extends CustomPainter {
  final List<double> song;
  final int soGiay;
  final double bienDo;
  final List<int> dinh;
  _VeEcg(this.song, this.soGiay, this.bienDo, this.dinh);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFFFFF5F5));
    final pxGiay = w / soGiay;
    final o = pxGiay * 0.04; // o nho 0,04 giay; o vuong ca chieu dung
    final nho = Paint()
      ..color = const Color(0xFFF6CFCF)
      ..strokeWidth = 0.5;
    final lon = Paint()
      ..color = const Color(0xFFE8A0A0)
      ..strokeWidth = 1;
    var i = 0;
    for (var x = 0.0; x <= w + 0.1; x += o, i++) {
      canvas.drawLine(Offset(x, 0), Offset(x, h), i % 5 == 0 ? lon : nho);
    }
    i = 0;
    for (var y = h / 2; y >= 0; y -= o, i++) {
      canvas.drawLine(Offset(0, y), Offset(w, y), i % 5 == 0 ? lon : nho);
    }
    i = 1;
    for (var y = h / 2 + o; y <= h; y += o, i++) {
      canvas.drawLine(Offset(0, y), Offset(w, y), i % 5 == 0 ? lon : nho);
    }
    if (song.length < 2) return;

    final pxMau = pxGiay / tanSoEcg;
    final k = (h / 2 - 6) / (bienDo * 1.15);
    double yCua(double v) => (h / 2 - v * k).clamp(1, h - 1).toDouble();
    final duong = Path()..moveTo(0, yCua(song[0]));
    for (var j = 1; j < song.length; j++) {
      duong.lineTo(j * pxMau, yCua(song[j]));
    }
    canvas.drawPath(
      duong,
      Paint()
        ..color = Colors.black
        ..strokeWidth = 1.3
        ..style = PaintingStyle.stroke
        ..strokeJoin = StrokeJoin.round,
    );
    final cham = Paint()..color = Colors.red;
    for (final r in dinh) {
      if (r < song.length) canvas.drawCircle(Offset(r * pxMau, yCua(song[r])), 3, cham);
    }
  }

  @override
  bool shouldRepaint(_VeEcg c) =>
      !identical(c.song, song) || c.bienDo != bienDo || c.soGiay != soGiay || !identical(c.dinh, dinh);
}
