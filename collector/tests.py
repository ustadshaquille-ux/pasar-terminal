"""Uji invarian yang gampang rusak diam-diam.

  python tests.py

Yang diuji cuma logika murni (tanpa jaringan, tanpa database), karena justru
di situ kesalahannya tidak kelihatan: berita nempel di hari yang salah, atau
berita sampah naik jadi headline. Dua-duanya bikin situs terlihat baik-baik
saja padahal isinya keliru.
"""
import json
import sys
from datetime import datetime

from config import AMBANG_HEADLINE, DATA_DIR, INDICES, WILAYAH
import emiten as em
from skor import _token, hitung_skor, kategorikan, skalakan, wilayahkan
from waktu import Kalender, parse_cnbc_url, parse_detik, parse_rfc822

gagal = []
NL = chr(10)


def cek(nama, dapat, harap):
    if dapat == harap:
        print("  ok    %s" % nama)
    else:
        print("  GAGAL %s\n          dapat  : %r\n          harusnya: %r" % (nama, dapat, harap))
        gagal.append(nama)


def benar(nama, syarat):
    cek(nama, bool(syarat), True)


# --- waktu ------------------------------------------------------------------
print("\n[waktu] penguraian tanggal")
cek("detik", parse_detik("Senin, 15 Jan 2024 23:03 WIB"), datetime(2024, 1, 15, 23, 3))
cek("cnbc dari url",
    parse_cnbc_url("https://www.cnbcindonesia.com/news/20240115190155-4-506085/x"),
    datetime(2024, 1, 15, 19, 1, 55))
cek("rss +0700", parse_rfc822("Sun, 23 Aug 2026 20:56:48 +0700"), datetime(2026, 8, 23, 20, 56, 48))
cek("rss UTC dinormalkan ke WIB",
    parse_rfc822("Sun, 23 Aug 2026 13:56:48 +0000"), datetime(2026, 8, 23, 20, 56, 48))

print("\n[waktu] atribusi ke sesi bursa")
kal = Kalender(["2024-01-11", "2024-01-12", "2024-01-15", "2024-01-16"])
cek("dalam jam bursa -> hari itu", kal.sesi_untuk(datetime(2024, 1, 12, 10, 0)), ("2024-01-12", 0))
cek("tepat di batas 16:15 -> hari itu", kal.sesi_untuk(datetime(2024, 1, 12, 16, 15)), ("2024-01-12", 0))
cek("16:16 -> sesi berikutnya", kal.sesi_untuk(datetime(2024, 1, 12, 16, 16)), ("2024-01-15", 1))
cek("malam Jumat -> Senin", kal.sesi_untuk(datetime(2024, 1, 12, 19, 0)), ("2024-01-15", 1))
cek("Sabtu -> Senin", kal.sesi_untuk(datetime(2024, 1, 13, 9, 0)), ("2024-01-15", 1))
cek("Minggu -> Senin", kal.sesi_untuk(datetime(2024, 1, 14, 9, 0)), ("2024-01-15", 1))

print("\n[waktu] proyeksi melewati bar terakhir")
# Tanpa ini, berita hari ini terbuang cuma karena bar besok belum terbit.
kal2 = Kalender(["2026-08-19", "2026-08-20", "2026-08-21"])
cek("Jumat malam -> Senin (diproyeksikan)", kal2.sesi_untuk(datetime(2026, 8, 21, 19, 0)),
    ("2026-08-24", 1))
cek("Minggu -> Senin (diproyeksikan)", kal2.sesi_untuk(datetime(2026, 8, 23, 9, 0)),
    ("2026-08-24", 1))
# Bar hari ini baru terbit sore; berita paginya tidak boleh lari ke besok.
cek("Senin pagi -> sesi Senin walau barnya belum terbit",
    kal2.sesi_untuk(datetime(2026, 8, 24, 5, 45)), ("2026-08-24", 0))
cek("Senin siang -> sesi Senin", kal2.sesi_untuk(datetime(2026, 8, 24, 11, 0)),
    ("2026-08-24", 0))
cek("Senin malam -> sesi Selasa", kal2.sesi_untuk(datetime(2026, 8, 24, 20, 0)),
    ("2026-08-25", 1))

# --- kategori ---------------------------------------------------------------
print("\n[kategori]")
cek("BI rate", kategorikan("BI Tahan Suku Bunga Acuan di Level 5,75%"), "MAKRO_DOMESTIK")
cek("Fed", kategorikan("The Fed Isyaratkan Pemangkasan Suku Bunga"), "MAKRO_GLOBAL")
cek("OJK", kategorikan("OJK Cabut Izin Usaha BPR di Bekasi"), "KEBIJAKAN")
cek("emas", kategorikan("Harga Emas Menguat Tembus Rekor"), "KOMODITAS")
cek("bukan berita pasar", kategorikan("Resep Rendang Padang Anti Gagal"), "LAINNYA")
cek("pajak kendaraan bukan kebijakan pasar",
    kategorikan("Pasukan Emak Dikerahkan Tagih Pajak Kendaraan Bermotor"), "LAINNYA")

cek("berita bursa punya kategori sendiri",
    kategorikan("IHSG Ditutup Menguat ke 6.501"), "BURSA")
cek("aliran asing masuk BURSA",
    kategorikan("Asing Borong Saham BRI-BCA, IHSG Menguat"), "BURSA")

# --- wilayah (PETA DAMPAK) --------------------------------------------------
print(NL + "[wilayah] dari mana anginnya datang")
cek("satu judul boleh banyak wilayah",
    wilayahkan("Tarif Trump ke China Bikin IHSG Anjlok"), ["US", "CN", "ID"])
cek("Fed = Amerika", wilayahkan("The Fed Tahan Suku Bunga"), ["US"])
cek("berita lokal murni", wilayahkan("BI Tahan BI Rate di 5,75%"), ["ID"])
cek("bukan berita wilayah", wilayahkan("Resep Rendang Padang Anti Gagal"), [])

# Ini pengujian yang paling penting di blok ini. Nama wilayah itu pendek dan
# bersarang di kata Indonesia biasa; sekali dijalankan tanpa batas kata,
# "iran" kepancing di gILIRANg dan penCAIRANnya, dan Timur Tengah melonjak
# jadi wilayah nomor dua tersibuk di seluruh arsip -- 919 artikel, sebagian
# besar soal pencairan dividen.
print(NL + "[wilayah] nama pendek tidak boleh kepancing di tengah kata")
for jebakan in ["BBCA Tebar Dividen, Cek Jadwal Pencairannya",
                "Giliran Emiten Haji Isam Buka Suara",
                "Aliran Dana Masuk ke Reksa Dana Pasar Uang",
                "Sekitaran Sudirman Macet Total"]:
    benar('"%s" -> tanpa ME' % jebakan[:34], "ME" not in wilayahkan(jebakan))
benar("Iran sungguhan tetap tertangkap",
      "ME" in wilayahkan("Sanksi Baru AS ke Iran, Harga Minyak Meroket"))

# --- kisi peta --------------------------------------------------------------
print(NL + "[peta] kisi titik dunia")
_peta = json.loads((DATA_DIR / "peta.json").read_text(encoding="utf-8"))
benar("kisi ada dan penuh", len(_peta["sel"]) == _peta["baris"]
      and all(len(b) == _peta["kolom"] for b in _peta["sel"]))
benar("cukup banyak sel darat",
      sum(1 for b in _peta["sel"] for c in b if c != ".") > 2000)
benar("tiap huruf sel dikenali",
      {c for b in _peta["sel"] for c in b} <= set(_peta["huruf"]) | {".", "X"})
benar("tiap wilayah di config.WILAYAH punya tempat di peta",
      {w for w, _ in WILAYAH} <= set(_peta["huruf"].values()))
benar("tiap indeks punya koordinat",
      all("lon" in i and "lat" in i for i in INDICES))
benar("simpul bursa memuat semua indeks",
      {k for b in _peta["bursa"] for k in b["kode"]} == {i["kode"] for i in INDICES})

# --- emiten & skala ---------------------------------------------------------
print(NL + "[emiten] deteksi kode saham dari judul")
cek("kode dalam kurung", em.deteksi("Laba Emiten Bioskop XXI (CNMA) Anjlok 40%"), ["CNMA"])
cek("kode berdiri sendiri yang dikenal",
    em.deteksi("CBDK Mau Buyback Saham, Siapkan Dana Rp 250 Miliar"), ["CBDK"])
cek("nama perusahaan tanpa kode",
    em.deteksi("Laba Bersih Bank Mandiri Tumbuh 8%"), ["BMRI"])
cek("beberapa emiten dalam satu judul",
    em.deteksi("Rekomendasi Saham Hari Ini: AMMN, BUMI, hingga UNVR"),
    ["AMMN", "BUMI", "UNVR"])
benar("akronim empat huruf bukan emiten",
      em.deteksi("IHSG Menguat, BUMN Karya Diselamatkan APBN") == [])
benar("kata biasa 'mandiri' bukan Bank Mandiri",
      em.deteksi("Kopdes Merah Putih Didorong Mandiri Secara Keuangan") == [])
benar("'BRIN' bukan BRI",
      em.deteksi("BRIN Kembangkan Riset Baterai Nasional") == [])
cek("harga emas Antam itu komoditas, bukan saham ANTM",
    em.deteksi("Harga Emas Antam Hari Ini Naik Rp 20.000"), [])
cek("tapi kalau kodenya tertulis, tetap saham ANTM",
    em.deteksi("Saham ANTM Melesat Ikut Harga Emas"), ["ANTM"])
cek("nama dipetik dari pola 'Nama (KODE)'",
    em.belajar("Adhi Karya (ADHI) Menang Tender"), [("ADHI", "Adhi Karya")])

print(NL + "[skala] makro vs mikro")
cek("berita emiten -> MIKRO",
    skalakan("Laba Bersih Bank Mandiri Tumbuh 8%", "EMITEN", ["BMRI"]), "MIKRO")
cek("berita bursa -> MAKRO", skalakan("IHSG Ditutup Menguat", "BURSA", []), "MAKRO")
cek("emiten yang cuma contoh di berita makro tetap MAKRO",
    skalakan("Bank Mandiri Buyback Saham Saat IHSG Lesu", "BURSA", ["BMRI"]), "MAKRO")
cek("berita ekonomi umum -> UMUM",
    skalakan("Tarif Angkutan Kapal Pelni Naik", "LAINNYA", []), "UMUM")

# --- klaster ----------------------------------------------------------------
print("\n[klaster] ambang overlap")


def overlap(a, b):
    x, y = _token(a), _token(b)
    if not x or not y:
        return 0, 0
    return len(x & y) / min(len(x), len(y)), len(x & y)


def segrup(a, b):
    ov, ir = overlap(a, b)
    return ov >= 0.65 and ir >= 3


benar("berita sama dari dua situs digabung",
      segrup("BI Tahan Suku Bunga Acuan di Level 5,75%",
             "Bank Indonesia Tahan Suku Bunga Acuan 5,75 Persen"))
benar("komoditas berbeda tidak digabung",
      not segrup("Harga Emas Naik Tajam", "Harga Minyak Turun Tajam"))
benar("berita tak berhubungan tidak digabung",
      not segrup("OJK Cabut Izin BPR di Bekasi", "Prabowo Resmikan Jalan Tol Baru"))

# --- skor -------------------------------------------------------------------
print("\n[skor] gerbang relevansi pasar")


def skor(judul, dom="finance.detik.com", n=1, move=1.6):
    a = {"judul": judul, "ringkasan": None, "domain": dom}
    a["kategori"] = kategorikan(judul)
    a["emiten"] = em.deteksi(judul)
    return hitung_skor(a, n, move)


benar("berita makro jadi headline", skor("Rupiah Ditutup Melesat 0,48%") >= AMBANG_HEADLINE)
benar("IHSG jadi headline walau kategorinya lain",
      skor("IHSG Ditutup Menguat 1,6% Ditopang Beli Asing") >= AMBANG_HEADLINE)
benar("komoditas jadi headline", skor("Nikel Anjlok Imbas Permintaan China") >= AMBANG_HEADLINE)
benar("berita non-pasar ditahan di bawah ambang",
      skor("Pasukan Emak Dikerahkan Tagih Pajak Kendaraan Bermotor") < AMBANG_HEADLINE)
benar("tender korporat ditahan",
      skor("PT Pertamina Patra Niaga RU Cilacap Buka Tender Proyek") < AMBANG_HEADLINE)
benar("berita gaya hidup ditahan", skor("Resep Rendang Padang Anti Gagal") < AMBANG_HEADLINE)

print("\n[skor] hari bergejolak tidak boleh mengangkat sampah melewati ambang")
benar("sampah tetap di bawah ambang walau IHSG -5%",
      skor("Resep Rendang Padang Anti Gagal", move=-5.0) < AMBANG_HEADLINE)
benar("klaster besar tidak menerobos gerbang",
      skor("Prabowo Resmikan Jalan Tol Baru", n=6) < AMBANG_HEADLINE)

print("\n[skor] urutan masuk akal")
benar("makro > kebijakan",
      skor("BI Tahan Suku Bunga Acuan") > skor("OJK Cabut Izin Usaha BPR di Bekasi"))
benar("banyak sumber menaikkan skor",
      skor("Rupiah Ditutup Melesat", n=5) > skor("Rupiah Ditutup Melesat", n=1))

# --- lag per bursa ----------------------------------------------------------
print("\n[lag] hanya bursa yang tutup setelah IDX yang digeser")
from config import INDICES, REF_ASIA, REF_GLOBAL
from export import _median, _ret_tergeser

lag = {i["kode"]: i["lag"] for i in INDICES}
cek("Wall Street digeser sehari", (lag["SPX"], lag["NASDAQ"]), (1, 1))
benar("semua bursa Asia tidak digeser",
      all(lag[k] == 0 for k in ("IHSG", "NIKKEI", "KOSPI", "STI", "SET")))
benar("acuan Asia tidak memuat bursa AS",
      not any(lag.get(k) for k in REF_ASIA))
cek("acuan global adalah bursa AS", lag[REF_GLOBAL], 1)

bars = {"X": [("2026-01-05", 10, 1.0, 0), ("2026-01-06", 11, 2.0, 0),
              ("2026-01-07", 12, 3.0, 0)]}
cek("lag 0 memakai return hari yang sama",
    _ret_tergeser(bars, "X", 0), {"2026-01-05": 1.0, "2026-01-06": 2.0, "2026-01-07": 3.0})
cek("lag 1 memindahkan return ke sesi berikutnya",
    _ret_tergeser(bars, "X", 1), {"2026-01-06": 1.0, "2026-01-07": 2.0})

print("\n[median] acuan Asia tahan terhadap bursa yang datanya bolong")
cek("median ganjil", _median([3, 1, 2]), 2)
cek("median genap", _median([1, 2, 3, 4]), 2.5)
cek("median kosong", _median([]), None)

# --- sintesis ---------------------------------------------------------------
print("\n[sintesis] nada dibaca sebagai kata utuh")
from sintesis import nada, tema_dari

cek("menguat -> naik", nada("IHSG Ditutup Menguat 1,6%"), 1)
cek("anjlok -> turun", nada("Rupiah Anjlok ke Rp17.900"), -1)
cek("'acuan' bukan 'cuan'", nada("BI Tahan Suku Bunga Acuan di Level 5,75%"), 0)
cek("'keturunan' bukan 'turun'", nada("Daftar Keturunan Konglomerat Masuk Bursa"), 0)
cek("dua arah sekaligus -> netral", nada("Emas Melesat, Minyak Merosot"), 0)

print("\n[sintesis] tema")
cek("satu judul bisa dua tema",
    sorted(tema_dari("Rupiah Menguat Usai BI Rate Ditahan")), ["Rupiah", "Suku bunga BI"])
cek("net sell tertangkap", tema_dari("Asing Net Sell Rp1,2 T di IHSG"), ["Asing di bursa"])
cek("berita non-pasar tanpa tema", tema_dari("Resep Rendang Padang"), [])

print("\n[sintesis] basis event-study harus se-periode")
import sintesis
_, tema = sintesis.hitung()
benar("basis dihitung dari sesi terliput, bukan seluruh sejarah",
      tema["periode"] is None or tema["n_sesi"] <= 4998)
benar("event-study ditutup selama sesi terliput masih sedikit",
      tema["cukup"] or not tema["tema"])
benar("ambang kecukupan masuk akal", tema["min_sesi"] >= 60)

print()
if gagal:
    print("%d uji GAGAL: %s" % (len(gagal), ", ".join(gagal)))
    sys.exit(1)
print("semua uji lulus")
