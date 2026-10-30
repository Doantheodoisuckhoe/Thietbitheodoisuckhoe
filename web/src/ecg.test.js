import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  bienDo, chiaDai, dinhRGia, giaiMaMau, locEcg, maHoaMau, taoSongGia, tenFileCsv, thanhCsv, trungBinhTruot,
} from './ecg.js'

test('giai ma uint16 little-endian giong app', () => {
  // Cung du lieu voi test cua app: [0, 1, 256, 4095] -> 00 00 01 00 00 01 FF 0F
  assert.deepEqual(giaiMaMau(btoa('\x00\x00\x01\x00\x00\x01\xff\x0f')), [0, 1, 256, 4095])
  assert.deepEqual(giaiMaMau(maHoaMau([5, 2048, 4000])), [5, 2048, 4000])
  assert.deepEqual(giaiMaMau(''), [])
})

test('trung binh truot thu nho o hai dau', () => {
  assert.deepEqual(trungBinhTruot([1, 2, 3, 4, 5], 3), [1.5, 2, 3, 4, 4.5])
})

test('loc bo troi nen va 50 Hz', () => {
  const y = locEcg(taoSongGia(72))
  const tb = y.reduce((a, b) => a + b, 0) / y.length
  assert.ok(Math.abs(tb) < 5, `trung binh sau loc ${tb}`)
  assert.ok(bienDo(y) > 100)
})

test('CSV co thoi gian theo ms', () => {
  assert.equal(thanhCsv([10, 20, 30]), 't_ms,adc\n0,10\n4,20\n8,30\n')
})

test('chia 30 giay thanh 6 dai 5 giay, dinh R theo dai', () => {
  const y = locEcg(taoSongGia(60))
  const r = dinhRGia(60)
  assert.equal(r.length, 30)
  const dai = chiaDai(y, r)
  assert.equal(dai.length, 6)
  assert.equal(dai[5].batDau, 6250)
  assert.ok(dai.every((d) => d.y.length === 1250 && d.dinhR.length === 5))
  assert.deepEqual(dai[1].dinhR, [70, 320, 570, 820, 1070])
  // Dinh R gia nam dung dinh song da loc.
  for (const i of r) assert.ok(y[i] > 0.5 * bienDo(y), `mau ${i}`)
})

test('ten file CSV theo gio may', () => {
  assert.equal(tenFileCsv(new Date(2026, 9, 30, 9, 5).getTime()), 'ecg_20261030_0905.csv')
})
