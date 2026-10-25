import { test } from 'node:test'
import assert from 'node:assert/strict'
import { tinhTrang, thanhMang, lienKetBanDo, PHUT } from './tinhTrang.js'

const now = new Date(2026, 9, 25, 9, 30).getTime()
const hienTai = { ketNoi: true, dangDeo: true, luc: now - 20000, nhipTim: 72 }

test('on dinh', () => {
  assert.equal(tinhTrang(hienTai, [], 'Bà Hằng', now).muc, 'onDinh')
  assert.equal(tinhTrang(hienTai, [], 'Bà Hằng', now).tieuDe, 'Bà Hằng đang ổn')
})

test('canh bao khan cap trong 1 gio dung dau', () => {
  const cb = [{ luc: now - 10 * PHUT, ten: 'Té ngã', khanCap: true, soTinDaGui: 2 }]
  const t = tinhTrang(null, cb, 'Bà Hằng', now)
  assert.equal(t.muc, 'khanCap')
  assert.equal(t.tieuDe, 'Bà Hằng: té ngã lúc 09:20')
  assert.match(t.phu, /2 người/)
})

test('canh bao cu hon 1 gio khong tinh', () => {
  const cb = [{ luc: now - 61 * PHUT, ten: 'SOS', khanCap: true, soTinDaGui: 1 }]
  assert.equal(tinhTrang(hienTai, cb, '', now).muc, 'onDinh')
})

test('mat lien lac khi qua 5 phut hoac dong ho mat ket noi', () => {
  assert.equal(tinhTrang({ ...hienTai, luc: now - 6 * PHUT }, [], '', now).muc, 'matLienLac')
  const t = tinhTrang({ ...hienTai, ketNoi: false }, [], '', now)
  assert.equal(t.muc, 'matLienLac')
  assert.match(t.phu, /Đồng hồ không kết nối/)
})

test('chua deo va can chu y', () => {
  assert.equal(tinhTrang({ ...hienTai, dangDeo: false }, [], '', now).muc, 'chuaDeo')
  const cb = [{ luc: now - 5 * PHUT, ten: 'Nhịp tim cao', khanCap: false, moTa: '135 lan/phut' }]
  assert.equal(tinhTrang(hienTai, cb, 'Ông', now).tieuDe, 'Ông: nhịp tim cao lúc 09:25')
})

test('thanh mang sap xep va bo muc hong', () => {
  const m = thanhMang({ b: { luc: 2 }, a: { luc: 1 }, x: null, y: { khong: 1 } })
  assert.deepEqual(m.map((x) => x.luc), [1, 2])
  assert.deepEqual(thanhMang({ a: { luc: 1 }, b: { luc: 2 } }, true).map((x) => x.luc), [2, 1])
})

test('lien ket ban do', () => {
  assert.equal(lienKetBanDo({ viDo: 21.03, kinhDo: 105.85 }), 'https://maps.google.com/?q=21.03,105.85')
  assert.equal(lienKetBanDo({ viDo: null }), null)
})
