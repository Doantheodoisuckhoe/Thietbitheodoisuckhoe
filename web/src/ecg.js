// Xu ly song ECG cho trang web: giai ma mau tu Firebase va loc giong app (app/suc_khoe/lib/ecg.dart).
// Khong phu thuoc React de test bang node --test.

export const TAN_SO_ECG = 250

/** base64 cua uint16 little-endian -> mang so (ADC 12 bit). */
export function giaiMaMau(b64) {
  if (!b64) return []
  const chuoi = atob(b64)
  const kq = new Array(chuoi.length >> 1)
  for (let i = 0; i < kq.length; i++) kq[i] = chuoi.charCodeAt(2 * i) | (chuoi.charCodeAt(2 * i + 1) << 8)
  return kq
}

/** Trung binh truot can giua, cua so w mau (le); o hai dau cua so tu thu nho. */
export function trungBinhTruot(x, w) {
  const n = x.length
  const h = w >> 1
  const tong = new Float64Array(n + 1)
  for (let i = 0; i < n; i++) tong[i + 1] = tong[i] + x[i]
  const kq = new Array(n)
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - h)
    const b = Math.min(n, i + h + 1)
    kq[i] = (tong[b] - tong[a]) / (b - a)
  }
  return kq
}

/** Trung binh 5 mau (20 ms) triet nhieu 50 Hz, tru trung binh 0,6 giay de bo troi nen. */
export function locEcg(mau) {
  const s = trungBinhTruot(mau, 5)
  const nen = trungBinhTruot(s, 151)
  return s.map((v, i) => v - nen[i])
}

/** Bien do de ve: 98% gia tri tuyet doi, toi thieu 1 de khong chia cho 0. */
export function bienDo(y) {
  if (y.length === 0) return 1
  const a = y.map(Math.abs).sort((p, q) => p - q)
  return Math.max(1, a[Math.floor(0.98 * (a.length - 1))])
}

/** Chuoi CSV de bac si tai ve: thoi gian (ms) va gia tri ADC goc. */
export function thanhCsv(mau, tanSo = TAN_SO_ECG) {
  const dong = ['t_ms,adc']
  mau.forEach((v, i) => dong.push(`${Math.round((i * 1000) / tanSo)},${v}`))
  return dong.join('\n') + '\n'
}

/** Song ECG gia (P-QRS-T + troi nen + nhieu 50 Hz) cho che do demo, giong test cua app. */
export function taoSongGia(bpm, giay = 30) {
  const t0 = 60 / bpm
  const g = (ph, tam, rong) => Math.exp(-(((ph - tam) / rong) ** 2))
  const x = []
  let hat = 1
  const ngauNhien = () => ((hat = (hat * 16807) % 2147483647) / 2147483647)
  for (let i = 0; i < giay * TAN_SO_ECG; i++) {
    const t = i / TAN_SO_ECG
    const ph = t % t0
    const v = 0.12 * g(ph, 0.15, 0.03) - 0.1 * g(ph, 0.26, 0.008) + g(ph, 0.28, 0.01) -
      0.25 * g(ph, 0.3, 0.01) + 0.3 * g(ph, 0.5, 0.05) +
      0.6 * Math.sin(2 * Math.PI * 0.3 * t) + 0.15 * Math.sin(2 * Math.PI * 50 * t) + (ngauNhien() - 0.5) * 0.12
    x.push(Math.round(1900 + 300 * v))
  }
  return x
}

/** Ma hoa nguoc lai (dung cho demo va test). */
export function maHoaMau(mau) {
  let s = ''
  for (const v of mau) s += String.fromCharCode(v & 0xff, (v >> 8) & 0xff)
  return btoa(s)
}

/** Vi tri dinh R cua song gia taoSongGia (dinh R o pha 0,28 giay moi nhip). */
export function dinhRGia(bpm, giay = 30) {
  const t0 = 60 / bpm
  const kq = []
  for (let t = 0.28; t < giay; t += t0) kq.push(Math.round(t * TAN_SO_ECG))
  return kq
}

/** Chia song thanh cac dai dai `giay` giay de ve nhu giay ECG. Moi dai: {batDau, y: [...], dinhR: [chi so trong dai]}. */
export function chiaDai(y, dinhR = [], giay = 5, tanSo = TAN_SO_ECG) {
  const n = giay * tanSo
  const kq = []
  for (let a = 0; a < y.length; a += n) {
    kq.push({ batDau: a, y: y.slice(a, a + n), dinhR: dinhR.filter((r) => r >= a && r < a + n).map((r) => r - a) })
  }
  return kq
}

/** Ten file CSV theo thoi diem do, vi du ecg_20261030_0905.csv */
export function tenFileCsv(luc) {
  const d = new Date(luc)
  const h = (n) => String(n).padStart(2, '0')
  return `ecg_${d.getFullYear()}${h(d.getMonth() + 1)}${h(d.getDate())}_${h(d.getHours())}${h(d.getMinutes())}.csv`
}
