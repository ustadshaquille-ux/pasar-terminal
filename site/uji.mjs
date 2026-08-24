/* Uji asap halaman, tanpa browser:  node uji.mjs
 *
 * Ada satu kelas bug yang tidak akan pernah tertangkap tests.py dan tidak
 * kelihatan waktu membaca kode: fungsi yang dipanggil tapi tidak pernah
 * didefinisikan. `gambarSintesis(h)` pernah hidup sebagai panggilan tanpa
 * badan selama berhari-hari — akibatnya isiPanel() melempar ReferenceError
 * di baris itu, dan SEMUA yang harusnya digambar sesudahnya (kesimpulan,
 * filter, seluruh daftar berita) tidak pernah muncul. Dari luar, halamannya
 * cuma terlihat "kosong kalau tanggalnya diklik".
 *
 * Jadi uji ini menjalankan app.js sungguhan di atas DOM tiruan seadanya,
 * memakai data JSON yang benar-benar diekspor, lalu memeriksa panel kanannya
 * berisi sesuatu. Kalau ada nama yang belum ada badannya, di sinilah pecah.
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const gagal = [];
const cek = (nama, syarat, ket = '') => {
  if (syarat) console.log('  ok    ' + nama);
  else { console.log('  GAGAL ' + nama + (ket ? '\n          ' + ket : '')); gagal.push(nama); }
};

/* ---------- DOM tiruan seperlunya ---------------------------------------- */
// Semua metode canvas jadi no-op, KECUALI yang mengembalikan nilai. Kalau
// measureText ikut mengembalikan undefined, kode gambar yang membaca .width
// meledak di uji padahal di peramban baik-baik saja.
const ctx2dNilai = {
  measureText: (s) => ({ width: String(s).length * 5 }),
};
const ctx2d = new Proxy({}, {
  get: (t, k) => (k in ctx2dNilai ? ctx2dNilai[k]
    : k in t ? t[k] : (t[k] = () => {})),
  set: (t, k, v) => { t[k] = v; return true; },
});

function buatEl(sel) {
  const el = {
    sel, innerHTML: '', textContent: '', hidden: false, value: '',
    style: {}, dataset: {}, scrollTop: 0,
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    setAttribute() {}, getAttribute: () => null, addEventListener() {},
    focus() {}, blur() {}, closest: () => null,
    getBoundingClientRect: () => ({ width: 1200, height: 500, left: 0, top: 0 }),
    getContext: () => ctx2d,
    querySelectorAll(q) {
      if (sel === '#pTab' && q === '.tab') {
        if (!el._tab) el._tab = ['MAKRO', 'MIKRO', 'SEMUA'].map((t) => {
          const b = buatEl('.tab'); b.dataset.t = t; return b;
        });
        return el._tab;
      }
      return [];
    },
  };
  return el;
}

const daftarEl = new Map();
const $$ = (sel) => {
  if (!daftarEl.has(sel)) daftarEl.set(sel, buatEl(sel));
  return daftarEl.get(sel);
};

const document = {
  querySelector: $$,
  addEventListener() {},
  createElement: () => buatEl('el'),
};

const sandbox = {
  document,
  window: { addEventListener() {}, devicePixelRatio: 1 },
  console,
  setTimeout: () => 0,
  clearTimeout: () => {},
  setInterval: () => 0,          // jam berdetak tidak perlu di uji
  Date, Math, JSON, Object, Array, Map, Set, Number, String, Promise, Infinity,
  fetch: async (f) => {
    const p = path.join(DIR, f);
    if (!fs.existsSync(p)) return { ok: false, json: async () => ({}) };
    return { ok: true, json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) };
  },
};
sandbox.globalThis = sandbox;

const kode = fs.readFileSync(path.join(DIR, 'app.js'), 'utf8')
  + '\n;globalThis.__uji = { S, isiPanel, gantiTab, cariSesi, gambarSintesis,'
  + ' panasWilayah, sesiBerberita, langkahPutar, setPutar, WARNA_KAT };\n';

console.log('\n[halaman] app.js dijalankan di atas data yang benar-benar diekspor');
try {
  vm.runInNewContext(kode, sandbox, { filename: 'app.js' });
} catch (e) {
  console.log('  GAGAL app.js meledak saat dimuat: ' + e.message);
  process.exit(1);
}

// beri kesempatan main() dan fetch-nya selesai
await new Promise((r) => setTimeout(r, 400));

const { S, isiPanel, gantiTab, cariSesi, panasWilayah, sesiBerberita,
        langkahPutar, setPutar } = sandbox.__uji;
const panel = () => $$('#pIsi').innerHTML;
const sintesis = () => $$('#pSintesis').innerHTML;

cek('data termuat', !!S.meta && S.spine.length > 100);
cek('daftar emiten termuat', Object.keys(S.emiten).length > 50);

const hariBerita = S.spine.slice().reverse().find((t) => S.hari[t]?.n);
await isiPanel(hariBerita);

console.log('\n[panel] hari dengan berita: ' + hariBerita);
cek('kartu berita tergambar', panel().includes('class="kartu"'),
    'isi panel: ' + panel().slice(0, 120));
cek('panel kesimpulan terisi', sintesis().includes('LIPUTAN'),
    'isi sintesis: ' + sintesis().slice(0, 120));
cek('nada dihitung', sintesis().includes('NADA') || sintesis().includes('DOMINAN'));
cek('tanggal tertulis di kepala panel', /\d{4}/.test($$('#pTanggal').textContent));
cek('angka IHSG tertulis', $$('#pAngka').innerHTML.includes('IHSG')
    || $$('#pAngka').innerHTML.includes('SESI BELUM'));

console.log('\n[panel] tab MIKRO');
await gantiTab('MIKRO');
await new Promise((r) => setTimeout(r, 250));
const adaMikro = (S.hari[hariBerita].sk || {}).MIKRO > 0;
cek('blok per emiten muncul',
    !adaMikro || panel().includes('grup-kepala'), panel().slice(0, 160));
cek('kode saham tampil di kepala blok',
    !adaMikro || /class="kode">[A-Z]{4}</.test(panel()), panel().slice(0, 160));

console.log('\n[panel] tab MAKRO');
await gantiTab('MAKRO');
await new Promise((r) => setTimeout(r, 250));
cek('berita makro dikelompokkan per kategori', panel().includes('grup-kepala'));
cek('tidak ada berita emiten yang bocor ke tab makro',
    !panel().includes('AKSI KORPORASI'));

console.log('\n[panel] hari tanpa berita tidak boleh meledak');
const hariKosong = S.spine.find((t) => !S.hari[t]?.n);
await isiPanel(hariKosong);
cek('pesan kosong yang jelas', panel().includes('Belum ada berita'));

console.log('\n[cari] command bar');
const kodeRamai = (S.hari[hariBerita].sin?.emiten || [])[0]?.[0];
cek('cari kode saham menemukan sesi',
    !kodeRamai || cariSesi(kodeRamai).length > 0, 'kode diuji: ' + kodeRamai);
cek('cari tanggal menemukan sesi', cariSesi(hariBerita).length === 1);
cek('cari tema menemukan sesi', cariSesi('rupiah').length > 0);
cek('cari ngawur tidak menemukan apa pun', cariSesi('zzzqqq').length === 0);

console.log('\n[peta] panas wilayah = keluar dari kebiasaan, bukan jumlah');
cek('kisi peta termuat', !!S.peta && S.peta.sel.length > 40 && S.peta.bursa.length > 0);
cek('tiap baris kisi selebar kolom',
    S.peta.sel.every((b) => b.length === S.peta.kolom));
cek('semua huruf wilayah dikenali',
    [...new Set(S.peta.sel.join(''))].every((c) => c === '.' || c === 'X' || S.peta.huruf[c]));

const sesiN = sesiBerberita();
cek('ada cukup sesi berberita buat baseline', sesiN.length > 60,
    'sesi berberita: ' + sesiN.length);

// Kalau yang digambar jumlah mentah, Indonesia menang tiap hari dan petanya
// tidak pernah memberi tahu apa pun. Yang diuji bukan satu sesi (ID memang
// boleh jadi anomali terbesar di sesi tertentu) melainkan sifatnya sepanjang
// arsip: pemenang mentah dan pemenang panas harus SERING berbeda.
let beda = 0, punya = 0, idMentahMenang = 0;
for (const t of sesiN) {
  const w = S.hari[t].w || {};
  const isi = Object.entries(w).sort((a, b) => b[1] - a[1]);
  if (!isi.length) continue;
  const p = panasWilayah(t);
  if (!p.ada) continue;
  punya++;
  if (isi[0][0] === 'ID') idMentahMenang++;
  if (isi[0][0] !== p.urut[0][0]) beda++;
}
cek('jumlah mentah memang didominasi Indonesia', idMentahMenang / punya > 0.8,
    `ID menang mentah di ${idMentahMenang}/${punya} sesi`);
cek('panas TIDAK sekadar mengikuti jumlah mentah', beda / punya > 0.35,
    `pemenang berbeda di ${beda}/${punya} sesi`);

const sesiUji = sesiN[sesiN.length - 1];
const panas = panasWilayah(sesiUji);
cek('nilai panas ternormalkan 0..1',
    Object.values(panas.nilai).every((v) => v >= 0 && v <= 1.0001));
cek('hasilnya deterministik (dipanggil dua kali sama)',
    JSON.stringify(panasWilayah(sesiUji)) === JSON.stringify(panas));

S.jejak = true;
S.panasCache.clear();
const jejak = panasWilayah(sesiUji);
cek('mode JEJAK menyalakan wilayah minimal sebanyak mode HARI',
    jejak.urut.length >= panas.urut.length,
    `hari=${panas.urut.length} jejak=${jejak.urut.length}`);
S.jejak = false;
S.panasCache.clear();

console.log('\n[peta] putar otomatis');
S.pin = S.spine[S.i1 - 3];
langkahPutar();
cek('putar memajukan satu sesi', S.pin === S.spine[S.i1 - 2]);
S.pin = S.spine[S.i1 - 1];
langkahPutar();
cek('putar berhenti di ujung jendela, tidak keluar batas',
    S.pin === S.spine[S.i1 - 1] && !S.putar);
setPutar(false);
S.pin = null;

console.log();
if (gagal.length) {
  console.log(gagal.length + ' uji GAGAL: ' + gagal.join(', '));
  process.exit(1);
}
console.log('semua uji halaman lulus');
