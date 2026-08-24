# PASAR TERMINAL

Situs statis: chart IHSG disandingkan dengan bursa yang benar-benar berdampak
padanya, dengan berita Indonesia yang menempel di **hari bursa yang kena
akibatnya** — dipisah antara yang menggerakkan seluruh papan dan yang cuma
menggerakkan satu saham.

Datanya diperbarui sendiri oleh GitHub Actions. Tidak ada server yang perlu
dibayar, tidak ada scraper yang perlu dijalankan dari komputer sendiri.

---

## Kenapa bentuknya begini

**Semua indeks di-rebase ke 100.** Menaruh IHSG (~6.500) dan Nikkei (~66.000)
di satu sumbu harga itu bohong visual. Setelah di-rebase ke awal rentang, yang
terbaca adalah hal yang sebenarnya ingin diketahui: siapa mengungguli siapa.
Tiap indeks bisa dimatikan-nyalakan sendiri lewat tombol di toolbar.

**Bursa dipilih dari pengukuran, bukan tebakan.** Korelasi return harian
terhadap IHSG, Agustus 2023–Agustus 2026 (Asia sejajar hari yang sama, AS
digeser D−1):

| Indeks | Negara | Korelasi | Dipakai |
|---|---|--:|:--:|
| SET | Thailand | 0,349 | ya |
| KOSPI | Korea | 0,327 | ya |
| STI | Singapura | 0,312 | ya |
| Nikkei 225 | Jepang | 0,302 | ya |
| KLCI | Malaysia | 0,299 | tidak |
| S&P 500 | AS | 0,237 | ya |
| Sensex | India | 0,231 | tidak |
| Nasdaq | AS | 0,228 | ya |
| Hang Seng | Hong Kong | 0,181 | tidak |
| Shanghai | China | 0,118 | tidak |

Hasil yang berlawanan dengan dugaan umum: **tetangga ASEAN/Asia lebih
menempel ke IHSG daripada Wall Street**, dan China justru paling lemah meski
ia mitra dagang terbesar. Hang Seng, Shanghai, KLCI, dan Sensex sengaja tidak
dipakai; menambahkannya cukup satu baris di `INDICES`.

**Divergensi punya panel sendiri, dengan dua acuan.** Ini penyaring utamanya:
dari ratusan hari bursa, batang panjang menandai hari ketika IHSG lepas dari
arah kawanan — di situlah berita lokal yang menentukan.

- *vs rerata Asia* (bawaan) — IHSG dikurangi **median** Nikkei/SET/KOSPI/STI
  sesi yang sama. Median, bukan rata-rata, supaya satu bursa yang datanya
  bolong tidak menyeret hasilnya.
- *vs S&P 500* — IHSG dikurangi S&P sesi sebelumnya, selera risiko global.

Keduanya perlu, karena sering berbeda jauh. 19 Agustus 2026: IHSG −0,86%,
dibanding S&P cuma −0,18 (terlihat biasa saja), tapi dibanding Asia **+2,30**
— kawasan jatuh jauh lebih dalam dan IHSG justru bertahan. Sinyal itu hilang
kalau acuannya hanya Amerika.

**Berita menempel ke sesi bursa, bukan ke tanggal terbitnya.** Artikel yang
terbit 19:00 Selasa tidak menggerakkan candle Selasa — dia menggerakkan Rabu.
Berita Sabtu menempel ke Senin. Kartunya diberi tanda `luar jam` supaya
perbedaan itu tetap terlihat, bukan disembunyikan.

**Geseran waktu dihitung per bursa, bukan disamaratakan.** Wall Street tutup
04:00 WIB besok paginya, jadi close S&P tanggal D baru bisa dicerna IDX di
sesi D+1 (`lag: 1`). Tapi bursa Asia sudah selesai sebelum IDX tutup — Nikkei
13:00 WIB, KOSPI 13:30, Shanghai 14:00, Hang Seng 15:00, STI 16:00 — jadi
mereka dipakai apa adanya (`lag: 0`). Menyamaratakan geseran untuk semua
bursa asing membalik arah sebab-akibat untuk separuh daftarnya. Tombol
`sejajar dampak` / `sejajar tanggal` mematikan atau menyalakan koreksi ini.

**Makro dan mikro dipisah, karena itu dua pertanyaan berbeda.** "Apa yang
menggerakkan papan hari ini" dan "saham apa yang ramai hari ini" tidak bisa
dijawab satu daftar. Dicampur, keduanya tenggelam: lima pengumuman dividen
berdesakan dengan satu keputusan suku bunga, dan yang terbaca cuma yang paling
banyak. Jadi tiap artikel punya dua label — **kategori** (soal apa) dan
**skala** (seluas apa):

- **MAKRO** — IHSG, rupiah, BI, The Fed, komoditas, kebijakan bursa.
- **MIKRO** — ada emiten tertentu di judulnya. Panelnya dikelompokkan per kode
  saham, lengkap dengan nama dan sektornya, diurut dari yang paling banyak
  diberitakan.
- **UMUM** — ekonomi umum dan sisanya. Tidak dibuang, cuma tidak ikut menonjol.

Berita emiten sengaja **tidak boleh jadi headline hari**; kalau boleh, hari
dengan lima rilis dividen menutupi hari ketika BI memangkas suku bunga.

**Emiten dikenali tiga jalur, dan daftarnya tumbuh sendiri.** Kode dalam
kurung ("Adhi Karya (ADHI)") nyaris selalu benar — dan sekalian dipakai
mempelajari nama emitennya, jadi kode yang belum pernah dikurasi tetap
terbaca di judul berikutnya. Kode berdiri sendiri ("Saham BBRI Diborong
Asing") hanya diterima kalau kodenya sudah dikenal: tanpa syarat itu IHSG,
BUMN, UMKM, APBN, dan puluhan akronim empat huruf lain ikut terbaca sebagai
emiten — di arsip ini IHSG saja muncul 237 kali. Jalur ketiga nama perusahaan,
karena mayoritas judul Indonesia menyebut "Bank Mandiri", bukan "BMRI".

Dua jebakan yang sudah ada penangkalnya, jangan dilepas:

- **"mandiri" itu kata sifat biasa.** Aliasnya harus "bank mandiri". Begitu
  juga "bri" yang harus dicocokkan sebagai kata utuh, kalau tidak "BRIN"
  (badan riset) ikut terbaca sebagai bank.
- **"Harga Emas Antam Hari Ini Naik" itu berita komoditas, bukan saham ANTM.**
  Pola ini muncul 83 kali di arsip — cukup untuk menenggelamkan seluruh panel
  emiten. Pengecualiannya berlaku khusus temuan lewat nama; kalau kodenya yang
  tertulis ("Saham ANTM Melesat Ikut Harga Emas"), itu memang berita sahamnya.

**Rilis humas ditahan, bukan dibuang.** Satu bank besar bisa mengeluarkan lima
rilis penghargaan dalam sehari. Kalau skornya sejajar, "BRI Sabet 6
Penghargaan" duduk di atas "Laba BRI Turun 8%". Kata seperti *penghargaan,
sabet, award, CSR, turnamen* menahan skornya di bawah ambang headline, jadi
kartunya turun ke dasar bloknya dan tetap bisa dibaca.

**Kesimpulan lintas-sumber dihitung, bukan ditafsirkan.** Situsnya statis dan
tidak memanggil model bahasa apa pun, jadi tiap angka di panel kesimpulan bisa
dilacak balik ke judul yang menghasilkannya:

- **Nada** — berapa judul bernada naik vs turun, dari leksikon verba pasar
  (`menguat/melesat/rebound` vs `anjlok/terkoreksi/tertekan`). Dicocokkan
  sebagai **kata utuh**: tanpa itu "Suku Bunga **Acuan**" terbaca positif
  karena mengandung "cuan", dan "ke**turun**an" terbaca negatif.
- **Dominan** — tema yang diangkat paling banyak **situs**, bukan paling banyak
  artikel. Satu situs yang menulis lima kali bukan konsensus.
- **Baru** — tema yang muncul hari ini tapi absen di 5 sesi sebelumnya. Pasar
  bergerak karena informasi baru, bukan yang diulang-ulang.
- **Korroborasi** — berapa persen berita hari itu diangkat lebih dari satu
  situs. Rendah = hari sepi, beritanya bising saja.

**Event-study per tema, dengan basis se-periode.** Kalau sebuah tema sudah
muncul cukup sering, ditampilkan median gerak IHSG pada sesi-sesi itu.
Pembandingnya **wajib** median sesi yang ada beritanya, bukan seluruh sejarah
IHSG: kalau arsip cuma menutupi satu jendela yang kebetulan pasar sedang naik,
membandingkannya dengan median 20 tahun bikin semua tema tampak positif — itu
bias seleksi, bukan temuan. Dengan basis salah, "APBN & fiskal" terbaca
+0,40%; dengan basis benar, +0,06%. Panelnya juga menutup diri sampai arsip
menutupi minimal 120 sesi, karena di bawah itu apa pun yang keluar cuma derau.

**Rangkanya tidak berwarna, isinya berwarna.** Itu satu-satunya aturan palet
di sini. Rangka — tombol, tab, chip, angka naik/turun, garis chart — cuma
hitam, tulang (putih hangat), dan merah. Tidak ada warna aksen antarmuka sama
sekali: yang aktif ditandai dengan **membalik bloknya** (latar tulang, teks
hitam), persis kursor terminal. Jadi tulang selalu berarti "naik / sehat /
sedang dipilih" dan merah selalu berarti "turun / risiko", tidak pernah
sekadar hiasan tombol.

Isinya baru berwarna, dan hue-nya menjawab **dari mana tekanannya datang**:

| | kategori | artinya |
|---|---|---|
| tulang | BURSA | pasar itu sendiri, bukan sebab dari luar |
| jingga | MAKRO DOM | dapur sendiri: BI, rupiah, inflasi, APBN |
| sian | MAKRO GLOBAL | datang dari luar: The Fed, tarif, Wall Street |
| biru | KEBIJAKAN | aturan main: OJK, IDX, pajak, POJK |
| kuningan | KOMODITAS | logam & tanah: emas, minyak, batu bara, CPO |
| hijau | EMITEN | satu perusahaan — sewarna dengan skala MIKRO |
| merah | POLITIK | risiko |

Hijau EMITEN dan hijau MIKRO sengaja satu warna: begitu pita **ALIRAN BERITA**
menghijau, kamu langsung tahu hari itu ramai berita korporasi, bukan hari yang
menggerakkan papan.

Indeks di chart dikecualikan dari semua itu — dibedakan dengan **tebal garis
dan pola putus-putus**, bukan warna. Yang perlu dibaca di chart itu *bentuk*
kurva, dan tujuh garis berwarna saling menutupi bentuk satu sama lain. Cara
ini tetap terbaca di cetakan hitam-putih dan untuk mata yang sulit membedakan
warna — dan menambah bursa baru di `config.py` tidak perlu memilih warna lagi,
polanya dibagikan otomatis dari `DEK_GARIS`.

Angka selalu monospace (IBM Plex Mono) supaya kolomnya rata: di font
proporsional "6.525,68" dan "17.685,00" punya lebar berbeda, jadi mata membaca
ulang tiap baris alih-alih memindai satu kolom. Kalimat dan judul berita
justru proporsional (Archivo), karena teks panjang dalam monospace melelahkan.

**PETA DAMPAK — dari sebelah mana anginnya datang.** Tiap artikel ditandai
wilayah yang disebut judulnya (boleh lebih dari satu: "Tarif Trump ke China
Bikin IHSG Anjlok" itu AS, China, dan Indonesia sekaligus), lalu peta titik
dunia menyalakan wilayah yang **keluar dari kebiasaannya sendiri**:

```
z = (hari ini − lazimnya) ÷ √(lazimnya + 2)
```

Yang digambar bukan jumlah berita. Kalau jumlah mentah yang dipakai, Indonesia
menyala penuh setiap hari dan peta ini tidak pernah memberi tahu apa pun —
5.062 dari 7.500 penyebutan wilayah di arsip memang Indonesia. Pembaginya akar
karena ini hitung-cacah (Poisson): wilayah yang biasanya 2 berita/hari memang
wajar melonjak ke 5, yang biasanya 40 tidak. "Lazimnya" diukur dari median 40
**sesi berberita** sebelumnya, bukan 40 hari kalender — arsipnya berlubang
(Nov 2025 lalu lompat ke Jan 2026) dan kalender membuat lubang itu terhitung
sebagai rentetan hari sepi.

Indonesia punya skala sendiri, terpisah dari dunia. Rumah selalu paling ramai,
jadi menormalkan luar negeri terhadap Indonesia membuat seluruh peta gelap
permanen — padahal "dari luar sebelah mana" justru satu-satunya hal yang tidak
bisa dibaca dari panel lain. Sekarang jingga menjawab *seberapa berisik di
rumah* dan sian menjawab *sebelah mana*, tanpa berebut sumbu yang sama.

Tombol **JEJAK** menjumlahkan 20 sesi ke belakang dengan peluruhan 0,85, dan
**▶ PUTAR** menjalankan sesi maju satu per satu. Dua-duanya dipakai bersamaan
untuk melihat sebuah tema *menyala pelan lalu padam*: satu berita tidak berarti
apa-apa, tiga minggu berita berturut-turut itu tema. Hitungannya deterministik
(tidak menyimpan sisa frame sebelumnya), jadi digeser mundur hasilnya sama.

Kisi petanya dibangun sekali (`python run.py peta`) dari garis pantai Natural
Earth 110m dan diarsip sebagai `site/data/peta.json` — 13 KB, dan situsnya
tidak pernah lagi menyentuh jaringan untuk itu. Titik kasar 2° dipilih bukan
cuma karena ringan: berita tidak punya koordinat, yang kita tahu cuma
"artikel ini menyebut China", dan menggambar batas negara dengan presisi
vektor itu berbohong tentang seberapa halus datanya.

**Ticker: IHSG dipaku, sisanya berjalan.** Angka di benda bergerak susah dibaca
justru saat dibutuhkan — itu sebabnya terminal sungguhan memakai grid statis,
dan yang berjalan di TV itu *lower third* CNBC. Jadi yang paling penting tidak
ikut jalan, dan gulungannya berhenti saat disentuh kursor.

**Keyboard dulu, mouse belakangan.** `←` `→` pindah hari · `shift`+`←` `→`
lompat ke hari signifikan berikutnya · `p` pin · `m` `k` `a` pindah panel
makro/mikro/semua · `1`–`7` nyalakan/matikan indeks · `esc` lepas pin ·
`/` command bar (tanggal untuk lompat, kata kunci untuk mencari sesi bertema
itu, atau **kode saham** untuk mencari sesi yang memberitakannya — pencarian
kode berjalan instan karena membaca ringkasan harian, tanpa menarik satu pun
berkas berita bulanan).

**Satu kejadian = satu kartu.** Berita yang sama diberitakan banyak situs
digabung jadi satu klaster; sumber lainnya jadi daftar anak di bawahnya,
lengkap dengan nama situs dan jamnya. Setiap judul tertaut ke situs aslinya.

---

## Sumber data

| Apa | Dari mana | Sejauh apa |
|---|---|---|
| Bar harian 7 indeks | Yahoo Finance (`^JKSE`, `^GSPC`, `^N225`, `^IXIC`, `^SET.BK`, `^KS11`, `^STI`) | 2006 → sekarang |
| Berita historis (tulang punggung) | Indeks harian Detik Finance, berpaginasi | ~120 artikel/hari |
| Berita historis (tulang punggung) | Indeks harian Liputan6 Bisnis, berpaginasi | ~65 artikel/hari |
| Berita historis (pendukung) | Indeks harian CNBC Indonesia | 10 artikel/hari |
| Berita berjalan | 17 feed RSS dari 13 situs (lihat di bawah) | terus-menerus |

Feed berjalan, dikelompokkan: **inti pasar** — Kontan (investasi, keuangan,
industri), CNBC Indonesia market, Bloomberg Technoz, IDX Channel, Pasardana,
Detik bursa & valas, Liputan6 saham. **Ekonomi umum** — Detik Finance,
Liputan6 bisnis, Katadata, CNN Indonesia, SindoNews Ekbis, Republika, Antara,
Tempo.

Sumber inti pasar itu yang paling banyak menyumbang berita MIKRO: gaya
penulisan judulnya menyertakan kode saham dalam kurung, persis pola yang
dibaca pendeteksi emiten.

Domain diambil dari URL artikelnya, bukan dari baris konfigurasi feed. Satu
situs boleh punya beberapa feed (Detik punya rubrik umum dan rubrik bursa),
dan kalau domainnya diambil dari konfigurasi, satu media tercatat sebagai dua
"sumber" — hitungan korroborasi lintas-situs jadi bohong.

Yang sudah dicoba dan **tidak** dipakai, supaya tidak dicoba lagi:

- **GDELT DOC API** — balas `429 Too Many Requests` terus-menerus dari IP rumahan.
  Layak dicoba ulang dari runner GitHub yang IP-nya berbeda.
- **Kontan indeks** — daftarnya dirender JavaScript (`<ul id="load_berita">` kosong),
  tidak ada endpoint AJAX yang terlihat dari HTML statis. RSS-nya tetap dipakai.
- **Bisnis.com** — `403 Forbidden`, baik RSS maupun indeks.
- **Tempo indeks** — dirender JavaScript, dan halaman 1 & 2 isinya identik.
- **Okezone** — indeksnya hidup, tapi hanya memuat tanggal di URL tanpa jam,
  dan RSS-nya kosong. Memakainya berarti menebak jam terbit, yang persis
  merusak invarian atribusi sesi yang jadi fondasi seluruh program ini.
  (Feed sindikasinya menjawab, isinya berita 2016.)
- **Bisnis.com** 403 · **investor.id** 404 · **EmitenNews** 500 ·
  **IDNFinancials** 404 · **Kompas** (`rss.kompas.com`) 403 · **Kumparan** 404
  · **Suara** 404 · **JPNN** 404 · **IQPlus** dan **Tempo /ekonomi** menjawab
  tapi nol item. Semua sudah dicoba; jangan diulang tanpa alasan baru.

Catatan data harga: **`range=max` di Yahoo diam-diam diturunkan jadi bar
bulanan** — 437 bar sejak 1990, bukan 5.000 bar harian. Selalu pakai
`period1`/`period2`. Dan data SET (Thailand) di Yahoo sering tertinggal
beberapa minggu; itu ditangani dengan mengembalikan `null` di luar rentang,
bukan membawa maju nilai terakhir.

Yang disimpan cuma **judul, ringkasan pendek, URL, domain, dan jam terbit** —
bukan isi artikel. Untuk membaca lengkap, tautannya ke situs asal. Ini soal
hak cipta sekaligus ukuran arsip.

---

## Cara jalan

```bash
cd collector

python run.py indices        # tarik bar 7 indeks (sekali di awal)
python run.py rss            # tarik berita terbaru dari 5 RSS
python run.py backfill 30    # indeks Detik+CNBC 30 hari ke belakang
python run.py proses         # kategori + klaster + skor ulang
python run.py export         # tulis JSON ke ../site/data

python run.py update         # impor + indices + rss + proses + export
```

Uji:

```bash
python tests.py        # logika collector: waktu, kategori, emiten, skor
cd ../site && node uji.mjs   # halaman dijalankan di atas DOM tiruan
```

`uji.mjs` ada karena satu kelas bug tidak akan pernah tertangkap `tests.py`
dan tidak kelihatan saat membaca kode: fungsi yang dipanggil tapi tidak pernah
didefinisikan. `gambarSintesis(h)` pernah hidup sebagai panggilan tanpa badan
— akibatnya `isiPanel()` melempar ReferenceError di baris itu dan **semua**
yang harusnya digambar sesudahnya (kesimpulan, filter, seluruh daftar berita)
tidak pernah muncul. Dari luar halamannya cuma terlihat "kosong kalau
tanggalnya diklik".

Lihat situsnya:

```bash
cd site && python -m http.server 8000     # buka http://localhost:8000
```

`file://` tidak bisa dipakai — `fetch()` ke berkas JSON akan diblokir CORS.

### Backfill panjang

Backfill bisa dijeda dan dilanjut. Sebelum menarik sebuah tanggal, runner
mengecek berapa artikel Detik yang sudah dimiliki untuk tanggal terbit itu;
kalau sudah ≥15, tanggalnya dilewati tanpa request. Jadi menjalankan
`backfill 730` dua kali tidak menarik ulang apa pun.

Dengan jeda 2 detik per request, satu hari kalender makan ~14 detik.
Sejak 1 Januari 2026 ≈ 1 jam; dua tahun penuh ≈ 5–6 jam. Jalankan bertahap lewat tab **Actions → perbarui data →
Run workflow**, isi `backfill_hari` misalnya `120`, dan ulangi. Tidak ada yang
perlu dijalankan dari komputer sendiri.

---

## Bentuk data

Arsip yang sesungguhnya adalah JSON di dalam repo, **bukan** `pasar.db`.
Database cuma berkas kerja: Actions membangunnya ulang dari JSON tiap kali
jalan, menambah yang baru, lalu mengekspor JSON lagi. Karena itu ID artikel
diturunkan dari URL, bukan nomor urut — kalau tidak, seluruh berkas bulan akan
terlihat berubah oleh git padahal isinya sama.

```
site/data/
  meta.json             status update + ringkasan indeks + daftar situs
  emiten.json           kode saham -> [nama, sektor], kurasi + hasil belajar
  pasar.json            semua bar 7 indeks + 2 acuan divergensi (sekali muat)
  hari.json             ringkasan per hari + 3 klaster teratas (scrub & ribbon)
  tema.json             statistik event-study per tema
  berita/YYYY-MM.json   detail lengkap per bulan, dimuat saat dibutuhkan
```

Pemisahan ini yang bikin scrub tetap mulus: menggeser kursor cuma membaca
`hari.json` yang sudah ada di memori, tidak pernah menembak jaringan.

---

## Menyetel

`collector/config.py` memuat daftar indeks (beserta warna dan lag-nya), daftar
sumber berita, kata kunci kategori, bobot skor, dan ambang penanda hari
penting. Situs membaca daftar indeks dari data, jadi menambah bursa cukup satu
baris di `INDICES` — tidak ada yang perlu diubah di `app.js`. Semua artikel disimpan mentah tanpa disaring,
jadi aturan di situ boleh diubah kapan saja — cukup jalankan `run.py proses`
lagi, tidak perlu scraping ulang. Ini disengaja: salah kata kunci tidak boleh
membuang hasil backfill berjam-jam.

## Menerbitkan

1. Push repo ini ke GitHub.
2. **Settings → Pages → Source: GitHub Actions**.
3. Workflow `perbarui data` jalan sesuai jadwal dan menerbitkan ulang situsnya.

Untuk repo privat, Actions punya kuota menit gratis; jadwal bawaan (~24 run
per hari) dipilih supaya muat di dalamnya. Repo publik tidak dibatasi.
