"""Kesimpulan lintas-sumber per sesi bursa.

Semuanya dihitung, tidak ada yang ditafsirkan. Situsnya statis dan tidak
memanggil model bahasa apa pun, jadi setiap angka di panel kesimpulan harus
bisa dilacak balik ke judul-judul yang menghasilkannya. Kalau sebuah pernyataan
tidak bisa dihitung, dia tidak ditampilkan.

Bacaan makro:
  nada        - berapa judul bernada naik vs turun, dari leksikon verba pasar
  dominan     - tema terbesar hari itu, diukur jumlah situs yang mengangkatnya
  baru        - tema yang muncul hari ini tapi absen di 5 sesi sebelumnya
  korroborasi - berapa persen berita hari itu diangkat lebih dari satu situs

Bacaan mikro:
  emiten      - saham mana yang paling banyak diberitakan hari itu, dengan
                nada masing-masing. Ini yang menjawab "hari ini yang ramai
                saham apa", pertanyaan yang tidak bisa dijawab panel makro.

Plus event-study kecil per tema: kalau sebuah tema sudah pernah muncul cukup
sering, berapa rata-rata gerak IHSG pada sesi-sesi itu, dibanding hari biasa.
"""
import re
from collections import defaultdict

from config import AMBANG_HEADLINE, TEMA
from store import db

# Verba pasar bahasa Indonesia. Sengaja bukan kata sifat umum: yang dipakai
# adalah kata yang di judul ekonomi hampir selalu berarti arah harga.
NADA_NAIK = [
    "menguat", "melesat", "rebound", "meroket", "melonjak", "ditopang",
    "cetak rekor", "tembus rekor", "bangkit", "menghijau", "positif",
    "surplus", "untung", "cuan", "naik", "tumbuh", "optimis", "pulih",
]
NADA_TURUN = [
    "anjlok", "terkoreksi", "tertekan", "ambles", "merosot", "longsor",
    "melemah", "jeblok", "memerah", "negatif", "defisit", "rugi", "turun",
    "tumbang", "lesu", "waspada", "khawatir", "terpuruk", "koreksi",
]

SESI_LOOKBACK_BARU = 5      # tema disebut "baru" kalau absen sebanyak ini
MIN_SAMPEL_TEMA = 5         # sebuah tema perlu sebanyak ini kemunculan
MIN_SESI_EVENT_STUDY = 120  # dan arsipnya perlu sebanyak ini sesi terliput


def _pola(kata):
    """Cocokkan sebagai kata utuh, bukan potongan.

    Tanpa ini "Suku Bunga Acuan" terbaca bernada positif karena "acuan"
    mengandung "cuan", dan "keturunan" terbaca negatif karena mengandung
    "turun". Bug seperti itu tidak kelihatan sampai angkanya sudah dipercaya.
    """
    return re.compile(r"(?<![a-z])(?:" + "|".join(re.escape(k) for k in kata)
                      + r")(?![a-z])")


_RE_NAIK = _pola(NADA_NAIK)
_RE_TURUN = _pola(NADA_TURUN)


def nada(judul):
    t = judul.lower()
    naik = bool(_RE_NAIK.search(t))
    turun = bool(_RE_TURUN.search(t))
    if naik and not turun:
        return 1
    if turun and not naik:
        return -1
    return 0            # dua-duanya atau tidak ada -> tidak dihitung sebagai arah


def tema_dari(judul):
    """Tema yang cocok dengan judul. Bisa lebih dari satu."""
    t = judul.lower()
    return [nama for nama, kunci in TEMA if any(k in t for k in kunci)]


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def hitung():
    """Balikin (ringkasan_per_sesi, statistik_per_tema)."""
    with db() as con:
        arts = [dict(r) for r in con.execute(
            "SELECT session_date, judul, domain, skor, cluster_id, skala, emiten"
            " FROM articles WHERE cluster_id IS NOT NULL")]
        ret_ihsg = {t: r for t, r in con.execute(
            "SELECT tanggal, ret_pct FROM bars WHERE kode='IHSG'")}

    per_sesi = defaultdict(list)
    for a in arts:
        per_sesi[a["session_date"]].append(a)

    # tema per sesi (hanya dari artikel yang lolos gerbang pasar -- kalau tidak,
    # berita gaya hidup ikut menyumbang "nada" dan angkanya jadi omong kosong)
    tema_sesi = {}
    for sesi, grup in per_sesi.items():
        tema_sesi[sesi] = set()
        for a in grup:
            if a["skor"] >= AMBANG_HEADLINE and a["skala"] != "MIKRO":
                tema_sesi[sesi].update(tema_dari(a["judul"]))

    urut = sorted(per_sesi)
    hasil = {}
    for i, sesi in enumerate(urut):
        grup = per_sesi[sesi]
        # Nada makro dihitung hanya dari berita seluruh-pasar. Kalau berita
        # satu emiten ikut, hari dengan 12 pengumuman dividen terbaca "pasar
        # optimis" padahal papan utamanya datar.
        layak = [a for a in grup
                 if a["skor"] >= AMBANG_HEADLINE and a["skala"] != "MIKRO"]

        n_naik = sum(1 for a in layak if nada(a["judul"]) > 0)
        n_turun = sum(1 for a in layak if nada(a["judul"]) < 0)
        berarah = n_naik + n_turun

        # tema dominan: yang diangkat paling banyak SITUS, bukan paling banyak
        # artikel -- satu situs yang menulis lima kali bukan konsensus.
        situs_tema = defaultdict(set)
        for a in layak:
            for tm in tema_dari(a["judul"]):
                situs_tema[tm].add(a["domain"])
        dominan = max(situs_tema.items(), key=lambda kv: len(kv[1]), default=None)

        # tema baru: ada hari ini, absen di N sesi sebelumnya
        sebelum = set()
        for j in range(max(0, i - SESI_LOOKBACK_BARU), i):
            sebelum |= tema_sesi.get(urut[j], set())
        baru = sorted(tema_sesi[sesi] - sebelum)

        # korroborasi: berapa persen artikel yang beritanya juga diangkat
        # situs lain (klaster berisi >1 domain)
        dom_klaster = defaultdict(set)
        for a in grup:
            dom_klaster[a["cluster_id"]].add(a["domain"])
        didukung = sum(1 for a in grup if len(dom_klaster[a["cluster_id"]]) > 1)

        # --- bacaan mikro: saham apa yang ramai hari ini --------------------
        per_kode = defaultdict(lambda: {"n": 0, "naik": 0, "turun": 0, "situs": set()})
        for a in grup:
            if not a["emiten"]:
                continue
            nd = nada(a["judul"])
            for kode in a["emiten"].split(","):
                d = per_kode[kode]
                d["n"] += 1
                d["situs"].add(a["domain"])
                if nd > 0:
                    d["naik"] += 1
                elif nd < 0:
                    d["turun"] += 1
        top_emiten = sorted(per_kode.items(),
                            key=lambda kv: (-kv[1]["n"], -len(kv[1]["situs"]), kv[0]))

        hasil[sesi] = {
            "naik": n_naik, "turun": n_turun,
            "arah": 0 if not berarah else round((n_naik - n_turun) / berarah, 2),
            "dominan": [dominan[0], len(dominan[1])] if dominan else None,
            "baru": baru[:3],
            "korr": round(didukung / len(grup) * 100) if grup else 0,
            "situs": len({a["domain"] for a in grup}),
            "tema": sorted(tema_sesi[sesi]),
            "n_makro": sum(1 for a in grup if a["skala"] == "MAKRO"),
            "n_mikro": sum(1 for a in grup if a["skala"] == "MIKRO"),
            "n_umum": sum(1 for a in grup if a["skala"] not in ("MAKRO", "MIKRO")),
            "emiten": [[k, d["n"], d["naik"], d["turun"]]
                       for k, d in top_emiten[:8]],
            "n_emiten": len(per_kode),
        }

    # --- event-study per tema ------------------------------------------------
    # Pembandingnya WAJIB sesi yang kita punya beritanya, bukan seluruh sejarah
    # IHSG. Kalau arsip berita cuma menutupi satu jendela yang kebetulan pasar
    # sedang naik, membandingkannya dengan median 20 tahun membuat SEMUA tema
    # tampak positif -- itu bias seleksi, bukan temuan. Dengan basis se-periode,
    # yang terbaca adalah tema mana yang menonjol DI DALAM periode itu sendiri.
    sesi_terliput = [s for s in urut if ret_ihsg.get(s) is not None]
    ret_terliput = [ret_ihsg[s] for s in sesi_terliput]
    dasar = _median(ret_terliput) if ret_terliput else 0

    stat = {}
    milik_tema = defaultdict(list)
    for sesi, tm in tema_sesi.items():
        for nama in tm:
            r = ret_ihsg.get(sesi)
            if r is not None:
                milik_tema[nama].append((sesi, r))
    for nama, pasang in milik_tema.items():
        if len(pasang) < MIN_SAMPEL_TEMA:
            continue
        rets = [r for _, r in pasang]
        stat[nama] = {
            "n": len(rets),
            "median": round(_median(rets), 3),
            "positif": sum(1 for r in rets if r > 0),
            "terakhir": max(s for s, _ in pasang),
        }
    # Di bawah ambang ini, apa pun yang keluar cuma derau. Lebih baik panelnya
    # bilang "belum cukup data" daripada menyodorkan angka yang terlihat pasti.
    cukup = len(ret_terliput) >= MIN_SESI_EVENT_STUDY
    return hasil, {
        "tema": stat if cukup else {},
        "dasar": round(dasar, 3),
        "n_sesi": len(ret_terliput),
        "periode": [sesi_terliput[0], sesi_terliput[-1]] if sesi_terliput else None,
        "min_sampel": MIN_SAMPEL_TEMA,
        "min_sesi": MIN_SESI_EVENT_STUDY,
        "cukup": cukup,
    }
