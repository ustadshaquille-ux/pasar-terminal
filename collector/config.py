"""Konfigurasi terpusat: indeks, sumber berita, kategori, aturan waktu."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "collector" / "pasar.db"
DATA_DIR = ROOT / "site" / "data"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# --- Indeks -----------------------------------------------------------------
# lag: berapa hari bursa ini harus digeser mundur supaya sejajar DAMPAK ke IDX.
#   0 = tutup sebelum/berbarengan IDX (Nikkei 13:00 WIB, HSI 15:00, STI 16:00)
#   1 = tutup setelah IDX (Wall Street 04:00 WIB besok paginya)
# Menyamaratakan lag=1 untuk semua bursa asing itu keliru: Asia sudah selesai
# sebelum IDX tutup, jadi menggesernya justru membuang informasi sehari.
#
# Pilihan indeks berdasarkan korelasi return harian vs IHSG, Agu 2023-Agu 2026:
#   SET 0.349 · KOSPI 0.327 · STI 0.312 · NIKKEI 0.302 · KLCI 0.299
#   SPX 0.237 · SENSEX 0.231 · NASDAQ 0.228 · HSI 0.181 · SHANGHAI 0.118
# Hang Seng & Shanghai sengaja tidak dipakai -- korelasinya paling lemah,
# meski intuisi bilang China penting. Tinggal tambah baris di sini kalau mau.
#
# Tidak ada field "warna" lagi. Chart membedakan indeks lewat tebal garis dan
# pola putus-putus, dan polanya dibagikan otomatis urut daftar ini (lihat
# DEK_GARIS di site/app.js). Jadi menambah bursa memang cukup satu baris:
# tidak ada palet yang perlu ikut diputuskan.
# kota: dipakai PETA DAMPAK buat menaruh simpul bursa di peta dunia.
INDICES = [
    {"kode": "IHSG",   "yahoo": "^JKSE",     "nama": "IHSG",      "negara": "Indonesia",
     "tz": "Asia/Jakarta",     "lag": 0, "utama": True,  "awal": True,
     "kota": "Jakarta",  "lon": 106.85, "lat": -6.21},
    {"kode": "SPX",    "yahoo": "^GSPC",     "nama": "S&P 500",   "negara": "AS",
     "tz": "America/New_York", "lag": 1, "utama": False, "awal": True,
     "kota": "New York", "lon": -74.01, "lat": 40.71},
    {"kode": "NIKKEI", "yahoo": "^N225",     "nama": "Nikkei 225", "negara": "Jepang",
     "tz": "Asia/Tokyo",       "lag": 0, "utama": False, "awal": True,
     "kota": "Tokyo",    "lon": 139.69, "lat": 35.69},
    {"kode": "NASDAQ", "yahoo": "^IXIC",     "nama": "Nasdaq",    "negara": "AS",
     "tz": "America/New_York", "lag": 1, "utama": False, "awal": False,
     "kota": "New York", "lon": -74.01, "lat": 40.71},
    {"kode": "SET",    "yahoo": "^SET.BK",   "nama": "SET",       "negara": "Thailand",
     "tz": "Asia/Bangkok",     "lag": 0, "utama": False, "awal": False,
     "kota": "Bangkok",  "lon": 100.50, "lat": 13.76},
    {"kode": "KOSPI",  "yahoo": "^KS11",     "nama": "KOSPI",     "negara": "Korea",
     "tz": "Asia/Seoul",       "lag": 0, "utama": False, "awal": False,
     "kota": "Seoul",    "lon": 126.98, "lat": 37.57},
    {"kode": "STI",    "yahoo": "^STI",      "nama": "STI",       "negara": "Singapura",
     "tz": "Asia/Singapore",   "lag": 0, "utama": False, "awal": False,
     "kota": "Singapura", "lon": 103.82, "lat": 1.35},
]

# Indeks yang dipakai sebagai pembanding di panel divergensi.
REF_GLOBAL = "SPX"
REF_ASIA = ["NIKKEI", "SET", "KOSPI", "STI"]

# Batas sesi IDX. Artikel terbit setelah ini -> nempel ke sesi bursa berikutnya.
JAM_TUTUP_IDX = (16, 15)

# --- Sumber berita ----------------------------------------------------------
# tier: 1 = rujukan utama, 2 = pendukung. Dipakai sebagai bobot skor.
SUMBER = {
    "finance.detik.com":       {"nama": "Detik Finance",     "tier": 1},
    "www.cnbcindonesia.com":   {"nama": "CNBC Indonesia",    "tier": 1},
    "investasi.kontan.co.id":  {"nama": "Kontan Investasi",  "tier": 1},
    "keuangan.kontan.co.id":   {"nama": "Kontan Keuangan",   "tier": 1},
    "industri.kontan.co.id":   {"nama": "Kontan Industri",   "tier": 1},
    "www.kontan.co.id":        {"nama": "Kontan",            "tier": 1},
    "www.liputan6.com":        {"nama": "Liputan6",          "tier": 1},
    "www.bloombergtechnoz.com":{"nama": "Bloomberg Technoz", "tier": 1},
    "katadata.co.id":          {"nama": "Katadata",          "tier": 1},
    "www.idxchannel.com":      {"nama": "IDX Channel",       "tier": 1},
    "pasardana.id":            {"nama": "Pasardana",         "tier": 1},
    "www.antaranews.com":      {"nama": "Antara",            "tier": 2},
    "rss.tempo.co":            {"nama": "Tempo",             "tier": 2},
    "bisnis.tempo.co":         {"nama": "Tempo",             "tier": 2},
    "www.tempo.co":            {"nama": "Tempo",             "tier": 2},
    "www.cnnindonesia.com":    {"nama": "CNN Indonesia",     "tier": 2},
    "ekbis.sindonews.com":     {"nama": "SindoNews Ekbis",   "tier": 2},
    "ekonomi.republika.co.id": {"nama": "Republika Ekonomi", "tier": 2},
    "www.republika.co.id":     {"nama": "Republika",         "tier": 2},
}

# Satu situs boleh punya beberapa feed; domainnya diambil dari URL artikel,
# bukan dari baris ini, supaya rubrik "bursa & valas" Detik tetap tercatat
# sebagai finance.detik.com dan tidak jadi sumber kembar.
#
# Yang sudah dicoba dan mati (jangan dicoba lagi tanpa alasan baru):
#   bisnis.com 403 · investor.id 404 · emitennews 500 · idnfinancials 404
#   kompas (rss.kompas.com) 403 · kumparan 404 · suara 404 · jpnn 404
#   okezone feed kosong/basi 2016 · iqplus & tempo/ekonomi 0 item
RSS_FEEDS = [
    # inti pasar
    ("https://investasi.kontan.co.id/rss",                 "investasi.kontan.co.id"),
    ("https://keuangan.kontan.co.id/rss",                  "keuangan.kontan.co.id"),
    ("https://industri.kontan.co.id/rss",                  "industri.kontan.co.id"),
    ("https://www.cnbcindonesia.com/market/rss",           "www.cnbcindonesia.com"),
    ("https://www.bloombergtechnoz.com/rss",               "www.bloombergtechnoz.com"),
    ("https://www.idxchannel.com/rss",                     "www.idxchannel.com"),
    ("https://pasardana.id/rss",                           "pasardana.id"),
    ("https://finance.detik.com/bursa-dan-valas/rss",      "finance.detik.com"),
    ("https://feed.liputan6.com/rss/bisnis/saham",         "www.liputan6.com"),
    # ekonomi umum
    ("https://finance.detik.com/rss",                      "finance.detik.com"),
    ("https://feed.liputan6.com/rss/bisnis",               "www.liputan6.com"),
    ("https://katadata.co.id/rss",                         "katadata.co.id"),
    ("https://www.cnnindonesia.com/ekonomi/rss",           "www.cnnindonesia.com"),
    ("https://ekbis.sindonews.com/rss",                    "ekbis.sindonews.com"),
    ("https://www.republika.co.id/rss/ekonomi",            "www.republika.co.id"),
    ("https://www.antaranews.com/rss/ekonomi.xml",         "www.antaranews.com"),
    ("https://rss.tempo.co/bisnis",                        "rss.tempo.co"),
]

# --- Kategori ---------------------------------------------------------------
# Urutan penting: yang di atas menang kalau cocok lebih dari satu.
# Disimpan sebagai aturan tampilan, BUKAN filter scraping -- artikel tetap
# disimpan semua supaya aturan bisa diubah tanpa scrape ulang.
KATEGORI = [
    # Berita bursa itu sendiri. Sebelum kategori ini ada, "IHSG Ditutup
    # Menguat ke 6.501" jatuh ke LAINNYA dan tampil abu-abu di antara berita
    # gaya hidup -- padahal itu justru inti halamannya. Di arsip ini kata
    # "IHSG" saja muncul di 237 judul.
    ("BURSA", [
        "ihsg", "indeks harga saham gabungan", "bursa saham", "bursa efek indonesia",
        "lq45", "idx composite", "papan utama", "top gainer", "top loser",
        "rekomendasi saham", "saham pilihan", "prediksi ihsg", "proyeksi ihsg",
        "net foreign", "asing borong", "asing jual", "asing lepas", "beli asing",
        "investor asing", "capital inflow", "capital outflow", "aliran modal asing",
        "bursa asia", "bursa eropa", "saham hari ini", "market recap",
    ]),
    ("MAKRO_DOMESTIK", [
        "bank indonesia", "bi rate", "suku bunga acuan", "bi-rate", "rdg bi",
        "inflasi", "deflasi", "pdb", "pertumbuhan ekonomi", "neraca dagang",
        "neraca perdagangan", "cadangan devisa", "rupiah", "kurs", "apbn",
        "defisit", "utang pemerintah", "sri mulyani", "purbaya", "perry warjiyo",
        "bps", "ekspor impor", "daya beli", "phk massal",
    ]),
    ("MAKRO_GLOBAL", [
        "the fed", "federal reserve", "fomc", "powell", "suku bunga as",
        "tarif trump", "perang dagang", "tarif impor as", "yield treasury",
        "dolar as", "dxy", "ekonomi china", "pboc", "resesi global",
        "wall street", "bank sentral eropa", "ecb", "boj", "geopolitik",
    ]),
    ("KEBIJAKAN", [
        "ojk", "bursa efek", "idx", "bei ", "auto reject", "suspensi saham",
        "papan pemantauan", "full call auction", "short selling", "danantara",
        "dhe", "devisa hasil ekspor", "penerimaan pajak", "tarif pajak", "ppn",
        "pph", "insentif fiskal", "pojk", "self regulatory", "ipo", "delisting",
    ]),
    ("KOMODITAS", [
        "harga emas", "minyak mentah", "brent", "wti", "batu bara", "batubara",
        "cpo", "sawit", "nikel", "tembaga", "timah", "gas alam", "opec",
    ]),
    ("EMITEN", [
        "dividen", "rups", "laba bersih", "kinerja emiten", "right issue",
        "buyback", "akuisisi", "merger", "obligasi korporasi", "emiten",
        "stock split", "private placement", "tender offer", "rights issue",
        "kuartal i", "kuartal ii", "kuartal iii", "semester i", "semester ii",
        "pendapatan naik", "rugi bersih", "aksi korporasi",
    ]),
    ("POLITIK", [
        "prabowo", "reshuffle kabinet", "menteri keuangan", "menteri bumn",
        "demo besar", "unjuk rasa", "kerusuhan", "pemilu", "korupsi", "kpk",
    ]),
]

# Kata yang nandain artikel ini market-wide (bukan berita korporat receh).
# Dipakai buat ngangkat skor, bukan buat mbuang.
BOBOT_PASAR = [
    "ihsg", "bursa", "indeks harga saham", "pasar modal", "investor asing",
    "net foreign", "asing jual", "asing beli", "rupiah", "obligasi negara",
    "sbn", "wall street", "bank indonesia", "the fed",
]

# Judul yang jelas bukan berita pasar -> skor ditekan, tetap disimpan.
NOISE = [
    "resep", "wisata", "zodiak", "ramalan", "artis", "sinopsis", "jadwal sholat",
    "lowongan kerja", "harga hp", "spesifikasi", "prediksi skor", "liga",
    "foto:", "video:", "infografis",
    # Berita rekrutmen dan feature ringan yang kebetulan menyebut lembaga
    # keuangan di judulnya -- "PCPM Bank Indonesia Dibuka Hari Ini, Cek
    # Syaratnya" bukan berita pasar, tapi lolos gerbang lewat "bank indonesia".
    "cek syaratnya", "cara daftar", "pendaftaran dibuka", "rekrutmen", "pcpm",
    "disulap", "tak layak edar", "begini caranya",
    # Rilis humas emiten. Ini yang paling banyak mengotori panel MIKRO: satu
    # bank besar bisa mengeluarkan lima rilis penghargaan dalam sehari, dan
    # kalau skornya sejajar, "BRI Sabet 6 Penghargaan" duduk di atas "Laba BRI
    # Turun 8%". Tidak dibuang -- cuma ditahan supaya turun ke bawah blok.
    "penghargaan", "sabet", "award", "juara", "csr", "bakti sosial", "santunan",
    "champions league", "academy", "turnamen", "hut ke-", "ulang tahun",
    "undian", "giveaway", "promo spesial", "gelar acara", "meriahkan",
]

# --- Dua sumbu: SKALA dan kategori -----------------------------------------
# Kategori menjawab "soal apa", skala menjawab "seluas apa". Dua-duanya perlu:
# "Laba BBRI Naik 12%" dan "BI Tahan Suku Bunga" sama-sama berita pasar, tapi
# yang satu menggerakkan satu saham dan yang satu menggerakkan seluruh papan.
# Dicampur dalam satu daftar, keduanya sama-sama tenggelam.
#
#   MAKRO - seluruh pasar: IHSG, rupiah, BI, Fed, komoditas, kebijakan
#   MIKRO - satu emiten (ada kode saham / nama perusahaan tercatat di judul)
#   UMUM  - ekonomi umum & sisanya; tidak dibuang, cuma tidak ikut menonjol
SKALA_KATEGORI = {
    "BURSA": "MAKRO", "MAKRO_DOMESTIK": "MAKRO", "MAKRO_GLOBAL": "MAKRO",
    "KEBIJAKAN": "MAKRO", "KOMODITAS": "MAKRO", "POLITIK": "MAKRO",
    "EMITEN": "MIKRO", "LAINNYA": "UMUM",
}

# --- Sumbu ketiga: WILAYAH --------------------------------------------------
# "Dari mana anginnya datang." Dipakai PETA DAMPAK: tiap sesi, wilayah yang
# lagi ramai dibicarakan menyala di peta dunia.
#
# Satu artikel boleh kena beberapa wilayah -- "Tarif Trump ke China Bikin IHSG
# Anjlok" itu memang soal AS, China, dan Indonesia sekaligus, dan memaksanya
# memilih satu malah membuang informasi.
#
# ID sengaja ditaruh terakhir dan tetap ikut ditandai. Hampir semua artikel di
# arsip ini menyebut Indonesia, jadi angkanya mentah tidak berguna. Yang
# dipakai peta bukan jumlah, melainkan RASIO terhadap kelaziman wilayah itu
# sendiri (lihat app.js): "hari ini AS dibicarakan 4x lebih sering daripada
# biasanya" itu temuan; "hari ini ada 300 berita Indonesia" bukan.
#
# Kunci harus spesifik. "as" atau "eu" sebagai kata lepas kepancing di mana-
# mana, jadi dipakai frasa. Pencocokan berjalan di judul saja, sama seperti
# kategori, dengan alasan yang sama.
WILAYAH = [
    ("US",    ["the fed", "fomc", "powell", "federal reserve", "wall street",
               "dow jones", "s&p 500", "nasdaq", "dolar as", "yield treasury",
               "tarif trump", "trump", "amerika serikat", "ekonomi as",
               "suku bunga as", "resesi as", "gedung putih", "washington",
               "tarif impor as", "tarif resiprokal"]),
    ("CN",    ["china", "tiongkok", "pboc", "yuan", "hang seng", "shanghai",
               "beijing", "hong kong", "hongkong", "ekonomi china"]),
    ("JP_KR", ["jepang", "boj", "bank of japan", "yen", "nikkei", "tokyo",
               "korea selatan", "korsel", "kospi", "samsung"]),
    ("EU",    ["eropa", "ecb", "bank sentral eropa", "zona euro", "jerman",
               "inggris", "prancis", "perancis", "italia", "belanda",
               "bank of england", "bursa eropa"]),
    ("ME",    ["opec", "arab saudi", "timur tengah", "iran", "israel", "qatar",
               "uni emirat", "uea", "gaza", "houthi", "laut merah"]),
    ("IN",    ["india", "sensex", "rupee", "reserve bank of india"]),
    ("ASEAN", ["singapura", "malaysia", "thailand", "vietnam", "filipina",
               "asean", "ringgit", "baht", "brunei", "kamboja", "myanmar"]),
    ("AU",    ["australia", "selandia baru", "reserve bank of australia"]),
    ("RU",    ["rusia", "ukraina", "putin", "moskow", "gazprom"]),
    ("LATAM", ["brasil", "argentina", "meksiko", "amerika latin", "chili"]),
    ("AF",    ["afrika", "nigeria", "mesir", "afrika selatan"]),
    ("ID",    ["indonesia", "ihsg", "bank indonesia", "bi rate", "rupiah",
               "bursa efek indonesia", "ojk", "apbn", "sri mulyani", "purbaya",
               "prabowo", "jakarta", "bps", "idx", "danantara", "pertamina",
               "bumn", "kpk", "dpr", "kemenkeu"]),
]

AMBANG_MOVE = 1.5        # |%| perubahan harian yang dianggap signifikan
AMBANG_HEADLINE = 5.0    # skor minimum supaya sebuah klaster boleh jadi headline hari
AMBANG_DIVERGENSI = 1.0  # |%| selisih IHSG vs SPX yang dianggap decoupling


# --- Tema berulang ----------------------------------------------------------
# Dipakai panel kesimpulan: apa yang dibicarakan hari ini, apa yang baru, dan
# bagaimana IHSG bergerak pada sesi-sesi lain ketika tema itu muncul.
# Kunci harus spesifik: tema yang kepancing kata umum bikin event-study-nya
# tidak berarti apa-apa karena hampir semua hari ikut terhitung.
TEMA = [
    ("Suku bunga BI",   ["bi rate", "bi-rate", "suku bunga acuan", "rdg bi",
                         "bank indonesia tahan", "bi turunkan", "bi pangkas"]),
    ("The Fed",         ["the fed", "fomc", "powell", "federal reserve",
                         "suku bunga as"]),
    ("Rupiah",          ["rupiah", "nilai tukar", "kurs dolar"]),
    ("Inflasi",         ["inflasi", "deflasi", "indeks harga konsumen"]),
    ("Tarif dagang AS", ["tarif trump", "perang dagang", "tarif impor",
                         "tarif resiprokal"]),
    ("Asing di bursa",  ["investor asing", "net foreign", "asing jual",
                         "asing beli", "net sell", "net buy", "dana asing",
                         "aliran modal asing", "capital outflow", "capital inflow"]),
    ("Harga emas",      ["harga emas", "emas antam"]),
    ("Minyak",          ["minyak mentah", "harga minyak", "brent", "wti", "opec"]),
    ("Batu bara",       ["batu bara", "batubara"]),
    ("Nikel",           ["harga nikel", "nikel anjlok", "nikel naik", "hilirisasi nikel"]),
    ("Sawit/CPO",       ["cpo", "kelapa sawit", "harga sawit"]),
    ("Regulasi bursa",  ["papan pemantauan", "auto reject", "suspensi saham",
                         "full call auction", "short selling", "pojk"]),
    ("Danantara",       ["danantara"]),
    ("IPO & delisting", ["ipo", "pencatatan perdana", "delisting"]),
    ("APBN & fiskal",   ["apbn", "defisit anggaran", "penerimaan pajak",
                         "utang pemerintah", "sri mulyani", "purbaya"]),
    ("Pertumbuhan PDB", ["pdb", "pertumbuhan ekonomi", "resesi"]),
    ("Neraca dagang",   ["neraca dagang", "neraca perdagangan", "surplus dagang"]),
    ("Wall Street",     ["wall street", "dow jones", "s&p 500", "indeks nasdaq"]),
]
