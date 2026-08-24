'use strict';

/* ==========================================================================
   PASAR TERMINAL — IHSG vs bursa yang benar-benar berdampak, dengan berita
   yang menempel di hari bursa yang kena akibatnya.

   Semua indeks digambar setelah di-rebase ke 100 pada awal rentang. Itu satu-
   satunya cara jujur menaruh IHSG (~6.500) dan Nikkei (~66.000) di satu sumbu.

   Daftar indeks dan lag-nya datang dari data (collector/config.py), bukan
   ditulis ulang di sini — menambah bursa cukup satu baris di sana. Gaya
   garisnya dibagikan otomatis dari DEK_GARIS di bawah.

   Panel kanan dipisah dua skala, karena dua pertanyaan yang berbeda:
     MAKRO — apa yang menggerakkan seluruh papan (IHSG, rupiah, Fed, komoditas)
     MIKRO — saham apa yang diberitakan hari itu, dikelompokkan per emiten
   Dicampur jadi satu daftar, dua-duanya tenggelam: pengumuman dividen
   berdesakan dengan keputusan suku bunga dan tidak ada yang terbaca.
   ========================================================================== */

/* ---------- bahasa rupa ---------------------------------------------------
   Rangkanya tetap hitam-tulang-merah: tombol, tab, angka naik/turun, dan
   seluruh antarmuka tidak punya warna aksen sama sekali. Yang berwarna cuma
   ISI -- kategori berita dan peta. Jadi warna di layar ini selalu berarti
   "ini soal apa", tidak pernah "ini tombolnya di sini".

   Hue-nya bukan diundi; tiap warna menjawab dari mana tekanannya datang:

     tulang   BURSA          pasar itu sendiri, bukan sebab dari luar
     jingga   MAKRO_DOMESTIK dapur sendiri: BI, rupiah, inflasi, APBN
     sian     MAKRO_GLOBAL   datang dari luar: The Fed, tarif, Wall Street
     biru     KEBIJAKAN      aturan main: OJK, IDX, pajak, POJK
     kuningan KOMODITAS      logam & tanah: emas, minyak, batu bara, CPO
     hijau    EMITEN         satu perusahaan (= skala MIKRO, warnanya sama)
     merah    POLITIK        risiko. sewarna dengan "turun", memang sengaja
     abu      LAINNYA        ada, tapi tidak menuntut apa-apa

   Hijau EMITEN dan hijau MIKRO sengaja satu warna: dua-duanya menjawab
   pertanyaan yang sama dari sisi berbeda, dan begitu pita ALIRAN BERITA
   menghijau kamu langsung tahu hari itu ramai berita korporasi, bukan hari
   yang menggerakkan papan.                                                */
const RUPA = {
  tulang: '#EDEAE4', redup: '#A5A29B', redup2: '#6B6862',
  abu: '#45423D', garis: '#1E1C1A', garis2: '#34312C',
  panel: '#0A0A09', merah: '#FF4438',
};
const WARNA_KAT = {
  BURSA: RUPA.tulang, MAKRO_DOMESTIK: '#FF8A3D', MAKRO_GLOBAL: '#35C6E8',
  KEBIJAKAN: '#8C9EFF', KOMODITAS: '#D9B310', EMITEN: '#12D488',
  POLITIK: RUPA.merah, LAINNYA: RUPA.abu,
};

/* Indeks di chart tetap TANPA warna: dibedakan lewat tebal garis dan pola
   putus-putus. Alasannya beda dari kategori -- di chart yang perlu dibaca itu
   BENTUK kurva, dan tujuh garis berwarna saling menutupi bentuk satu sama
   lain. Deck dibagikan urut data, jadi menambah bursa di config.py tetap
   cukup satu baris. Bonus: tetap terbaca kalau dicetak hitam-putih. */
const GARIS_UTAMA = { c: RUPA.tulang, w: 2, d: [] };
const DEK_GARIS = [
  { c: RUPA.redup,  w: 1.2, d: [] },
  { c: RUPA.redup,  w: 1.2, d: [5, 3] },
  { c: '#7E7B74',   w: 1.2, d: [2, 3] },
  { c: '#7E7B74',   w: 1.2, d: [9, 3, 2, 3] },
  { c: '#605D57',   w: 1.4, d: [1, 3] },
  { c: '#605D57',   w: 1.4, d: [7, 2, 1, 2] },
];
/** Contoh garis untuk legend & tombol: pola yang sama, dibuat pakai CSS. */
function swatch(gy) {
  if (!gy.d.length) return `background:${gy.c}`;
  const on = gy.d[0], off = gy.d[1];
  return `background-image:repeating-linear-gradient(90deg,${gy.c} 0 ${on}px,`
       + `transparent ${on}px ${on + off}px)`;
}

/* ---------- PETA DAMPAK --------------------------------------------------
   Wilayah dipanaskan pakai dua warna saja, bukan dua belas: rumah (jingga,
   sewarna MAKRO_DOMESTIK) dan luar negeri (sian, sewarna MAKRO_GLOBAL).
   Memberi tiap benua hue sendiri terlihat keren dan tidak berguna -- yang
   mau dijawab peta ini cuma satu: tekanan hari ini datang dari dalam atau
   dari luar, dan dari sebelah mana.                                       */
const WARNA_PETA = {
  darat: '#221F1C', darat2: '#2E2A26',
  rumah: '#FF8A3D', luar: '#35C6E8',
};
const LABEL_WIL = {
  ID: 'Indonesia', US: 'Amerika', CN: 'China', JP_KR: 'Jepang & Korea',
  ASEAN: 'ASEAN', IN: 'India', EU: 'Eropa', ME: 'Timur Tengah',
  RU: 'Rusia', AU: 'Australia', LATAM: 'Amerika Latin', AF: 'Afrika',
};
const LABEL_KAT = {
  BURSA: 'bursa', MAKRO_DOMESTIK: 'makro dom', MAKRO_GLOBAL: 'makro global',
  KEBIJAKAN: 'kebijakan', KOMODITAS: 'komoditas', EMITEN: 'emiten',
  POLITIK: 'politik', LAINNYA: 'lainnya',
};
const URUT_KAT = ['BURSA', 'MAKRO_DOMESTIK', 'MAKRO_GLOBAL', 'KEBIJAKAN',
                  'KOMODITAS', 'POLITIK', 'EMITEN', 'LAINNYA'];
const WARNA_SKALA = { MAKRO: RUPA.tulang, MIKRO: WARNA_KAT.EMITEN, UMUM: '#2A2825' };

const RENTANG = [
  ['1B', 21], ['3B', 63], ['6B', 126], ['1T', 252],
  ['3T', 756], ['5T', 1260], ['MAX', Infinity],
];
const BULAN = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
const HARI = ['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];

const S = {
  meta: null, pasar: null, hari: null, tema: null, emiten: {},
  urut: [],                   // kode indeks, urutan gambar (utama digambar terakhir)
  seri: {},                   // kode -> {nama, negara, warna, lag, tgl[], c[], idx{}}
  spine: [], akhirBar: null,
  aktif: new Set(),
  rentang: '1T',
  dampak: true,               // geser bursa yang tutup setelah IDX
  refDiv: 'asia',             // acuan panel divergensi: 'asia' | 'global'
  skala: 'linear',            // 'linear' | 'log' -- dipilih otomatis per rentang
  tanpaData: new Set(),       // seri aktif yang tak punya data di jendela ini
  i0: 0, i1: 0,
  hover: null, pin: null,
  tab: 'MAKRO',               // MAKRO | MIKRO | SEMUA
  filter: new Set(),          // kategori (tab makro/semua) atau kode emiten (tab mikro)
  bulanCache: new Map(),
  panelTok: 0,                // penjaga balapan: scrub cepat -> fetch bulan menyusul

  peta: null,                 // kisi titik dunia + simpul bursa (data/peta.json)
  jejak: false,               // peta: HARI saja, atau JEJAK 20 sesi meluruh
  putar: null,                // id interval saat sesi diputar otomatis
  panasCache: new Map(),      // t|mode -> hasil panasWilayah(); scrub itu sering
  sesiBerita: null,
};

const WIL_URUT = ['ID', 'US', 'CN', 'JP_KR', 'ASEAN', 'IN',
                  'EU', 'ME', 'RU', 'AU', 'LATAM', 'AF'];

const $ = (s) => document.querySelector(s);
const fmt = (v, d = 2) => v == null ? '—'
  : v.toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (v) => v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
const kelas = (v) => v == null ? '' : v >= 0 ? 'naik' : 'turun';
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function tglPanjang(t) {
  const d = new Date(t + 'T00:00:00');
  return `${HARI[d.getDay()]}, ${d.getDate()} ${BULAN[d.getMonth()]} ${d.getFullYear()}`;
}
function tglPendek(t) {
  const d = new Date(t + 'T00:00:00');
  return `${d.getDate()} ${BULAN[d.getMonth()]}`;
}
const jamDari = (iso) => iso ? iso.slice(11, 16) : '';
const namaEmiten = (k) => (S.emiten[k] || [])[0] || k;
const sektorEmiten = (k) => (S.emiten[k] || [])[1] || 'lainnya';

/* ---------- muat data ---------------------------------------------------- */
async function muat() {
  const ambil = (f, kosong) => fetch(f).then((r) => (r.ok ? r.json() : kosong))
    .catch(() => kosong);
  const [meta, pasar, hari, tema, emiten, peta] = await Promise.all([
    fetch('data/meta.json').then((r) => r.json()),
    fetch('data/pasar.json').then((r) => r.json()),
    fetch('data/hari.json').then((r) => r.json()),
    ambil('data/tema.json', { tema: {}, cukup: false }),
    ambil('data/emiten.json', {}),
    ambil('data/peta.json', null),
  ]);
  S.meta = meta; S.pasar = pasar; S.hari = hari; S.tema = tema; S.emiten = emiten;
  S.peta = peta;

  let nGaya = 0;
  for (const s of pasar.indeks) {
    const tgl = s.bar.map((b) => b[0]);
    const idx = {};
    tgl.forEach((t, i) => { idx[t] = i; });
    S.seri[s.kode] = {
      nama: s.nama, negara: s.negara, lag: s.lag, utama: s.utama,
      gaya: s.utama ? GARIS_UTAMA : DEK_GARIS[nGaya++ % DEK_GARIS.length],
      tgl, c: s.bar.map((b) => b[1]), r: s.bar.map((b) => b[2]), idx,
    };
    if (s.awal) S.aktif.add(s.kode);
  }
  // yang utama digambar paling akhir supaya garisnya di atas yang lain
  S.urut = pasar.indeks.map((s) => s.kode)
    .sort((a, b) => (S.seri[a].utama ? 1 : 0) - (S.seri[b].utama ? 1 : 0));

  // Sesi yang barnya belum terbit ikut masuk sumbu-x, supaya berita akhir
  // pekan / hari ini tetap bisa dibuka. Harganya memang belum ada.
  S.akhirBar = S.seri.IHSG.tgl[S.seri.IHSG.tgl.length - 1];
  S.spine = S.seri.IHSG.tgl.concat((meta.sesi_mendatang || []).filter((t) => t > S.akhirBar));
}

/** Nilai `kode` yang sudah bisa diketahui pasar Indonesia pada sesi t. */
function nilaiPada(kode, t) {
  const s = S.seri[kode];
  if (!s) return null;
  // Jangan pernah membawa maju nilai terakhir melewati ujung data: itu
  // menggambar garis datar palsu di sesi yang harganya memang belum ada.
  if (t > s.tgl[s.tgl.length - 1]) return null;
  let i = s.idx[t];
  if (i === undefined) {                    // bursa itu libur / beda kalender
    i = cariTerakhir(s.tgl, t);
    if (i < 0) return null;
  }
  // Hanya bursa yang tutup SETELAH IDX yang digeser (Wall Street, lag 1).
  // Bursa Asia lag 0: Nikkei tutup 13:00 WIB, STI 16:00 -- sudah selesai
  // sebelum IDX tutup, jadi menggesernya justru membuang informasi sehari.
  if (S.dampak) i -= s.lag;
  return i >= 0 ? s.c[i] : null;
}

/** Return harian sebuah bursa pada sesi IDX `t`, ikut aturan lag yang sama
    dengan nilaiPada. Dipakai simpul bursa di peta. */
function retPada(kode, t) {
  const s = S.seri[kode];
  if (!s || t > s.tgl[s.tgl.length - 1]) return null;
  let i = s.idx[t];
  if (i === undefined) { i = cariTerakhir(s.tgl, t); if (i < 0) return null; }
  if (S.dampak) i -= s.lag;
  return i >= 0 ? s.r[i] : null;
}

function cariTerakhir(arr, t) {           // indeks terakhir dengan arr[i] <= t
  let lo = 0, hi = arr.length - 1, r = -1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (arr[m] <= t) { r = m; lo = m + 1; } else hi = m - 1;
  }
  return r;
}

const divHari = (t) => (S.pasar.divergensi[S.refDiv] || {})[t] ?? null;

/* ---------- kerangka gambar ---------------------------------------------- */
function siapkan(cv) {
  const r = cv.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  cv.width = Math.max(1, Math.round(r.width * dpr));
  cv.height = Math.max(1, Math.round(r.height * dpr));
  const g = cv.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, r.width, r.height);
  return { g, W: r.width, H: r.height };
}

const PAD = { l: 8, r: 62, t: 8, b: 20 };
const FONT = '10px "IBM Plex Mono", ui-monospace, monospace';

function xDari(i, W) {
  const n = S.i1 - S.i0;
  const lebar = W - PAD.l - PAD.r;
  return PAD.l + (n <= 1 ? lebar / 2 : (i - S.i0) / (n - 1) * lebar);
}
function iDariX(x, W) {
  const n = S.i1 - S.i0;
  const f = (x - PAD.l) / (W - PAD.l - PAD.r);
  return Math.max(S.i0, Math.min(S.i1 - 1, S.i0 + Math.round(f * (n - 1))));
}

/* ---------- chart utama --------------------------------------------------- */
function gambarChart() {
  const { g, W, H } = siapkan($('#chart'));
  const tgl = S.spine.slice(S.i0, S.i1);
  if (!tgl.length) return;

  // rebase: tiap seri = 100 di hari pertama yang terlihat
  const jalur = {};
  let min = Infinity, max = -Infinity;
  S.tanpaData = new Set();
  for (const kode of S.urut) {
    if (!S.aktif.has(kode)) continue;
    const mentah = tgl.map((t) => nilaiPada(kode, t));
    // Dasar rebase = titik PERTAMA YANG ADA milik seri ini di jendela, bukan
    // nilai di tgl[0]. Bursa lain mulai sehari setelah IHSG, jadi memaksa
    // dasar ke tanggal pertama IHSG membuat seluruh garisnya hilang di MAX.
    const dasar = mentah.find((v) => v != null);
    if (!dasar) { S.tanpaData.add(kode); continue; }
    const arr = mentah.map((v) => v == null ? null : v / dasar * 100);
    jalur[kode] = arr;
    for (const v of arr) if (v != null) { if (v < min) min = v; if (v > max) max = v; }
  }
  if (min === Infinity) return;
  // Rentang panjang bisa merentang 10x lipat; di skala linear IHSG jadi gepeng
  // di dasar sementara Nasdaq membubung, dan bentuk keduanya tak terbaca.
  const log = S.skala === 'log';
  const f = log ? Math.log : (x) => x;
  let lo = f(min), hi = f(max);
  const bantal = (hi - lo) * 0.12 || (log ? 0.02 : 1);
  lo -= bantal; hi += bantal;
  const yDari = (v) => PAD.t + (1 - (f(v) - lo) / (hi - lo)) * (H - PAD.t - PAD.b);
  const nilaiDiPecahan = (k) => log ? Math.exp(lo + (hi - lo) * k) : lo + (hi - lo) * k;

  g.font = FONT;
  g.textBaseline = 'middle';
  for (let k = 0; k <= 4; k++) {
    const v = nilaiDiPecahan(k / 4);
    const y = Math.round(yDari(v)) + 0.5;
    g.strokeStyle = RUPA.garis; g.lineWidth = 1;
    g.beginPath(); g.moveTo(PAD.l, y); g.lineTo(W - PAD.r, y); g.stroke();
    g.fillStyle = RUPA.abu; g.textAlign = 'left';
    g.fillText(pct(v - 100), W - PAD.r + 7, y);   // sumbu dalam %, karena sudah di-rebase
  }

  g.textAlign = 'center'; g.textBaseline = 'top';
  const langkah = Math.max(1, Math.floor(tgl.length / 7));
  for (let i = 0; i < tgl.length; i += langkah) {
    const x = xDari(S.i0 + i, W);
    g.strokeStyle = '#141311';
    g.beginPath(); g.moveTo(x, PAD.t); g.lineTo(x, H - PAD.b); g.stroke();
    g.fillStyle = RUPA.abu;
    g.fillText(tglPendek(tgl[i]), x, H - PAD.b + 5);
  }

  // Penanda hari penting: pita tipis, tidak mengotori garis harga.
  // Ditandai hanya hari yang GERAK IHSG-nya menonjol. Hari ramai-berita
  // sudah punya panelnya sendiri di bawah.
  //
  // Dulu tiap pita mewarisi warna kategori beritanya. Di rentang bergejolak
  // hasilnya pagar vertikal pelangi yang justru menutupi garis harga. Sekarang
  // cuma dua tingkat: hari risiko (politik) merah dan benar-benar terlihat,
  // sisanya guratan tulang nyaris transparan -- kalau menumpuk, penumpukannya
  // sendiri yang jadi informasi (gejolak berkerumun), bukan tiap batangnya.
  for (let i = 0; i < tgl.length; i++) {
    const h = S.hari[tgl[i]];
    if (!h || !h.n || Math.abs(h.r || 0) < (S.meta.ambang?.move ?? 1.5)) continue;
    const top = h.top && h.top[0];
    const risiko = top && top.k === 'POLITIK';
    g.fillStyle = risiko ? RUPA.merah + '55' : RUPA.tulang + '12';
    g.fillRect(xDari(S.i0 + i, W) - 0.5, PAD.t, 1, H - PAD.t - PAD.b);
  }

  for (const kode of S.urut) {
    const arr = jalur[kode];
    if (!arr) continue;
    const gy = S.seri[kode].gaya;
    g.strokeStyle = gy.c;
    g.lineWidth = gy.w;
    g.setLineDash(gy.d);
    g.beginPath();
    let jalan = false;
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] == null) { jalan = false; continue; }
      const x = xDari(S.i0 + i, W), y = yDari(arr[i]);
      if (!jalan) { g.moveTo(x, y); jalan = true; } else g.lineTo(x, y);
    }
    g.stroke();
    g.setLineDash([]);
  }

  const sorot = S.pin || S.hover;
  if (sorot) {
    const i = S.spine.indexOf(sorot);
    if (i >= S.i0 && i < S.i1) {
      const x = xDari(i, W);
      for (const kode of Object.keys(jalur)) {
        const v = jalur[kode][i - S.i0];
        if (v == null) continue;
        g.fillStyle = S.seri[kode].gaya.c;
        g.beginPath(); g.arc(x, yDari(v), 2.6, 0, 7); g.fill();
        g.strokeStyle = '#000'; g.lineWidth = 1.4; g.stroke();
      }
    }
  }
  gambarLegend(jalur, sorot);
}

function gambarLegend(jalur, sorot) {
  const t = sorot || S.spine[S.i1 - 1];
  const iSorot = S.spine.indexOf(t) - S.i0;
  $('#legend').innerHTML = S.urut.slice().reverse().filter((k) => jalur[k]).map((k) => {
    // Angkanya dibaca dari jalur yang sudah di-rebase, jadi ikut apa yang
    // benar-benar tergambar. Kalau sesi yang disorot belum punya harga
    // (berita akhir pekan menempel ke Senin), mundur ke titik terakhir yang
    // ada -- menampilkan "—" di situ bikin legend terlihat rusak padahal
    // datanya cuma belum terbit.
    const arr = jalur[k];
    let i = Math.min(Math.max(iSorot, 0), arr.length - 1);
    while (i >= 0 && arr[i] == null) i--;
    const p = i >= 0 && arr[i] != null ? arr[i] - 100 : null;
    const gy = S.seri[k].gaya;
    return `<span class="li"><i class="sw" style="${swatch(gy)}"></i>
      <span class="kd" style="color:${gy.c}">${k}</span>
      <span class="${kelas(p)}">${pct(p)}</span></span>`;
  }).join('');
}

/* ---------- divergensi ---------------------------------------------------- */
function gambarDivergensi() {
  const { g, W, H } = siapkan($('#divergensi'));
  const tgl = S.spine.slice(S.i0, S.i1);
  if (!tgl.length) return;

  const nilai = tgl.map(divHari);
  const ada = nilai.filter((v) => v != null).map(Math.abs);
  const maks = Math.max(1, ...ada);
  const mid = H / 2;
  const lebarBar = Math.max(1, (W - PAD.l - PAD.r) / tgl.length * 0.72);
  const ambang = S.meta.ambang?.divergensi ?? 1;
  const sorot = S.pin || S.hover;

  g.strokeStyle = RUPA.garis2; g.lineWidth = 1;
  g.beginPath(); g.moveTo(PAD.l, mid + 0.5); g.lineTo(W - PAD.r, mid + 0.5); g.stroke();

  for (let i = 0; i < tgl.length; i++) {
    const v = nilai[i];
    if (v == null) continue;
    const x = xDari(S.i0 + i, W);
    const h = (Math.abs(v) / maks) * (mid - 6);
    g.globalAlpha = tgl[i] === sorot ? 1 : (Math.abs(v) >= ambang ? 0.92 : 0.32);
    g.fillStyle = v >= 0 ? RUPA.tulang : RUPA.merah;
    g.fillRect(x - lebarBar / 2, v >= 0 ? mid - h : mid, lebarBar, h);
  }
  g.globalAlpha = 1;

  g.font = FONT;
  g.fillStyle = RUPA.abu; g.textAlign = 'left'; g.textBaseline = 'middle';
  g.fillText('+' + maks.toFixed(1), W - PAD.r + 7, 9);
  g.fillText('−' + maks.toFixed(1), W - PAD.r + 7, H - 9);
}

/* ---------- PETA DAMPAK ---------------------------------------------------
   "Wilayah mana yang lagi ada apa-apanya hari ini."

   Yang digambar BUKAN jumlah berita. Kalau jumlah mentah yang dipakai,
   Indonesia menyala penuh tiap hari dan peta ini tidak pernah memberi tahu
   apa pun -- 5.062 dari 7.500 penyebutan wilayah di arsip ini memang
   Indonesia. Yang berarti adalah KELUAR DARI KEBIASAAN wilayah itu sendiri:

     z = (hari ini - lazimnya) / akar(lazimnya + 2)

   Pembaginya akar, bukan simpangan baku, karena ini hitung-cacah (Poisson):
   wilayah yang biasanya 2 berita per hari memang wajar melonjak ke 5, dan
   wilayah yang biasanya 40 tidak. Tambahan +2 menahan wilayah sepi (Afrika:
   biasanya nol) meledak jadi z besar cuma karena satu artikel nyasar.

   "Lazimnya" = median 40 sesi BERBERITA sebelumnya, bukan 40 hari kalender:
   arsipnya berlubang (Nov 2025 lalu lompat ke Jan 2026), dan memakai kalender
   membuat lubang itu terhitung sebagai rentetan hari sepi.

   Mode JEJAK menjumlahkan z dua puluh sesi ke belakang dengan peluruhan 0,85.
   Itu yang bikin -- sambil sesi diputar maju -- sebuah wilayah kelihatan
   MENYALA PELAN lalu padam: satu berita tidak berarti apa-apa, tiga minggu
   berita berturut-turut itu tema. Hitungannya deterministik (tidak menyimpan
   sisa dari frame sebelumnya), jadi digeser mundur pun hasilnya sama. */
const PETA_JENDELA = 40;   // sesi buat mengukur "lazimnya"
const PETA_EKOR = 20;      // sesi yang dijumlahkan di mode JEJAK
const PETA_LURUH = 0.85;
const PETA_AMBANG = 1.0;   // di bawah ini hari biasa, tidak usah menyala

function sesiBerberita() {
  if (!S.sesiBerita) S.sesiBerita = S.spine.filter((t) => (S.hari[t]?.n || 0) > 0);
  return S.sesiBerita;
}

/** z tiap wilayah pada daftar[i], relatif 40 sesi berberita sebelumnya. */
function _zWilayah(daftar, i) {
  const w = S.hari[daftar[i]]?.w || {};
  const mulai = Math.max(0, i - PETA_JENDELA);
  const out = {};
  for (const wil of WIL_URUT) {
    const riwayat = [];
    for (let k = mulai; k < i; k++) riwayat.push(S.hari[daftar[k]]?.w?.[wil] || 0);
    riwayat.sort((a, b) => a - b);
    const n = riwayat.length;
    const dasar = !n ? 0
      : n % 2 ? riwayat[(n - 1) / 2] : (riwayat[n / 2 - 1] + riwayat[n / 2]) / 2;
    out[wil] = ((w[wil] || 0) - dasar) / Math.sqrt(dasar + 2);
  }
  return out;
}

function panasWilayah(t) {
  const kunci = t + (S.jejak ? '|j' : '|h');
  if (S.panasCache.has(kunci)) return S.panasCache.get(kunci);

  const daftar = sesiBerberita();
  let i = daftar.indexOf(t);
  // Sesi tanpa berita (arsip belum menjangkau, atau hari yang memang sepi)
  // memakai sesi berberita terakhir sebelumnya. Peta yang tiba-tiba padam
  // terbaca seperti kerusakan, bukan seperti data.
  if (i < 0) {
    for (let k = daftar.length - 1; k >= 0; k--) if (daftar[k] <= t) { i = k; break; }
  }
  const hasil = { nilai: {}, urut: [], basi: false, ada: false };
  if (i < 0) { S.panasCache.set(kunci, hasil); return hasil; }
  hasil.basi = daftar[i] !== t;

  const mentah = {};
  for (const wil of WIL_URUT) mentah[wil] = 0;
  const ekor = S.jejak ? Math.min(PETA_EKOR, i + 1) : 1;
  for (let e = 0; e < ekor; e++) {
    const z = _zWilayah(daftar, i - e);
    const bobot = Math.pow(PETA_LURUH, e);
    for (const wil of WIL_URUT) {
      if (z[wil] >= PETA_AMBANG) mentah[wil] += z[wil] * bobot;
    }
  }
  hasil.urut = WIL_URUT.filter((w) => mentah[w] > 0)
    .sort((a, b) => mentah[b] - mentah[a]).map((w) => [w, mentah[w]]);
  hasil.ada = hasil.urut.length > 0;

  // Terangnya dipangkatkan dua dan dibatasi empat wilayah luar teratas.
  //
  // Percobaan pertama memakai bagian linear terhadap yang terpanas, dan pada
  // hari ramai SELURUH dunia menyala sian dengan terang yang mirip-mirip --
  // benar secara angka, tapi tidak menjawab pertanyaannya. Yang mau dibaca
  // sekali lihat itu "hari ini sebelah MANA", jadi jarak antara juara satu
  // dan juara tiga harus terlihat. Pangkat tiga melakukan itu: yang di 76%
  // teratas turun jadi 44% terang. Cuma tiga wilayah luar yang boleh menyala
  // sekaligus -- Rusia dan Amerika Utara itu daratan raksasa, dan empat
  // wilayah besar dengan terang mirip-mirip terbaca sebagai "dunia", bukan
  // sebagai arah.
  //
  // Indonesia DIKELUARKAN dari pembagian itu dan punya skalanya sendiri.
  // Alasannya bukan estetika: rumah selalu paling ramai (5.062 dari 7.500
  // penyebutan), jadi menormalkan luar negeri terhadap Indonesia membuat
  // seluruh dunia gelap permanen -- dan justru "dari luar sebelah mana"
  // itu satu-satunya hal yang tidak bisa dibaca dari panel lain. Sekarang
  // Indonesia menjawab "seberapa berisik di rumah", dunia menjawab "sebelah
  // mana", dan keduanya tidak lagi berebut satu sumbu yang sama.
  const SKALA_RUMAH = S.jejak ? 45 : 14;
  const luar = hasil.urut.filter(([w]) => w !== 'ID');
  const maksLuar = luar.length ? luar[0][1] : 0;
  const bolehNyala = new Set(luar.slice(0, 3).map(([w]) => w));
  for (const wil of WIL_URUT) {
    if (wil === 'ID') {
      hasil.nilai.ID = Math.min(1, mentah.ID / SKALA_RUMAH);
      continue;
    }
    const n = maksLuar > 0 && bolehNyala.has(wil) ? mentah[wil] / maksLuar : 0;
    hasil.nilai[wil] = n * n * n;
  }

  if (S.panasCache.size > 400) S.panasCache.clear();
  S.panasCache.set(kunci, hasil);
  return hasil;
}

function gambarPeta() {
  const kanvas = $('#peta');
  if (!kanvas || !S.peta) return;
  const { g, W, H } = siapkan(kanvas);
  const P = S.peta;
  const t = hariAktif();
  const panas = t ? panasWilayah(t) : { nilai: {}, urut: [], ada: false };

  // Kisi dipasang di tengah dengan rasio dijaga: dunia yang gepeng terbaca
  // salah, dan yang penting di sini justru posisi relatif antarbenua.
  const skala = Math.min(W / P.kolom, H / P.baris);
  const ox = (W - P.kolom * skala) / 2;
  const oy = (H - P.baris * skala) / 2;
  const r = Math.max(0.8, skala * 0.40);

  for (let b = 0; b < P.baris; b++) {
    const baris = P.sel[b];
    const y = oy + (b + 0.5) * skala;
    for (let k = 0; k < P.kolom; k++) {
      const ch = baris[k];
      if (ch === '.') continue;
      const wil = P.huruf[ch];
      const n = wil ? (panas.nilai[wil] || 0) : 0;
      if (n > 0.03) {
        g.fillStyle = wil === 'ID' ? WARNA_PETA.rumah : WARNA_PETA.luar;
        g.globalAlpha = 0.14 + 0.86 * n;
      } else {
        g.fillStyle = wil ? WARNA_PETA.darat2 : WARNA_PETA.darat;
        g.globalAlpha = 1;
      }
      // Indonesia dapat titik lebih gemuk saat menyala. Kepulauan ini cuma
      // 60-an sel; berdampingan dengan Amerika Utara yang 400 sel, terang
      // yang sama terbaca sebagai "yang di sana lebih penting" -- padahal
      // yang dibandingkan luas daratan, bukan berita. Menggemukkan titiknya
      // mengembalikan bobot ke isinya.
      const rr = wil === 'ID' && n > 0.15 ? r * 1.5 : r;
      const x = ox + (k + 0.5) * skala;
      g.fillRect(x - rr, y - rr, rr * 2, rr * 2);
    }
  }
  g.globalAlpha = 1;

  // Simpul bursa. Warnanya cuma dua -- tulang naik, merah turun -- karena di
  // atas peta yang sudah berpendar, hue ketiga bikin mata tidak tahu lagi
  // mana yang data dan mana yang latar.
  g.font = '8px "IBM Plex Mono", ui-monospace, monospace';
  g.textAlign = 'center';
  g.textBaseline = 'middle';

  const simpul = P.bursa.map((bu) => {
    const rets = bu.kode.map((k) => (t ? retPada(k, t) : null)).filter((v) => v != null);
    const ret = rets.length ? rets.reduce((a, b) => a + b, 0) / rets.length : null;
    return {
      bu, ret,
      x: ox + ((bu.lon - P.lon0) / P.langkah) * skala,
      y: oy + ((P.lat0 - bu.lat) / P.langkah) * skala,
      kuat: ret == null ? 0 : Math.min(1, Math.abs(ret) / 2),
    };
  });

  for (const n of simpul) {
    const naik = n.ret != null && n.ret >= 0;
    if (n.kuat > 0.05) {                       // halo sebesar geraknya
      g.beginPath();
      g.arc(n.x, n.y, 3 + n.kuat * 7, 0, 7);
      g.fillStyle = naik ? 'rgba(237,234,228,.13)' : 'rgba(255,68,56,.17)';
      g.fill();
    }
    const sisi = n.ret == null ? 3 : 3.4 + n.kuat * 2.6;
    g.fillStyle = n.ret == null ? RUPA.abu : (naik ? RUPA.tulang : RUPA.merah);
    g.fillRect(n.x - sisi / 2, n.y - sisi / 2, sisi, sisi);
    g.strokeStyle = '#000'; g.lineWidth = 1;
    g.strokeRect(n.x - sisi / 2, n.y - sisi / 2, sisi, sisi);
  }

  // Label ditaruh belakangan dan dijatah: Jakarta, Singapura, dan Bangkok
  // cuma berjarak sepuluh piksel di kisi 2 derajat, jadi kalau semuanya
  // dilabeli hasilnya tumpukan huruf yang tidak terbaca satu pun. IHSG selalu
  // dapat tempat (ini terminal IDX), sisanya urut siapa yang bergerak paling
  // besar -- yang kalah tetap punya kotak, cuma tanpa nama.
  const antre = simpul.slice().sort((a, b) => {
    if (a.bu.kode.includes('IHSG')) return -1;
    if (b.bu.kode.includes('IHSG')) return 1;
    return b.kuat - a.kuat;
  });
  const dipakai = [];
  const bentrok = (k) => dipakai.some((d) => k[0] < d[2] && k[2] > d[0]
                                          && k[1] < d[3] && k[3] > d[1]);
  for (const n of antre) {
    const label = n.bu.kode.join('/');
    const lw = g.measureText(label).width + 4;
    // Empat tempat duduk dicoba berurutan sebelum menyerah: bawah, atas,
    // kanan, kiri. Tanpa ini Tokyo selalu kalah dari Seoul -- jaraknya cuma
    // 26 piksel di kisi 2 derajat, padahal dua-duanya bursa penting.
    const calon = [[n.x, n.y + 10], [n.x, n.y - 9],
                   [n.x + lw / 2 + 6, n.y], [n.x - lw / 2 - 6, n.y]];
    let taruh = null;
    for (const [cx, cy] of calon) {
      const k = [cx - lw / 2, cy - 5, cx + lw / 2, cy + 5];
      if (k[0] < 0 || k[2] > W || k[1] < 0 || k[3] > H) continue;
      if (bentrok(k)) continue;
      taruh = { cx, cy, k }; break;
    }
    if (!taruh) continue;
    dipakai.push(taruh.k);
    g.fillStyle = 'rgba(0,0,0,.78)';
    g.fillRect(taruh.k[0], taruh.k[1], lw, 10);
    g.fillStyle = n.ret == null ? RUPA.abu
      : (n.ret >= 0 ? RUPA.tulang : RUPA.merah);
    g.fillText(label, taruh.cx, taruh.cy);
  }

  const ket = $('#petaKet');
  if (!ket) return;
  if (!panas.ada) {
    ket.innerHTML = '<em>sesi biasa \u2014 tidak ada wilayah yang keluar dari kebiasaannya</em>';
  } else {
    ket.innerHTML = panas.urut.slice(0, 3).map(([w, z]) =>
      `<span class="wil ${w === 'ID' ? 'w-rumah' : 'w-luar'}">${esc(LABEL_WIL[w] || w)}`
      + ` <b>${z.toFixed(1)}\u03c3</b></span>`).join('')
      + (panas.basi ? ' <em>(sesi berberita terakhir)</em>' : '');
  }
}

/* ---------- putar otomatis ------------------------------------------------
   Ini yang bikin "seiring berjalannya hari" kelihatan. Panel berita sengaja
   TIDAK ikut disegarkan tiap langkah: dia menarik berkas bulanan, dan pada
   tujuh langkah per detik itu jadi antrean fetch yang tidak pernah terkejar.
   Chart, peta, dan kepala panel sudah cukup untuk membaca geraknya; panelnya
   menyusul begitu diberhentikan. */
const PUTAR_MS = 145;

function setPutar(nyala) {
  if (S.putar) { clearInterval(S.putar); S.putar = null; }
  if (nyala) {
    if (!S.pin) S.pin = hariAktif() || S.spine[S.i0];
    $('#crosshair').classList.add('pin');
    S.putar = setInterval(langkahPutar, PUTAR_MS);
  } else if (S.pin) {
    isiPanel(S.pin);
  }
  const b = $('#putar');
  if (b) {
    b.setAttribute('aria-pressed', !!S.putar);
    b.textContent = S.putar ? '\u25A0 STOP' : '\u25B6 PUTAR';
  }
}

function langkahPutar() {
  const i = S.spine.indexOf(S.pin);
  if (i < 0 || i + 1 >= S.i1) { setPutar(false); return; }
  S.pin = S.spine[i + 1];
  S.hover = S.pin;
  gambarChart(); gambarDivergensi(); gambarRibbon(); gambarPeta();
  kepalaPanel(S.pin);
}

/* ---------- ribbon berita ------------------------------------------------- */
/* Batang bertumpuk per skala. Ini yang bikin pemisahan makro/mikro kelihatan
   sebagai deret waktu: hari yang tinggi tapi hampir seluruhnya ungu berarti
   hari itu ramai berita emiten, bukan hari yang menggerakkan papan. */
function gambarRibbon() {
  const { g, W, H } = siapkan($('#ribbon'));
  const tgl = S.spine.slice(S.i0, S.i1);
  if (!tgl.length) return;

  const maksN = Math.max(1, ...tgl.map((t) => S.hari[t]?.n || 0));
  const lebar = Math.max(1, (W - PAD.l - PAD.r) / tgl.length * 0.86);
  const sorot = S.pin || S.hover;
  const lapis = ['UMUM', 'MIKRO', 'MAKRO'];

  for (let i = 0; i < tgl.length; i++) {
    const h = S.hari[tgl[i]];
    const x = xDari(S.i0 + i, W);
    if (!h || !h.n) {
      g.fillStyle = '#1A1917';
      g.fillRect(x - lebar / 2, H - 3, lebar, 2);
      continue;
    }
    const sk = h.sk || { UMUM: h.n };
    const total = h.n || 1;
    const tinggi = Math.max(3, (h.n / maksN) * (H - 5));
    g.globalAlpha = tgl[i] === sorot ? 1 : 0.72;
    let y = H - 2;
    for (const nama of lapis) {
      const bagian = (sk[nama] || 0) / total * tinggi;
      if (bagian <= 0) continue;
      g.fillStyle = WARNA_SKALA[nama];
      g.fillRect(x - lebar / 2, y - bagian, lebar, bagian);
      y -= bagian;
    }
  }
  g.globalAlpha = 1;
}

/* ---------- panel kanan --------------------------------------------------- */
async function bulanData(bln) {
  if (S.bulanCache.has(bln)) return S.bulanCache.get(bln);
  const p = fetch(`data/berita/${bln}.json`)
    .then((r) => (r.ok ? r.json() : {}))
    .catch(() => ({}));
  S.bulanCache.set(bln, p);
  return p;
}

/* --- kesimpulan lintas-sumber -------------------------------------------
   Semua angka di sini dihitung di collector (sintesis.py) dari judul-judul
   hari itu; halaman ini tidak menafsirkan apa pun, cuma menampilkan.
   ------------------------------------------------------------------------ */
function gambarSintesis(h, t) {
  const el = $('#pSintesis');
  const s = h && h.sin;
  if (!s) {
    el.innerHTML = '<span class="kosong-kecil">belum ada kesimpulan untuk sesi ini</span>';
    return;
  }
  const baris = [];

  // nada: proporsi judul makro bernada naik vs turun
  const berarah = s.naik + s.turun;
  if (berarah) {
    const pn = Math.round(s.naik / berarah * 100);
    baris.push(`<div class="baris"><span class="tanda">NADA</span>
      <span class="isi" style="display:flex;gap:7px;align-items:center">
        <span class="meter"><i class="n" style="width:${pn}%"></i><i class="t" style="width:${100 - pn}%"></i></span>
        <span><b class="naik">${s.naik} naik</b> · <b class="turun">${s.turun} turun</b>
        <span class="kosong-kecil">dari ${berarah} judul makro berarah</span></span>
      </span></div>`);
  }

  if (s.dominan) {
    baris.push(`<div class="baris"><span class="tanda">DOMINAN</span>
      <span class="isi"><b>${esc(s.dominan[0])}</b>
      <span class="kosong-kecil">diangkat ${s.dominan[1]} situs</span></span></div>`);
  }

  if (s.baru && s.baru.length) {
    baris.push(`<div class="baris"><span class="tanda">BARU</span><span class="isi">${
      s.baru.map((x) => `<span class="tema-tag baru">${esc(x)}</span>`).join('')
    } <span class="kosong-kecil">absen di 5 sesi sebelumnya</span></span></div>`);
  }

  // tema hari ini + event-study kalau arsipnya sudah cukup panjang
  const temaStat = (S.tema && S.tema.tema) || {};
  if (s.tema && s.tema.length) {
    baris.push(`<div class="baris"><span class="tanda">TEMA</span><span class="isi">${
      s.tema.map((x) => {
        const st = temaStat[x];
        const judul = st
          ? `median IHSG pada ${st.n} sesi bertema ini: ${pct(st.median)} (basis ${pct(S.tema.dasar)})`
          : 'belum cukup sampel untuk event-study';
        const angka = st ? `<span class="n ${kelas(st.median)}">${pct(st.median)}</span>` : '';
        return `<span class="tema-tag" title="${esc(judul)}">${esc(x)}${angka}</span>`;
      }).join('')
    }</span></div>`);
  }

  // emiten paling ramai hari itu -> klik lompat ke tab MIKRO yang terfilter
  if (s.emiten && s.emiten.length) {
    baris.push(`<div class="baris"><span class="tanda">EMITEN</span><span class="isi">${
      s.emiten.map(([k, n, naik, turun]) => {
        const ar = naik > turun ? '<span class="ar naik">▲</span>'
          : turun > naik ? '<span class="ar turun">▼</span>' : '';
        return `<button class="emi-chip" data-e="${esc(k)}"
          title="${esc(namaEmiten(k))} — ${n} berita">${esc(k)}<span class="n">${n}</span>${ar}</button>`;
      }).join('')
    }</span></div>`);
  }

  baris.push(`<div class="baris"><span class="tanda">LIPUTAN</span><span class="isi">
    <b>${s.situs}</b> situs · korroborasi <b>${s.korr}%</b>
    <span class="kosong-kecil">(berita yang diangkat lebih dari satu situs)</span>
    </span></div>`);

  el.innerHTML = baris.join('');
}

function perbaruiTab(h) {
  const sk = (h && h.sk) || {};
  const jml = { MAKRO: sk.MAKRO || 0, MIKRO: sk.MIKRO || 0,
                SEMUA: (h && h.n) || 0 };
  $('#pTab').querySelectorAll('.tab').forEach((b) => {
    b.setAttribute('aria-pressed', b.dataset.t === S.tab);
    b.innerHTML = `${b.dataset.t}<span class="n">${jml[b.dataset.t]}</span>`;
  });
}

/** Satu kejadian = satu kartu; sumber lain jadi daftar anak di bawahnya. */
function kartu(g, indukKode) {
  const a = g[0], lain = g.slice(1);
  // Di dalam blok BBRI, mengulang tag "BBRI" di tiap kartu cuma bising. Yang
  // berguna justru kode LAIN yang ikut disebut judul yang sama.
  const tik = (a.e || []).filter((k) => k !== indukKode).map((k) =>
    `<span class="tik" title="${esc(namaEmiten(k))}">${esc(k)}</span>`).join('');
  // Kategori "lainnya" tidak menambah apa-apa di panel emiten; kartunya sudah
  // jelas milik siapa dari blok tempatnya berdiri.
  const kat = (indukKode && a.k === 'LAINNYA') ? ''
    : `<span class="kat" style="color:${WARNA_KAT[a.k] || RUPA.abu}">${LABEL_KAT[a.k] || a.k}</span>`;
  return `<article class="kartu" style="border-left-color:${WARNA_KAT[a.k] || RUPA.abu}">
    <div class="judul"><a href="${esc(a.u)}" target="_blank" rel="noopener noreferrer">${esc(a.j)}</a></div>
    ${a.r ? `<div class="ring">${esc(a.r)}</div>` : ''}
    <div class="kaki">
      ${tik}${kat}
      <span class="sumber">${esc(a.nm)}</span>
      <span>${jamDari(a.t)}</span>
      ${a.lj ? '<span class="luar" title="terbit di luar jam bursa, dampaknya masuk ke sesi ini">luar jam</span>' : ''}
      ${lain.length ? `<span>+${lain.length} sumber</span>` : ''}
    </div>
    ${lain.length ? `<div class="lain">${lain.map((x) =>
      `<a href="${esc(x.u)}" target="_blank" rel="noopener noreferrer">${esc(x.j)}
        <span class="dom">${esc(x.nm)} · ${jamDari(x.t)}</span></a>`).join('')}</div>` : ''}
  </article>`;
}

/** Kumpulan artikel -> daftar klaster, terurut skor. */
function klasterkan(arts) {
  const grup = new Map();
  for (const a of arts) {
    const k = a.c || a.id;
    if (!grup.has(k)) grup.set(k, []);
    grup.get(k).push(a);
  }
  return [...grup.values()]
    .map((g) => g.sort((x, y) => y.s - x.s))
    .sort((a, b) => b[0].s - a[0].s);
}

function daftarMakro(arts) {
  const per = new Map();
  for (const a of arts) {
    if (!per.has(a.k)) per.set(a.k, []);
    per.get(a.k).push(a);
  }
  const urut = [...per.keys()].sort((a, b) => URUT_KAT.indexOf(a) - URUT_KAT.indexOf(b));
  return urut.map((k) => {
    const g = klasterkan(per.get(k));
    return `<div class="grup-kepala">
        <span class="kode" style="color:${WARNA_KAT[k]}">${LABEL_KAT[k] || k}</span>
        <span class="hit">${per.get(k).length} berita · ${g.length} kejadian</span>
      </div>${g.map(kartu).join('')}`;
  }).join('');
}

/* Panel MIKRO: satu blok per emiten. Judul yang menyebut beberapa kode muncul
   di tiap bloknya — itu memang yang dicari: "hari ini BBRI diberitakan apa
   saja", bukan "berita ini punya siapa". */
function daftarMikro(arts, h) {
  const per = new Map();
  const tanpaKode = [];
  for (const a of arts) {
    if (!a.e || !a.e.length) { tanpaKode.push(a); continue; }
    for (const k of a.e) {
      if (!per.has(k)) per.set(k, []);
      per.get(k).push(a);
    }
  }
  const nadaEmiten = {};
  for (const [k, n, naik, turun] of ((h && h.sin && h.sin.emiten) || [])) {
    nadaEmiten[k] = [naik, turun];
  }
  const kode = [...per.keys()].sort((a, b) => {
    const d = per.get(b).length - per.get(a).length;
    return d || Math.max(...per.get(b).map((x) => x.s)) - Math.max(...per.get(a).map((x) => x.s));
  });

  const blok = kode.map((k) => {
    const g = klasterkan(per.get(k));
    const [naik, turun] = nadaEmiten[k] || [0, 0];
    const arah = (naik ? `<span class="up">▲${naik}</span> ` : '')
               + (turun ? `<span class="dn">▼${turun}</span> ` : '');
    return `<div class="grup-kepala">
        <span class="kode">${esc(k)}</span>
        <span class="nm">${esc(namaEmiten(k))}</span>
        <span class="sek">${esc(sektorEmiten(k))}</span>
        <span class="hit">${arah}${per.get(k).length} berita</span>
      </div>${g.map((x) => kartu(x, k)).join('')}`;
  });

  if (tanpaKode.length) {
    blok.push(`<div class="grup-kepala">
        <span class="kode" style="color:var(--k-emiten)">AKSI KORPORASI</span>
        <span class="nm">tanpa kode saham di judul</span>
        <span class="hit">${tanpaKode.length} berita</span>
      </div>${klasterkan(tanpaKode).map(kartu).join('')}`);
  }
  return blok.join('');
}

function gambarFilter(arts) {
  const el = $('#pFilter');
  if (S.tab === 'MIKRO') {
    const hitung = {};
    for (const a of arts) for (const k of (a.e || [])) hitung[k] = (hitung[k] || 0) + 1;
    const kode = Object.keys(hitung).sort((a, b) => hitung[b] - hitung[a]).slice(0, 14);
    el.innerHTML = (S.filter.size ? '<button class="chip reset" data-k="*">semua ✕</button>' : '')
      + kode.map((k) => bikinChip(k, `${esc(k)} ${hitung[k]}`, esc(namaEmiten(k)))).join('');
    return;
  }
  const hitung = {};
  for (const a of arts) hitung[a.k] = (hitung[a.k] || 0) + 1;
  el.innerHTML = Object.keys(hitung)
    .sort((a, b) => URUT_KAT.indexOf(a) - URUT_KAT.indexOf(b))
    .map((k) => bikinChip(k, `${LABEL_KAT[k] || k} ${hitung[k]}`, '',
                          WARNA_KAT[k] || RUPA.abu)).join('');
}

/* Sebelumnya semua chip tampil "terpilih" selama belum ada filter -- sebaris
   kotak menyala yang tidak menyampaikan apa-apa, karena memang tidak ada
   yang sedang disaring. Sekarang terpilih artinya benar-benar terpilih:
   tanpa filter semua netral, begitu satu dipilih sisanya meredup. */
function bikinChip(k, isi, judul, warna) {
  const on = S.filter.has(k);
  const kelasnya = 'chip' + (on ? '' : S.filter.size ? ' redup' : '');
  const titik = warna ? `<i class="dot" style="background:${warna}"></i>` : '';
  return `<button class="${kelasnya}" data-k="${k}" aria-pressed="${on}"`
       + (judul ? ` title="${judul}"` : '') + `>${titik}${isi}</button>`;
}

/* Kepala panel dipisah dari isinya supaya PUTAR bisa memperbaruinya tiap
   langkah tanpa ikut menarik berkas berita bulanan. */
function kepalaPanel(t) {
  const h = S.hari[t];
  $('#pTanggal').textContent = tglPanjang(t);
  $('#unpin').hidden = !S.pin;

  const dv = divHari(t);
  const acuan = S.refDiv === 'asia' ? 'vs Asia' : 'vs S&P';
  $('#pAngka').innerHTML = [
    h?.mendatang
      ? '<span class="mendatang">SESI BELUM BERJALAN — BERITA SUDAH TERKUMPUL</span>'
      : `<span>IHSG <b>${fmt(nilaiPada('IHSG', t))}</b> <b class="${kelas(h?.r)}">${pct(h?.r)}</b></span>`,
    dv != null ? `<span>DIV ${acuan} <b class="${kelas(dv)}">${pct(dv)}</b></span>` : '',
    h?.n ? `<span>${h.n} berita</span>` : '<span>tidak ada berita</span>',
  ].filter(Boolean).join('');
}

async function isiPanel(t) {
  if (!t) return;
  const tok = ++S.panelTok;
  const h = S.hari[t];
  kepalaPanel(t);
  gambarSintesis(h, t);
  perbaruiTab(h);

  const isi = $('#pIsi');
  if (!h || !h.n) {
    isi.innerHTML = '<div class="kosong">Belum ada berita terarsip untuk sesi ini.</div>';
    $('#pFilter').innerHTML = '';
    return;
  }

  const semua = (await bulanData(t.slice(0, 7)))[t] || [];
  // Scrub cepat memicu banyak fetch sekaligus; tanpa penjaga ini, jawaban
  // bulan lama bisa mendarat setelah hari sudah berpindah dan panelnya
  // menampilkan berita hari yang salah.
  if (tok !== S.panelTok) return;
  if (!semua.length) {
    isi.innerHTML = '<div class="kosong">Belum ada berita terarsip untuk sesi ini.</div>';
    $('#pFilter').innerHTML = '';
    return;
  }

  const perTab = S.tab === 'SEMUA' ? semua
    : semua.filter((a) => (a.sk || 'UMUM') === S.tab);
  gambarFilter(perTab);

  let pakai = perTab;
  if (S.filter.size) {
    pakai = S.tab === 'MIKRO'
      ? perTab.filter((a) => (a.e || []).some((k) => S.filter.has(k)))
      : perTab.filter((a) => S.filter.has(a.k));
  }

  if (!pakai.length) {
    isi.innerHTML = `<div class="kosong">Tidak ada berita ${S.tab.toLowerCase()} di sesi ini.<br>
      <span style="color:var(--redup2)">Coba tab lain di atas.</span></div>`;
    return;
  }

  isi.innerHTML = S.tab === 'MIKRO' ? daftarMikro(pakai, h)
    : S.tab === 'MAKRO' ? daftarMakro(pakai)
    : klasterkan(pakai).map(kartu).join('');
  isi.scrollTop = 0;
}

const hariAktif = () => S.pin || S.hover || S.spine[S.i1 - 1];

function gantiTab(nama, kodeEmiten) {
  S.tab = nama;
  S.filter = new Set(kodeEmiten ? [kodeEmiten] : []);
  isiPanel(hariAktif());
}

/* ---------- interaksi ----------------------------------------------------- */
function setRentang(kode) {
  S.rentang = kode;
  const n = RENTANG.find((r) => r[0] === kode)[1];
  S.i1 = S.spine.length;
  S.i0 = Math.max(0, S.i1 - (n === Infinity ? S.spine.length : n));
  if (!S.skalaManual) S.skala = sebaranBesar() ? 'log' : 'linear';
  render();
}

/** Apakah selisih terjauh-terdekat di jendela ini cukup lebar untuk perlu log? */
function sebaranBesar() {
  const tgl = S.spine.slice(S.i0, S.i1);
  let min = Infinity, max = -Infinity;
  for (const kode of S.urut) {
    if (!S.aktif.has(kode)) continue;
    const mentah = tgl.map((t) => nilaiPada(kode, t));
    const dasar = mentah.find((v) => v != null);
    if (!dasar) continue;
    for (const v of mentah) {
      if (v == null) continue;
      const r = v / dasar;
      if (r < min) min = r;
      if (r > max) max = r;
    }
  }
  return min !== Infinity && max / min > 3;
}

function render() {
  gambarChart(); gambarDivergensi(); gambarRibbon(); gambarPeta();
  $('#rentang').querySelectorAll('button').forEach((b) =>
    b.setAttribute('aria-pressed', b.dataset.r === S.rentang));
  $('#seri').querySelectorAll('button').forEach((b) => {
    b.setAttribute('aria-pressed', S.aktif.has(b.dataset.s));
    const kosong = S.tanpaData.has(b.dataset.s);
    b.classList.toggle('kosong', kosong);
    b.title = `${S.seri[b.dataset.s].nama} — ${S.seri[b.dataset.s].negara}`
      + (S.seri[b.dataset.s].lag ? ' (tutup setelah IDX)' : '')
      + (kosong ? ' — tidak ada data di rentang ini' : '');
  });
  $('#skala').setAttribute('aria-pressed', S.skala === 'log');
  $('#skala').textContent = S.skala === 'log' ? 'LOG' : 'LIN';
  $('#tglAlign').setAttribute('aria-pressed', S.dampak);
  $('#tglAlign').textContent = S.dampak ? 'DAMPAK' : 'TANGGAL';
  $('#refDiv').textContent = S.refDiv === 'asia' ? 'VS RERATA ASIA' : 'VS S&P 500';
  $('#refKet').textContent = S.refDiv === 'asia'
    ? 'IHSG dikurangi median Nikkei/SET/KOSPI/STI sesi yang sama'
    : 'IHSG dikurangi S&P 500 sesi sebelumnya';
}

function pasangInteraksi() {
  const wrap = $('#wrapChart'), ch = $('#crosshair');
  const posisi = (e) => {
    const r = wrap.getBoundingClientRect();
    const i = iDariX(e.clientX - r.left, r.width);
    return { i, t: S.spine[i], x: xDari(i, r.width) };
  };

  wrap.addEventListener('mousemove', (e) => {
    const p = posisi(e);
    if (!p.t) return;
    ch.style.display = 'block';
    ch.style.left = p.x + 'px';
    if (S.pin || p.t === S.hover) return;
    S.hover = p.t;
    gambarChart(); gambarDivergensi(); gambarRibbon(); gambarPeta(); isiPanel(p.t);
  });
  wrap.addEventListener('mouseleave', () => {
    if (S.pin) return;
    ch.style.display = 'none';
    S.hover = null; render();
  });
  wrap.addEventListener('click', (e) => {
    const p = posisi(e);
    if (!p.t) return;
    S.pin = S.pin === p.t ? null : p.t;
    ch.classList.toggle('pin', !!S.pin);
    S.hover = p.t; render(); isiPanel(p.t);
  });
  $('#unpin').addEventListener('click', () => {
    S.pin = null; ch.classList.remove('pin'); render();
  });

  $('#rentang').innerHTML = RENTANG.map(([k]) =>
    `<button class="pil" data-r="${k}">${k}</button>`).join('');
  $('#rentang').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (b) setRentang(b.dataset.r);
  });

  // tombol seri dibangun dari data: menambah bursa di config.py cukup
  $('#seri').innerHTML = S.urut.slice().reverse().map((k) =>
    `<button class="pil seri" data-s="${k}" title="${esc(S.seri[k].nama)} — ${esc(S.seri[k].negara)}${S.seri[k].lag ? ' (tutup setelah IDX)' : ''}"
       ><i class="dot" style="${swatch(S.seri[k].gaya)}"></i>${k}</button>`).join('');
  $('#seri').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return;
    const k = b.dataset.s;
    if (S.aktif.has(k)) S.aktif.delete(k); else S.aktif.add(k);
    render();
  });

  $('#tglAlign').addEventListener('click', () => { S.dampak = !S.dampak; render(); });
  $('#skala').addEventListener('click', () => {
    S.skala = S.skala === 'log' ? 'linear' : 'log';
    S.skalaManual = true;         // sekali dipilih tangan, berhenti ikut rentang
    render();
  });
  $('#refDiv').addEventListener('click', () => {
    S.refDiv = S.refDiv === 'asia' ? 'global' : 'asia';
    render(); isiPanel(hariAktif());
  });
  $('#bukaCmd').addEventListener('click', bukaCmd);

  $('#jejak').addEventListener('click', () => {
    S.jejak = !S.jejak;
    $('#jejak').setAttribute('aria-pressed', S.jejak);
    gambarPeta();
  });
  $('#putar').addEventListener('click', () => setPutar(!S.putar));

  $('#pTab').addEventListener('click', (e) => {
    const b = e.target.closest('.tab'); if (b) gantiTab(b.dataset.t);
  });
  $('#pSintesis').addEventListener('click', (e) => {
    const b = e.target.closest('.emi-chip'); if (b) gantiTab('MIKRO', b.dataset.e);
  });
  $('#pFilter').addEventListener('click', (e) => {
    const b = e.target.closest('.chip'); if (!b) return;
    const k = b.dataset.k;
    if (k === '*') S.filter.clear();
    else if (S.filter.has(k)) S.filter.delete(k);
    else S.filter.add(k);
    isiPanel(hariAktif());
  });

  let tempo;
  window.addEventListener('resize', () => { clearTimeout(tempo); tempo = setTimeout(render, 120); });
}

function kartuTicker(i) {
  return `<div class="tk" title="${esc(i.nama)} — ${esc(i.negara)}">
       <b>${i.kode}</b>
       <span class="v">${fmt(i.last)}</span>
       <span class="p ${kelas(i.ret)}">${pct(i.ret)}</span>
     </div>`;
}

function pasangHeader() {
  const utama = S.meta.indeks.find((i) => i.kode === 'IHSG');
  const sisa = S.meta.indeks.filter((i) => i.kode !== 'IHSG');
  $('#tickerPin').innerHTML = utama ? kartuTicker(utama) : '';
  // isinya digandakan supaya gulungannya menyambung tanpa jeda kosong
  const satu = sisa.map(kartuTicker).join('');
  $('#tickerJalan').innerHTML = satu + satu;
  $('#update').textContent = 'DATA ' + S.meta.diperbarui
    + (S.meta.sumber ? ` · ${S.meta.sumber.length} SITUS` : '');
  $('#ribLegend').innerHTML = [['MAKRO', 'makro'], ['MIKRO', 'emiten'], ['UMUM', 'umum']]
    .map(([k, l]) => `<span><i style="background:${WARNA_SKALA[k]}"></i>${l}</span>`).join('');

  const jam = () => {
    const d = new Date();
    const wib = new Date(d.getTime() + (d.getTimezoneOffset() + 420) * 60000);
    $('#jam').textContent = wib.toTimeString().slice(0, 8) + ' WIB';
  };
  jam(); setInterval(jam, 1000);
}

/* ---------- keyboard & command bar ---------------------------------------
   Bloomberg terasa seperti terminal bukan karena warnanya, tapi karena
   tangannya tidak perlu pindah ke mouse. Ini bagian itu.
   ------------------------------------------------------------------------ */
function pindahHari(langkah, hanyaPenting) {
  const kini = hariAktif();
  let i = S.spine.indexOf(kini);
  if (i < 0) i = S.i1 - 1;
  const arah = Math.sign(langkah);
  for (let n = 0; n < S.spine.length; n++) {
    i += arah;
    if (i < 0 || i >= S.spine.length) return;
    if (!hanyaPenting || S.hari[S.spine[i]]?.p) break;
  }
  pilihHari(S.spine[i]);
}

function pilihHari(t) {
  if (!t) return;
  const i = S.spine.indexOf(t);
  if (i < 0) return;
  // geser jendela kalau harinya di luar tampilan
  if (i < S.i0 || i >= S.i1) {
    const lebar = S.i1 - S.i0;
    S.i0 = Math.max(0, Math.min(i - Math.floor(lebar / 2), S.spine.length - lebar));
    S.i1 = Math.min(S.spine.length, S.i0 + lebar);
  }
  S.pin = t; S.hover = t;
  const ch = $('#crosshair');
  ch.style.display = 'block';
  ch.classList.add('pin');
  ch.style.left = xDari(i, $('#wrapChart').getBoundingClientRect().width) + 'px';
  render(); isiPanel(t);
}

function bukaCmd() {
  $('#cmdLapis').hidden = false;
  $('#cmdInput').value = '';
  $('#cmdHasil').innerHTML = '';
  $('#cmdInput').focus();
}
function tutupCmd() { $('#cmdLapis').hidden = true; $('#cmdInput').blur(); }

/** Cari sesi: tanggal persis, kode emiten, atau kata kunci tema/headline. */
function cariSesi(q) {
  q = q.trim().toLowerCase();
  if (!q) return [];
  const m = q.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
  if (m) {
    const t = `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`;
    const i = S.spine.findIndex((x) => x >= t);
    return i < 0 ? [] : [{ t: S.spine[i], jdl: S.hari[S.spine[i]]?.top?.[0]?.j || '(tanpa berita)' }];
  }
  // Kode emiten dicari lewat ringkasan harian, jadi tetap instan: tidak perlu
  // menarik berkas bulanan mana pun untuk tahu hari mana yang memuatnya.
  const kodeQ = q.toUpperCase();
  const adaEmiten = !!S.emiten[kodeQ];
  const out = [];
  for (let i = S.spine.length - 1; i >= 0 && out.length < 40; i--) {
    const t = S.spine[i], h = S.hari[t];
    if (!h || !h.n) continue;
    if (adaEmiten) {
      const e = (h.sin?.emiten || []).find((x) => x[0] === kodeQ);
      if (e) out.push({ t, jdl: `${kodeQ} · ${namaEmiten(kodeQ)} — ${e[1]} berita`, e: kodeQ });
      continue;
    }
    const tema = (h.sin?.tema || []).find((x) => x.toLowerCase().includes(q));
    const judul = (h.top || []).find((k) => k.j.toLowerCase().includes(q));
    if (tema || judul) out.push({ t, jdl: judul ? judul.j : `tema: ${tema}` });
  }
  return out;
}

function gambarHasilCmd(q) {
  const hasil = cariSesi(q);
  S.cmdHasil = hasil; S.cmdPilih = 0;
  $('#cmdHasil').innerHTML = hasil.length ? hasil.map((r, i) => {
    const h = S.hari[r.t];
    return `<div class="cmd-item${i === 0 ? ' pilih' : ''}" data-t="${r.t}" data-e="${esc(r.e || '')}">
      <span class="tgl">${r.t}</span>
      <span class="jdl">${esc(r.jdl.slice(0, 78))}</span>
      <span class="met ${kelas(h?.r)}">${pct(h?.r)}</span>
    </div>`;
  }).join('') : (q.trim() ? '<div class="cmd-item"><span class="jdl">tidak ada sesi yang cocok</span></div>' : '');
}

function bukaHasil(r) {
  tutupCmd();
  if (r.e) { S.tab = 'MIKRO'; S.filter = new Set([r.e]); }
  pilihHari(r.t);
}

function pasangKeyboard() {
  document.addEventListener('keydown', (e) => {
    const diInput = e.target === $('#cmdInput');
    if (diInput) {
      if (e.key === 'Escape') { tutupCmd(); return; }
      if (e.key === 'Enter') {
        const r = S.cmdHasil?.[S.cmdPilih || 0];
        if (r) bukaHasil(r);
        return;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        const n = (S.cmdHasil || []).length;
        if (!n) return;
        S.cmdPilih = (S.cmdPilih + (e.key === 'ArrowDown' ? 1 : n - 1)) % n;
        $('#cmdHasil').querySelectorAll('.cmd-item').forEach((el, i) =>
          el.classList.toggle('pilih', i === S.cmdPilih));
        return;
      }
      setTimeout(() => gambarHasilCmd($('#cmdInput').value), 0);
      return;
    }

    if (e.key === '/') { e.preventDefault(); bukaCmd(); return; }
    if (e.key === 'Escape' && !$('#cmdLapis').hidden) { tutupCmd(); return; }
    if (e.key === 'Escape') {
      S.pin = null; $('#crosshair').classList.remove('pin'); render(); return;
    }
    if (e.key === 'ArrowLeft')  { e.preventDefault(); pindahHari(-1, e.shiftKey); return; }
    if (e.key === 'ArrowRight') { e.preventDefault(); pindahHari(1, e.shiftKey); return; }
    if (e.key === 'Home') { e.preventDefault(); pilihHari(S.spine[S.i0]); return; }
    if (e.key === 'End')  { e.preventDefault(); pilihHari(S.spine[S.spine.length - 1]); return; }
    if (e.key === 'm' || e.key === 'M') { gantiTab('MAKRO'); return; }
    if (e.key === 'k' || e.key === 'K') { gantiTab('MIKRO'); return; }
    if (e.key === 'a' || e.key === 'A') { gantiTab('SEMUA'); return; }
    if (e.key === 'p' || e.key === 'P') {
      S.pin = S.pin ? null : (S.hover || S.spine[S.i1 - 1]);
      $('#crosshair').classList.toggle('pin', !!S.pin);
      render(); isiPanel(hariAktif()); return;
    }
    if (/^[1-9]$/.test(e.key)) {
      const kode = S.urut.slice().reverse()[+e.key - 1];
      if (!kode) return;
      if (S.aktif.has(kode)) S.aktif.delete(kode); else S.aktif.add(kode);
      render();
    }
  });

  $('#cmdLapis').addEventListener('click', (e) => {
    if (e.target === $('#cmdLapis')) tutupCmd();
  });
  $('#cmdHasil').addEventListener('click', (e) => {
    const it = e.target.closest('.cmd-item');
    if (it?.dataset.t) bukaHasil({ t: it.dataset.t, e: it.dataset.e || null });
  });
  $('#pIsi').addEventListener('click', (e) => {
    const k = e.target.closest('.kartu');
    if (k && e.target.tagName !== 'A') k.classList.toggle('buka');
  });
}

(async function main() {
  await muat();
  pasangHeader();
  pasangInteraksi();
  pasangKeyboard();
  setRentang('1T');
  // Hari terakhir yang benar-benar punya berita, bukan sekadar bar terakhir:
  // membuka terminal di hari kosong bikin panelnya terlihat rusak.
  const awal = S.spine.slice().reverse().find((t) => S.hari[t]?.n) || S.spine[S.spine.length - 1];
  pilihHari(awal);
})();
