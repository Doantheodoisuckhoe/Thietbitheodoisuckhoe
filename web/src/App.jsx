import { useEffect, useMemo, useState } from 'react'
import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { cheDoDemo, dangNhap, dangXuat, taiSongEcg, theoDoiDangNhap, theoDoiDuLieu } from './duLieu.js'
import { bienDo, chiaDai, giaiMaMau, locEcg, tenFileCsv, thanhCsv, TAN_SO_ECG } from './ecg.js'
import { gio, lienKetBanDo, ngayGio, PHUT, tinhTrang } from './tinhTrang.js'

export default function App() {
  const [nguoiDung, setNguoiDung] = useState(undefined) // undefined = dang kiem tra
  useEffect(() => theoDoiDangNhap((u) => setNguoiDung(u)), [])

  if (nguoiDung === undefined) return <div className="cho">Đang tải...</div>
  if (!nguoiDung) return <DangNhap />
  return <BangTheoDoi nguoiDung={nguoiDung} />
}

function DangNhap() {
  const [email, setEmail] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [loi, setLoi] = useState('')
  const [dangChay, setDangChay] = useState(false)

  async function gui(e) {
    e.preventDefault()
    setLoi('')
    setDangChay(true)
    try {
      await dangNhap(email, matKhau)
    } catch (err) {
      setLoi(err.message)
      setDangChay(false)
    }
  }

  return (
    <main className="dang-nhap">
      <h1>Theo dõi sức khỏe người thân</h1>
      <p>Đăng nhập bằng email và mật khẩu gia đình đã nhập trong app trên điện thoại của người đeo đồng hồ.</p>
      <form onSubmit={gui}>
        <label>
          Email
          <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Mật khẩu
          <input type="password" autoComplete="current-password" value={matKhau}
            onChange={(e) => setMatKhau(e.target.value)} required />
        </label>
        {loi && <p className="loi" role="alert">{loi}</p>}
        <button type="submit" disabled={dangChay}>{dangChay ? 'Đang đăng nhập...' : 'Đăng nhập'}</button>
      </form>
    </main>
  )
}

function useBayGio(chuKy = 15000) {
  const [t, setT] = useState(Date.now())
  useEffect(() => {
    const h = setInterval(() => setT(Date.now()), chuKy)
    return () => clearInterval(h)
  }, [chuKy])
  return t
}

function BangTheoDoi({ nguoiDung }) {
  const [d, setD] = useState({ thongTin: null, hienTai: null, soDo: [], canhBao: [], ecg: [], loi: null, daTai: false })
  useEffect(() => theoDoiDuLieu(nguoiDung.uid, setD), [nguoiDung.uid])
  const bayGio = useBayGio()

  const ten = d.thongTin?.tenNguoiDeo || ''
  const tt = tinhTrang(d.hienTai, d.canhBao, ten, bayGio)
  const conHieuLuc = d.hienTai && d.hienTai.ketNoi && d.hienTai.dangDeo && bayGio - d.hienTai.luc < 5 * PHUT

  return (
    <>
      <header className={`dai-trang-thai muc-${tt.muc}`}>
        <div className="khung">
          <div className="thanh-tren">
            <span className="ten-web">Theo dõi sức khỏe</span>
            <span className="tai-khoan">
              {cheDoDemo ? 'Dữ liệu mẫu' : nguoiDung.email}
              {!cheDoDemo && <button className="nut-phu" onClick={dangXuat}>Đăng xuất</button>}
            </span>
          </div>
          <h1 aria-live="polite">{d.daTai ? tt.tieuDe : 'Đang tải dữ liệu...'}</h1>
          {d.daTai && tt.phu && <p className="phu">{tt.phu}</p>}
        </div>
      </header>

      <main className="khung noi-dung">
        {d.loi && <p className="loi" role="alert">{d.loi}</p>}

        <section aria-label="Số đo hiện tại" className="chi-so">
          <ChiSo ten="Nhịp tim" giaTri={conHieuLuc ? d.hienTai.nhipTim : null} donVi="lần/phút" />
          <ChiSo ten="SpO2" giaTri={conHieuLuc ? d.hienTai.spo2 : null} donVi="%" />
          <ChiSo ten="Nhiệt độ da" giaTri={conHieuLuc ? d.hienTai.nhietDo?.toFixed(1) : null} donVi="°C" />
          <ChiSo ten="Pin đồng hồ" giaTri={d.hienTai?.pinPhanTram} donVi="%" />
        </section>

        {cheDoDemo && (
          <p className="bao-demo">
            Đây là dữ liệu mẫu để xem giao diện. Web sẽ hiện dữ liệu thật khi điền cấu hình Firebase
            trong <code>web/src/cauHinhFirebase.js</code>. Thêm <code>?demo=nga</code> vào cuối địa chỉ
            để xem lúc có cảnh báo té ngã.
          </p>
        )}

        <BieuDo soDo={d.soDo} />

        <section className="khoi">
          <h2>Cảnh báo</h2>
          <DanhSachCanhBao canhBao={d.canhBao} bayGio={bayGio} />
        </section>

        <KhoiEcg uid={nguoiDung.uid} ds={d.ecg} bayGio={bayGio} />

        <p className="ghi-chu">
          SpO2 chưa được hiệu chuẩn. Điện tâm đồ là 1 chuyển đạo đo ở hai tay, chưa hiệu chuẩn biên độ theo mV. Nhiệt độ là nhiệt độ da cổ tay, thấp hơn thân nhiệt khoảng 3 đến 4 °C.
          Web chỉ dùng để theo dõi, không thay cho thiết bị y tế.
        </p>
      </main>
    </>
  )
}

function ChiSo({ ten, giaTri, donVi }) {
  const co = giaTri !== null && giaTri !== undefined
  return (
    <div className="o-chi-so">
      <div className="ten-chi-so">{ten}</div>
      <div className="gia-tri">
        {co ? giaTri : '–'}
        {co && <span className="don-vi">{donVi}</span>}
      </div>
    </div>
  )
}

const LOAI_BIEU_DO = [
  { khoa: 'nhipTim', ten: 'Nhịp tim', donVi: 'lần/phút', mien: [40, 140], nguong: [40, 120] },
  { khoa: 'spo2', ten: 'SpO2', donVi: '%', mien: [85, 100], nguong: [90] },
  { khoa: 'nhietDo', ten: 'Nhiệt độ da', donVi: '°C', mien: [30, 39], nguong: [38] },
]

// SVG cua bieu do khong doc duoc bien CSS, nen doc mau tu CSS va doc lai khi doi giao dien sang/toi.
function useMau() {
  const doc = () => {
    const s = getComputedStyle(document.documentElement)
    const v = (k) => s.getPropertyValue(k).trim()
    return { chinh: v('--chinh'), canhBao: v('--canh-bao'), luoi: v('--luoi'), chuNhat: v('--chu-nhat'),
      nenKhoi: v('--nen-khoi'), vien: v('--vien'), chu: v('--chu') }
  }
  const [mau, setMau] = useState(doc)
  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)')
    const f = () => setMau(doc())
    mq.addEventListener('change', f)
    return () => mq.removeEventListener('change', f)
  }, [])
  return mau
}

function BieuDo({ soDo }) {
  const [chon, setChon] = useState('nhipTim')
  const mau = useMau()
  const loai = LOAI_BIEU_DO.find((l) => l.khoa === chon)

  // Chen diem trong khi mat du lieu hon 3 phut de duong bi ngat, khong noi thang qua khoang trong.
  const duLieu = useMemo(() => {
    const kq = []
    for (let i = 0; i < soDo.length; i++) {
      if (i > 0 && soDo[i].luc - soDo[i - 1].luc > 3 * PHUT) kq.push({ luc: soDo[i - 1].luc + PHUT })
      kq.push(soDo[i])
    }
    return kq
  }, [soDo])

  return (
    <section className="khoi">
      <div className="dau-khoi">
        <h2>24 giờ qua</h2>
        <div className="chon-loai" role="tablist" aria-label="Chọn số đo">
          {LOAI_BIEU_DO.map((l) => (
            <button key={l.khoa} role="tab" aria-selected={l.khoa === chon}
              className={l.khoa === chon ? 'dang-chon' : ''} onClick={() => setChon(l.khoa)}>
              {l.ten}
            </button>
          ))}
        </div>
      </div>
      {soDo.length === 0 ? (
        <p className="trong">Chưa có số đo nào trong 24 giờ qua.</p>
      ) : (
        <div className="bieu-do">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={duLieu} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
              <CartesianGrid stroke={mau.luoi} vertical={false} />
              <XAxis dataKey="luc" type="number" scale="time" domain={['dataMin', 'dataMax']}
                tickFormatter={gio} stroke={mau.chuNhat} fontSize={12} minTickGap={40} />
              <YAxis domain={loai.mien} stroke={mau.chuNhat} fontSize={12} allowDataOverflow />
              {loai.nguong.map((n) => (
                <ReferenceLine key={n} y={n} stroke={mau.canhBao} strokeWidth={1.5} strokeDasharray="5 4" />
              ))}
              <Tooltip
                labelFormatter={(v) => gio(v)}
                formatter={(v) => [`${v} ${loai.donVi}`, loai.ten]}
                contentStyle={{ background: mau.nenKhoi, border: `1px solid ${mau.vien}`, borderRadius: 8, color: mau.chu }}
              />
              <Line type="monotone" dataKey={chon} stroke={mau.chinh} strokeWidth={2} dot={false}
                connectNulls={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <p className="chu-thich">Đường đứt nét đỏ là ngưỡng đồng hồ gửi cảnh báo.</p>
        </div>
      )}
    </section>
  )
}

function DanhSachCanhBao({ canhBao, bayGio }) {
  if (canhBao.length === 0) return <p className="trong">Chưa có cảnh báo nào.</p>
  return (
    <ol className="dong-thoi-gian">
      {canhBao.map((c) => {
        const banDo = lienKetBanDo(c)
        return (
          <li key={`${c.luc}_${c.ma}`} className={c.khanCap ? 'khan-cap' : 'chu-y'}>
            <div className="thoi-diem">{ngayGio(c.luc, bayGio)}</div>
            <div className="mo-ta">
              <strong>{c.ten}</strong>
              {c.moTa && <span> ({c.moTa.replace('lan/phut', 'lần/phút').replace('do C', '°C')})</span>}
              <div className="phu-canh-bao">
                {c.soTinDaGui > 0
                  ? `Đã gửi SMS cho ${c.soTinDaGui}/${c.soNguoiThan} người`
                  : 'Chưa gửi được SMS'}
                {banDo && (
                  <> {' '}<a href={banDo} target="_blank" rel="noreferrer">Xem vị trí</a></>
                )}
              </div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

// ---------- Dien tam do (ECG) ----------
function KhoiEcg({ uid, ds, bayGio }) {
  const [chon, setChon] = useState(null)
  // Mac dinh mo lan do moi nhat; lan do dang xem bi xoa khoi danh sach thi quay ve lan moi nhat.
  const luc = ds.some((e) => e.luc === chon) ? chon : ds[0]?.luc ?? null
  const tomTat = ds.find((e) => e.luc === luc)

  return (
    <section className="khoi" aria-labelledby="tieu-de-ecg">
      <h2 id="tieu-de-ecg">Điện tâm đồ (ECG)</h2>
      {ds.length === 0 ? (
        <p className="trong">
          Chưa có lần đo ECG nào. Người đeo bấm đo ECG trong app (30 giây, đặt 3 điện cực) khi đồng hồ đang
          kết nối; kết quả sẽ hiện ở đây.
        </p>
      ) : (
        <div className="ecg">
          <ol className="ds-ecg" aria-label="Các lần đo">
            {ds.map((e) => (
              <li key={e.luc}>
                <button className={e.luc === luc ? 'dang-chon' : ''} aria-pressed={e.luc === luc}
                  onClick={() => setChon(e.luc)}>
                  <span className="thoi-diem">{ngayGio(e.luc, bayGio)}</span>
                  <span className="nhip-ecg">{e.nhipTb ? `${e.nhipTb} lần/phút` : 'Không tính được nhịp'}</span>
                  {e.coTuotDienCuc && <span className="tuot">Có lúc tuột điện cực</span>}
                </button>
              </li>
            ))}
          </ol>
          {tomTat && <XemSongEcg key={luc} uid={uid} tomTat={tomTat} bayGio={bayGio} />}
        </div>
      )}
    </section>
  )
}

function XemSongEcg({ uid, tomTat, bayGio }) {
  const [song, setSong] = useState(null) // null = dang tai
  const [loi, setLoi] = useState('')

  useEffect(() => {
    let huy = false
    taiSongEcg(uid, tomTat.luc)
      .then((s) => {
        if (huy) return
        if (!s || !s.mau) setLoi('Không tìm thấy sóng của lần đo này.')
        else setSong({ ...s, mauGoc: giaiMaMau(s.mau) })
      })
      .catch((e) => !huy && setLoi(`Không tải được sóng ECG: ${e.message}`))
    return () => { huy = true }
  }, [uid, tomTat.luc])

  const tanSo = song?.tanSo || TAN_SO_ECG
  const ve = useMemo(() => {
    if (!song) return null
    const y = locEcg(song.mauGoc)
    return { dai: chiaDai(y, song.dinhR || [], 5, tanSo), bd: bienDo(y) }
  }, [song, tanSo])

  function taiCsv() {
    const url = URL.createObjectURL(new Blob([thanhCsv(song.mauGoc, tanSo)], { type: 'text/csv' }))
    const a = document.createElement('a')
    a.href = url
    a.download = tenFileCsv(tomTat.luc)
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const t = tomTat
  return (
    <div className="xem-ecg">
      <div className="dau-khoi">
        <div>
          <div className="tieu-de-do">Đo lúc {ngayGio(t.luc, bayGio)}, {t.soGiay} giây</div>
          <div className="so-ecg">
            <span><strong>{t.nhipTb ?? '–'}</strong> lần/phút trung bình</span>
            {t.nhipThapNhat != null && <span>thấp nhất {t.nhipThapNhat}, cao nhất {t.nhipCaoNhat}</span>}
            <span>{t.soNhip} nhịp đếm được</span>
          </div>
        </div>
        <button className="nut-tai" onClick={taiCsv} disabled={!song}>Tải CSV cho bác sĩ</button>
      </div>
      {(t.coTuotDienCuc || t.soMauThieu > 0) && (
        <p className="bao-ecg">
          {t.coTuotDienCuc && 'Trong lần đo có lúc tuột điện cực, đoạn sóng đó có thể bị nhiễu. '}
          {t.soMauThieu > 0 && `Mất ${t.soMauThieu} mẫu (khoảng ${(t.soMauThieu / TAN_SO_ECG).toFixed(1).replace('.', ',')} giây) do Bluetooth, đoạn đó sóng đi ngang.`}
        </p>
      )}
      {loi && <p className="loi" role="alert">{loi}</p>}
      {!loi && !ve && <p className="trong">Đang tải sóng...</p>}
      {ve && (
        <>
          <div className="giay-ecg" role="img"
            aria-label={`Sóng điện tâm đồ ${t.soGiay} giây, nhịp trung bình ${t.nhipTb ?? 'không rõ'} lần mỗi phút`}>
            {ve.dai.map((d) => (
              <DaiEcg key={d.batDau} dai={d} bd={ve.bd} tanSo={tanSo} />
            ))}
          </div>
          <p className="chu-thich">
            Mỗi dòng 5 giây. Ô nhỏ 0,04 giây, ô lớn 0,2 giây, giống giấy ECG chạy 25 mm/s. Chấm xanh là đỉnh R app
            đếm được. Biên độ chưa hiệu chuẩn theo mV.
          </p>
        </>
      )}
    </div>
  )
}

// 1 dai 5 giay: 1 o nho = 10 mau (0,04 s o 250 Hz) = 10 don vi SVG, cao 24 o nho.
const O = 10
const CAO_DAI = 24 * O
function DaiEcg({ dai, bd, tanSo }) {
  const rong = 5 * tanSo // so mau 1 dai day du
  // Duong nen hoi thap (60% chieu cao) vi song R huong len; dinh cao gap doi bien do van vua dai.
  const doc = (v) => Math.max(2, Math.min(CAO_DAI - 2, CAO_DAI * 0.6 - (v / bd) * (CAO_DAI * 0.28)))
  const diem = dai.y.map((v, i) => `${i},${doc(v).toFixed(1)}`).join(' ')
  const doc0 = []
  for (let x = 0; x <= rong; x += O) doc0.push(x)
  const ngang = []
  for (let y = 0; y <= CAO_DAI; y += O) ngang.push(y)
  const giay0 = Math.round(dai.batDau / tanSo)
  return (
    <div className="dai-ecg">
      <span className="nhan-dai">{giay0}–{giay0 + 5} s</span>
      <svg viewBox={`0 0 ${rong} ${CAO_DAI}`} preserveAspectRatio="xMinYMid meet" aria-hidden="true">
        {doc0.map((x) => (
          <line key={`d${x}`} x1={x} x2={x} y1={0} y2={CAO_DAI} className={x % (5 * O) === 0 ? 'lon' : 'nho'} />
        ))}
        {ngang.map((y) => (
          <line key={`n${y}`} x1={0} x2={rong} y1={y} y2={y} className={y % (5 * O) === 0 ? 'lon' : 'nho'} />
        ))}
        <polyline points={diem} className="vet" />
        {dai.dinhR.map((r) => (
          <circle key={r} cx={r} cy={Math.max(6, doc(dai.y[r]) - 9)} r={4} className="dinh" />
        ))}
      </svg>
    </div>
  )
}
