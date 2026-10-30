// Lay du lieu tu Firebase Realtime Database, hoac du lieu gia khi chua cau hinh (che do demo).
import { initializeApp } from 'firebase/app'
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'firebase/auth'
import { get, getDatabase, limitToLast, onValue, orderByChild, query, ref, startAt } from 'firebase/database'
import { cauHinhFirebase } from './cauHinhFirebase.js'
import { thanhMang, PHUT } from './tinhTrang.js'
import { dinhRGia, maHoaMau, taoSongGia, TAN_SO_ECG } from './ecg.js'

export const cheDoDemo = !cauHinhFirebase.apiKey || new URLSearchParams(location.search).has('demo')

let auth = null
let db = null
if (!cheDoDemo) {
  const app = initializeApp(cauHinhFirebase)
  auth = getAuth(app)
  db = getDatabase(app)
}

export function theoDoiDangNhap(cb) {
  if (cheDoDemo) {
    cb({ uid: 'demo', email: 'demo@vi-du.vn' })
    return () => {}
  }
  return onAuthStateChanged(auth, cb)
}

const LOI = {
  'auth/invalid-credential': 'Sai email hoặc mật khẩu.',
  'auth/invalid-email': 'Email chưa đúng định dạng.',
  'auth/too-many-requests': 'Thử sai quá nhiều lần. Đợi vài phút rồi thử lại.',
  'auth/network-request-failed': 'Không kết nối được mạng.',
  'auth/api-key-not-valid.-please-pass-a-valid-api-key.': 'Cấu hình Firebase sai apiKey (web/src/cauHinhFirebase.js).',
  'auth/operation-not-allowed': 'Chưa bật đăng nhập Email/Password trong Firebase.',
}

export async function dangNhap(email, matKhau) {
  try {
    await signInWithEmailAndPassword(auth, email.trim(), matKhau)
  } catch (e) {
    throw new Error(LOI[e.code] || `Không đăng nhập được (${e.code || e.message}).`)
  }
}

export const dangXuat = () => (cheDoDemo ? Promise.resolve() : signOut(auth))

/**
 * Nghe du lieu cua mot tai khoan. Goi capNhat({thongTin, hienTai, soDo, canhBao, ecg, loi}) moi khi doi.
 * soDo: 24 gio gan nhat, cu truoc. canhBao: 50 canh bao gan nhat, moi truoc.
 * ecg: tom tat 20 lan do ECG gan nhat, moi truoc (song tai rieng bang taiSongEcg khi bam xem).
 */
export function theoDoiDuLieu(uid, capNhat) {
  if (cheDoDemo) return theoDoiDemo(capNhat)
  const trangThai = { thongTin: null, hienTai: null, soDo: [], canhBao: [], ecg: [], loi: null, daTai: false }
  const goc = `nguoiDung/${uid}`
  const loi = (e) => capNhat({ ...Object.assign(trangThai, { loi: `Không đọc được dữ liệu: ${e.message}` }) })
  const nghe = (q, gan) =>
    onValue(q, (s) => {
      gan(s.val())
      trangThai.daTai = true
      capNhat({ ...trangThai })
    }, loi)

  const huy = [
    nghe(ref(db, `${goc}/thongTin`), (v) => (trangThai.thongTin = v)),
    nghe(ref(db, `${goc}/hienTai`), (v) => (trangThai.hienTai = v)),
    nghe(query(ref(db, `${goc}/soDo`), orderByChild('luc'), startAt(Date.now() - 24 * 60 * PHUT)),
      (v) => (trangThai.soDo = thanhMang(v))),
    nghe(query(ref(db, `${goc}/canhBao`), orderByChild('luc'), limitToLast(50)),
      (v) => (trangThai.canhBao = thanhMang(v, true))),
    nghe(query(ref(db, `${goc}/ecg`), orderByChild('luc'), limitToLast(20)),
      (v) => (trangThai.ecg = thanhMang(v, true))),
  ]
  return () => huy.forEach((h) => h())
}

/** Tai song cua 1 lan do ECG: {luc, tanSo, mau (base64 uint16 LE), dinhR}. Tra null neu khong co. */
export async function taiSongEcg(uid, luc) {
  if (cheDoDemo) {
    const e = ECG_DEMO.find((x) => x.luc === luc) || ECG_DEMO[0]
    return { luc, tanSo: TAN_SO_ECG, mau: maHoaMau(taoSongGia(e.nhipTb, e.soGiay)), dinhR: dinhRGia(e.nhipTb, e.soGiay) }
  }
  const s = await get(ref(db, `nguoiDung/${uid}/ecgSong/${luc}`))
  return s.val()
}

// ---------- Che do demo ----------
// Moc demo co dinh (khong doi moi 10 giay) de khi bam xem 1 lan do thi danh sach khong nhay.
const MOC_DEMO = Date.now()
const ECG_DEMO = [
  { luc: MOC_DEMO - 2 * 60 * PHUT, soGiay: 30, nhipTb: 76, nhipThapNhat: 72, nhipCaoNhat: 81, soNhip: 38, coTuotDienCuc: false, soMauThieu: 0 },
  { luc: MOC_DEMO - 27 * 60 * PHUT, soGiay: 30, nhipTb: 64, nhipThapNhat: 60, nhipCaoNhat: 69, soNhip: 32, coTuotDienCuc: false, soMauThieu: 0 },
  { luc: MOC_DEMO - 3 * 24 * 60 * PHUT, soGiay: 30, nhipTb: 88, nhipThapNhat: 82, nhipCaoNhat: 95, soNhip: 44, coTuotDienCuc: true, soMauThieu: 12 },
]

function taoDemo(bayGio) {
  const soDo = []
  const batDau = bayGio - 24 * 60 * PHUT
  for (let t = batDau; t <= bayGio; t += PHUT) {
    const gioTrongNgay = new Date(t).getHours() + new Date(t).getMinutes() / 60
    const ngu = gioTrongNgay < 6 || gioTrongNgay > 22
    // Bo 1 khoang thao dong ho luc tam (19:00-19:40).
    if (gioTrongNgay >= 19 && gioTrongNgay < 19.67) continue
    const nhieu = Math.sin(t / 7e5) * 3 + Math.sin(t / 1.3e5) * 2
    soDo.push({
      luc: t,
      nhipTim: Math.round((ngu ? 58 : 74) + nhieu),
      spo2: Math.round(96.5 + Math.sin(t / 2e6)),
      nhietDo: Math.round((ngu ? 33.8 : 33.1) * 10 + Math.sin(t / 3e6) * 4) / 10,
    })
  }
  const cuoi = soDo[soDo.length - 1]
  return {
    thongTin: { tenNguoiDeo: 'Bà Nguyễn Thị Hằng' },
    hienTai: { ...cuoi, pinPhanTram: 64, dangDeo: true, ketNoi: true, luc: bayGio - 8000 },
    soDo,
    canhBao: [
      ...(new URLSearchParams(location.search).get('demo') === 'nga'
        ? [{ luc: bayGio - 3 * PHUT, ma: 2, ten: 'Té ngã', khanCap: true, moTa: '', soTinDaGui: 2, soNguoiThan: 2, viDo: 21.02851, kinhDo: 105.85423 }]
        : []),
      { luc: bayGio - 26 * 60 * PHUT, ma: 2, ten: 'Té ngã', khanCap: true, moTa: '', soTinDaGui: 2, soNguoiThan: 2, viDo: 21.02851, kinhDo: 105.85423 },
      { luc: bayGio - 30 * 60 * PHUT, ma: 3, ten: 'Nhịp tim cao', khanCap: false, moTa: '128 lan/phut', soTinDaGui: 2, soNguoiThan: 2, viDo: 21.02851, kinhDo: 105.85423 },
      { luc: bayGio - 3 * 24 * 60 * PHUT, ma: 1, ten: 'SOS', khanCap: true, moTa: '', soTinDaGui: 2, soNguoiThan: 2, viDo: null, kinhDo: null },
    ],
    ecg: ECG_DEMO,
    loi: null,
    daTai: true,
  }
}

function theoDoiDemo(capNhat) {
  capNhat(taoDemo(Date.now()))
  const h = setInterval(() => capNhat(taoDemo(Date.now())), 10000)
  return () => clearInterval(h)
}
