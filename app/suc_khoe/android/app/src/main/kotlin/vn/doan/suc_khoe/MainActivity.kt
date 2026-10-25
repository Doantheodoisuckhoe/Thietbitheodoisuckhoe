package vn.doan.suc_khoe

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.telephony.SmsManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

// Gui SMS va goi dien bang API Android (Flutter khong co san).
// Dart goi qua kenh "suc_khoe/dien_thoai", xem lib/dich_vu_dien_thoai.dart.
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "suc_khoe/dien_thoai")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "guiSms" -> {
                        val so = call.argument<String>("so")
                        val noiDung = call.argument<String>("noiDung")
                        if (so.isNullOrBlank() || noiDung.isNullOrEmpty()) {
                            result.success(false)
                        } else {
                            result.success(guiSms(so, noiDung))
                        }
                    }
                    "goiDien" -> {
                        val so = call.argument<String>("so")
                        if (so.isNullOrBlank()) {
                            result.success(false)
                        } else {
                            try {
                                val i = Intent(Intent.ACTION_CALL, Uri.parse("tel:$so"))
                                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                startActivity(i)
                                result.success(true)
                            } catch (e: Exception) {
                                result.success(false)
                            }
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun guiSms(so: String, noiDung: String): Boolean {
        return try {
            val sms: SmsManager = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                getSystemService(SmsManager::class.java)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getDefault()
            }
            val cacPhan = sms.divideMessage(noiDung)
            sms.sendMultipartTextMessage(so, null, cacPhan, null, null)
            true
        } catch (e: Exception) {
            false
        }
    }
}
