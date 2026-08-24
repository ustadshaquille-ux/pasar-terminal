"""Kategori, skala (makro/mikro), skor relevansi, dan klasterisasi berita.

Sengaja dipisah dari pengumpulan: semua artikel sudah tersimpan mentah, jadi
aturan di sini boleh diubah kapan saja dan tinggal dijalankan ulang tanpa
perlu scraping lagi (6 jam backfill tidak terbuang gara-gara salah keyword).

Tiga sumbu, bukan satu:
  kategori - soal apa (bursa, makro domestik, komoditas, ...)
  skala    - seluas apa (MAKRO seluruh pasar / MIKRO satu emiten / UMUM sisanya)
  wilayah  - dari mana anginnya datang (US, CN, EU, ID, ...) -> PETA DAMPAK
"""
import re
from collections import Counter, defaultdict

from config import (AMBANG_HEADLINE, AMBANG_MOVE, BOBOT_PASAR, KATEGORI,
                    NOISE, SKALA_KATEGORI, SUMBER, WILAYAH)
import emiten as em
from store import db

STOP = set("""
di ke dari yang dan atau untuk pada dengan ini itu ada akan sudah telah
bisa dapat juga saja lebih masih hingga sampai karena agar oleh dalam
adalah ialah para kata ujar sebut jadi tak tidak bukan nya se si the of
a an to in on for and or is are was were be by at as it its
""".split())

MAKRO_KUAT = re.compile(
    r"(?<![a-z])(ihsg|bi rate|suku bunga acuan|the fed|fomc|inflasi|rupiah|"
    r"neraca dagang|neraca perdagangan|apbn|pdb|bank indonesia)(?![a-z])")


def kategorikan(judul, ringkasan=None):
    # Sengaja HANYA judul. Ringkasan RSS penuh angka harga, jadi kata "rupiah"
    # muncul di berita apa saja -- itu yang bikin "Perajin Aceh Ubah Drum
    # Plastik" sempat masuk MAKRO_DOMESTIK. Judul adalah ringkasan editorial
    # yang sudah dikurasi; itu sinyal yang benar.
    t = judul.lower()
    for nama, kunci in KATEGORI:
        for k in kunci:
            if k in t:
                return nama
    return "LAINNYA"


# Wilayah dicocokkan dengan BATAS KATA, tidak seperti kategori.
#
# Kategori memakai frasa panjang ("neraca perdagangan"), jadi pencocokan
# substring aman di sana. Nama wilayah pendek dan justru bersarang di kata
# Indonesia biasa: "iran" ada di dalam g-il-IRAN, pen-c-a-IRAN-nya, al-IRAN,
# sek-IT-a-r-a-n; "eropa" aman, tapi "uea" dan "chili" tidak. Pertama kali
# dijalankan tanpa batas kata, Timur Tengah jadi wilayah nomor dua tersibuk
# di seluruh arsip — 919 artikel, sebagian besar soal pencairan dividen.
_POLA_WILAYAH = [
    (nama, re.compile("|".join(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])"
                               for k in kunci)))
    for nama, kunci in WILAYAH
]


def wilayahkan(judul):
    """Semua wilayah yang disebut judul, bukan cuma satu.

    "Tarif Trump ke China Bikin IHSG Anjlok" memang soal AS, China, dan
    Indonesia sekaligus; memaksanya memilih satu membuang justru rantai sebab
    yang mau ditunjukkan peta. Urutannya ikut config.WILAYAH supaya keluarannya
    stabil (dipakai uji).
    """
    t = judul.lower()
    return [nama for nama, pola in _POLA_WILAYAH if pola.search(t)]


def skalakan(judul, kategori, kode_emiten):
    """MAKRO / MIKRO / UMUM.

    Emiten yang tersebut di judul menang atas kategori: "Laba BBRI Naik" itu
    berita satu saham, mau kategorinya EMITEN atau LAINNYA. Kecuali judulnya
    juga membawa penggerak seluruh papan ("Bank Mandiri Buyback Saat IHSG
    Lesu") -- di situ yang menggerakkan pasar tetap yang makro, emitennya cuma
    contoh, jadi beritanya tinggal di MAKRO sambil tetap membawa tag emiten.
    """
    if kode_emiten and not MAKRO_KUAT.search(judul.lower()):
        return "MIKRO"
    return SKALA_KATEGORI.get(kategori, "UMUM")


def _token(judul):
    kata = re.findall(r"[a-z0-9]+", judul.lower())
    return {k for k in kata if k not in STOP and len(k) > 2}


def hitung_skor(art, ukuran_klaster, move_pct):
    """Skor 0..~10. Dipakai buat urutan tampil & ambang marker."""
    judul = art["judul"].lower()
    penuh = (art["judul"] + " " + (art["ringkasan"] or "")).lower()
    tier = SUMBER.get(art["domain"], {}).get("tier", 3)
    s = {1: 3.0, 2: 2.0}.get(tier, 1.0)

    s += {"BURSA": 3.0, "MAKRO_DOMESTIK": 3.0, "MAKRO_GLOBAL": 2.5,
          "KEBIJAKAN": 2.0, "KOMODITAS": 1.5, "EMITEN": 1.5,
          "POLITIK": 1.0}.get(art["kategori"], 0.0)

    if any(k in judul for k in BOBOT_PASAR):
        s += 2.0
    # Berita satu emiten dinilai dari sisi lain: yang penting bukan seberapa
    # banyak kata pasar di judulnya, tapi apakah emitennya memang disebut.
    if art.get("emiten"):
        s += 2.0
    # Noise diperlakukan sebagai gerbang, bukan potongan angka. Sebagai potongan
    # -3, "PCPM Bank Indonesia Dibuka Hari Ini, Cek Syaratnya" masih menyisakan
    # 6,07 dan tetap jadi headline -- berita rekrutmen menang atas berita pasar
    # cuma karena judulnya menyebut Bank Indonesia.
    noise = any(k in penuh for k in NOISE)   # deteksi sampah terbantu teks lebih banyak

    s += min(ukuran_klaster - 1, 5) * 0.6            # makin banyak situs ngangkat, makin penting
    s += min(abs(move_pct or 0) / AMBANG_MOVE, 2.0)  # hari bergejolak menaikkan bobot

    # Gerbang relevansi pasar. Tanpa ini, artikel yang cuma kebetulan menyerempet
    # satu kata kebijakan ikut terangkat oleh bonus hari bergejolak dan nangkring
    # jadi headline hari itu -- persis yang bikin judul macam "Pasukan Emak
    # Dikerahkan Tagih Pajak Kendaraan" muncul di hari IHSG lepas dari global.
    # Skornya tidak dinolkan (artikelnya tetap bisa dibaca di panel), cuma
    # ditahan di bawah ambang headline.
    # Yang lolos: berita bursa, makro, kebijakan, komoditas, dan berita yang
    # menyebut emiten. Yang tetap harus membuktikan diri lewat kata pasar:
    # POLITIK dan LAINNYA tanpa emiten.
    pasar_wide = (any(k in judul for k in BOBOT_PASAR)
                  or bool(art.get("emiten"))
                  or art["kategori"] in ("BURSA", "MAKRO_DOMESTIK", "MAKRO_GLOBAL",
                                         "KEBIJAKAN", "KOMODITAS"))
    if noise or not pasar_wide:
        s = min(s, AMBANG_HEADLINE - 0.1)
    return round(max(s, 0.0), 3)


def pelajari_emiten(judul_semua):
    """Bangun daftar emiten: kurasi + yang dipetik dari pola 'Nama (KODE)'.

    Hasil belajar disimpan supaya kode yang belum ada di daftar kurasi tetap
    dikenali saat berdiri sendiri di judul lain ("BEEF Rugi di Kuartal II").
    """
    calon = defaultdict(Counter)
    for j in judul_semua:
        for kode, nama in em.belajar(j):
            calon[kode][nama] += 1
    belajaran = {}
    for kode, nama_hit in calon.items():
        if kode in em.EMITEN:
            continue
        nama, n = nama_hit.most_common(1)[0]
        if n >= 1 and 3 <= len(nama) <= 48:
            belajaran[kode] = nama
    return belajaran


def proses(sesi_dari=None):
    """Kategorikan + skalakan + klasterkan + skor ulang seluruh artikel."""
    with db() as con:
        syarat = "WHERE session_date >= ?" if sesi_dari else ""
        arg = (sesi_dari,) if sesi_dari else ()
        rows = [dict(r) for r in con.execute(
            f"SELECT id,judul,ringkasan,domain,session_date FROM articles {syarat}", arg)]
        move = {r[0]: r[1] for r in con.execute(
            "SELECT tanggal, ret_pct FROM bars WHERE kode='IHSG'")}

    belajaran = pelajari_emiten([r["judul"] for r in rows])
    dikenal = set(em.EMITEN) | set(belajaran)

    for r in rows:
        r["kategori"] = kategorikan(r["judul"])
        r["wilayah"] = wilayahkan(r["judul"])
        r["emiten"] = em.deteksi(r["judul"], dikenal)
        r["skala"] = skalakan(r["judul"], r["kategori"], r["emiten"])
        r["tok"] = _token(r["judul"])

    # --- klaster: greedy Jaccard dalam satu sesi -----------------------------
    per_sesi = defaultdict(list)
    for r in rows:
        per_sesi[r["session_date"]].append(r)

    klaster = []          # (judul_wakil, sesi, kategori, [anggota])
    for sesi, grup in per_sesi.items():
        grup.sort(key=lambda x: -len(x["tok"]))
        wakil = []        # (tokens, anggota[])
        for r in grup:
            pas = None
            for w in wakil:
                if not r["tok"] or not w[0]:
                    continue
                # Overlap coefficient, bukan Jaccard: judul berita panjangnya
                # beda-beda jauh, dan Jaccard menghukum judul pendek terlalu
                # keras ("BI Tahan Suku Bunga" vs versi panjangnya cuma 0.50).
                irisan = len(r["tok"] & w[0])
                ov = irisan / min(len(r["tok"]), len(w[0]))
                if ov >= 0.65 and irisan >= 3:
                    pas = w
                    break
            if pas:
                pas[1].append(r)
            else:
                wakil.append((r["tok"], [r]))
        for tok, anggota in wakil:
            # judul wakil: dari sumber tier tertinggi, judul terpanjang
            anggota.sort(key=lambda x: (SUMBER.get(x["domain"], {}).get("tier", 3),
                                        -len(x["judul"])))
            klaster.append((anggota[0]["judul"], sesi, anggota[0]["kategori"], anggota))

    with db() as con:
        con.execute("DELETE FROM clusters")
        con.execute("DELETE FROM emiten")
        con.executemany(
            "INSERT INTO emiten(kode,nama,sektor,sumber) VALUES(?,?,?,?)",
            [(k, v[0], v[1], "kurasi") for k, v in em.EMITEN.items()]
            + [(k, v, "lainnya", "belajar") for k, v in belajaran.items()])
        for judul, sesi, kat, anggota in klaster:
            m = move.get(sesi)
            skor_anggota = [hitung_skor(a, len(anggota), m) for a in anggota]
            # skala klaster = skala anggota dengan skor tertinggi
            utama = anggota[skor_anggota.index(max(skor_anggota))]
            cur = con.execute(
                "INSERT INTO clusters(judul_wakil,session_date,kategori,skala,ukuran,skor)"
                " VALUES(?,?,?,?,?,?)",
                (judul, sesi, kat, utama["skala"], len(anggota),
                 round(max(skor_anggota), 3)))
            cid = cur.lastrowid
            for a, sk in zip(anggota, skor_anggota):
                con.execute(
                    "UPDATE articles SET kategori=?,skala=?,emiten=?,wilayah=?,"
                    "skor=?,cluster_id=? WHERE id=?",
                    (a["kategori"], a["skala"], ",".join(a["emiten"]) or None,
                     ",".join(a["wilayah"]) or None, sk, cid, a["id"]))
    return len(rows), len(klaster), len(belajaran)
