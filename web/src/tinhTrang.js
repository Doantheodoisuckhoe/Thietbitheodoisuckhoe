// Tinh trang thai tong quat de hien o dau trang. Khong phu thuoc React de test bang node --test.

export const PHUT = 60 * 1000

export function gio(ms) {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export function ngayGio(ms, bayGio = Date.now()) {
  const d = new Date(ms)
  const homNay = new Date(bayGio)
  const cungNgay = d.toDateString() === homNay.toDateString()
  const homQua = new Date(bayGio - 24 * 60 * PHUT).toDateString() === d.toDateString()
  if (cungNgay) return `${gio(ms)} hôm nay`
  if (homQua) return `${gio(ms)} hôm qua`
  return `${gio(ms)} ${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
}

/**
 * @param {object|null} hienTai  /nguoiDung/{uid}/hienTai
 * @param {object[]} canhBao     danh sach canh bao, moi nhat truoc
 * @param {string} ten           ten nguoi deo
 * @returns {{muc: string, tieuDe: string, phu: string}}
 *   muc: khanCap | canChuY | matLienLac | chuaDeo | onDinh | chuaCo
 */
export function tinhTrang(hienTai, canhBao, ten, bayGio = Date.now()) {
  const nguoi = ten?.trim() || 'Người thân'
  const ganDay = canhBao.filter((c) => bayGio - c.luc < 60 * PHUT)
  const khanCap = ganDay.find((c) => c.khanCap)
  if (khanCap) {
    return {
      muc: 'khanCap',
      tieuDe: `${nguoi}: ${khanCap.ten.toLowerCase()} lúc ${gio(khanCap.luc)}`,
      phu: khanCap.soTinDaGui > 0
        ? `Đã gửi SMS cho ${khanCap.soTinDaGui} người. Hãy gọi điện kiểm tra ngay.`
        : 'Chưa gửi được SMS. Hãy gọi điện kiểm tra ngay.',
    }
  }
  if (!hienTai) {
    return { muc: 'chuaCo', tieuDe: 'Chưa có dữ liệu', phu: 'App trên điện thoại người đeo chưa gửi số đo nào lên.' }
  }
  if (!hienTai.ketNoi || bayGio - hienTai.luc > 5 * PHUT) {
    return {
      muc: 'matLienLac',
      tieuDe: `Mất liên lạc từ ${ngayGio(hienTai.luc, bayGio)}`,
      phu: hienTai.ketNoi
        ? 'Điện thoại của người đeo không gửi dữ liệu lên (tắt máy, hết pin hoặc mất mạng).'
        : 'Đồng hồ không kết nối với điện thoại (ở xa điện thoại hoặc hết pin).',
    }
  }
  if (!hienTai.dangDeo) {
    return { muc: 'chuaDeo', tieuDe: `${nguoi} đang không đeo đồng hồ`, phu: 'Đồng hồ vẫn kết nối nhưng không chạm da.' }
  }
  const chuY = ganDay[0]
  if (chuY) {
    return {
      muc: 'canChuY',
      tieuDe: `${nguoi}: ${chuY.ten.toLowerCase()} lúc ${gio(chuY.luc)}`,
      phu: chuY.moTa ? `Giá trị lúc báo: ${chuY.moTa}.` : '',
    }
  }
  return { muc: 'onDinh', tieuDe: `${nguoi} đang ổn`, phu: `Cập nhật lúc ${gio(hienTai.luc)}.` }
}

/** Doi object {khoa: diem} cua Firebase thanh mang sap xep theo thoi gian. */
export function thanhMang(obj, giamDan = false) {
  const ds = Object.values(obj || {}).filter((x) => x && typeof x.luc === 'number')
  ds.sort((a, b) => (giamDan ? b.luc - a.luc : a.luc - b.luc))
  return ds
}

export function lienKetBanDo(c) {
  if (c.viDo == null || c.kinhDo == null) return null
  return `https://maps.google.com/?q=${c.viDo},${c.kinhDo}`
}
