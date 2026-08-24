"""Bangun peta titik dunia untuk PETA DAMPAK — sekali jalan, hasilnya diarsip.

Kenapa peta titik, bukan peta garis negara. Tiga alasan, urut kepentingannya:

  1. Berat. Satu berkas batas negara yang layak itu ratusan KB, dan situs ini
     sudah memuat 1,5 MB bar harga. Kisi titik 2 derajat muat di ~13 KB teks
     dan tetap terbaca sebagai bentuk benua.
  2. Jujur soal ketelitiannya. Berita tidak punya koordinat. Yang kita tahu
     cuma "artikel ini menyebut China". Menggambar batas provinsi Guangdong
     dengan presisi vektor itu berbohong tentang seberapa halus datanya.
     Titik kasar menyampaikan "sekitar sini" — dan itu memang yang kita tahu.
  3. Satu titik = satu satuan cahaya. Wilayah yang ramai menyala terangnya
     bertambah tanpa perlu gradasi atau bayangan; cocok dengan palet layar
     hitam.

Hasilnya `site/data/peta.json`, dan situs tidak pernah lagi menyentuh jaringan
untuk ini. Jalankan ulang hanya kalau kisi/wilayahnya diubah:

    python run.py peta

Sumber garis pantai: Natural Earth 110m (domain publik).
"""
import json
import urllib.request

from config import DATA_DIR, INDICES, ROOT, UA

SUMBER_LAND = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
               "master/geojson/ne_110m_land.geojson")
CACHE = ROOT / "collector" / "cache_land.geojson"

# Kisi. Lintang dipotong di 80°U dan 58°S: Antarktika dan tudung Arktik
# memakan sepertiga tinggi peta dan tidak pernah jadi berita pasar.
LANGKAH = 2.0
LON0, LON1 = -180.0, 180.0
LAT0, LAT1 = 80.0, -58.0

# Kotak wilayah, diperiksa berurutan — yang pertama cocok menang. Sengaja
# kasar: ini pengelompokan berita, bukan atlas. Yang penting tiap benua jatuh
# ke ember yang sama dengan kata kunci di config.WILAYAH.
#
# Urutannya menyelesaikan tumpang tindih: Indonesia diambil sebelum ASEAN,
# Jepang/Korea sebelum China, China sebelum Rusia (Manchuria ikut China).
KOTAK = [
    # (wilayah, lon_min, lon_max, lat_min, lat_max)
    ("ID",    94.0,  141.5, -11.5,   6.5),
    ("JP_KR", 124.0, 146.5,  30.0,  46.5),
    ("ASEAN", 92.0,  127.5, -11.0,  24.0),
    ("IN",    67.0,   92.5,   5.0,  36.5),
    ("CN",    73.0,  126.0,  17.0,  50.0),
    ("RU",    27.0,  180.0,  48.0,  78.0),
    ("ME",    25.0,   64.0,  11.0,  43.0),
    ("EU",   -26.0,   45.0,  35.0,  72.0),
    ("AF",   -20.0,   52.0, -36.0,  37.5),
    ("AU",   110.0,  180.0, -48.0,  -9.0),
    ("US",  -170.0,  -52.0,  13.0,  74.0),
    ("LATAM", -85.0, -32.0, -56.0,  14.0),
]

# Satu huruf per sel. '.' laut. Huruf lain = wilayah; 'X' darat yang tidak
# masuk ember mana pun (kepulauan Pasifik, Greenland) — tetap digambar redup
# supaya bentuk dunianya utuh.
HURUF = {"ID": "I", "ASEAN": "A", "CN": "C", "JP_KR": "J", "IN": "N",
         "US": "U", "EU": "E", "ME": "M", "AU": "O", "RU": "R",
         "AF": "F", "LATAM": "L"}
LAUT = "."
LAIN = "X"


def _unduh():
    if CACHE.exists() and CACHE.stat().st_size > 10_000:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    req = urllib.request.Request(SUMBER_LAND, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        mentah = r.read().decode("utf-8")
    CACHE.write_text(mentah, encoding="utf-8")
    return json.loads(mentah)


def _cincin(geo):
    """Semua cincin luar dari Polygon/MultiPolygon, plus kotak pembatasnya.

    Cincin dalam (danau) diabaikan: pada kisi 2 derajat, Laut Kaspia pun cuma
    beberapa sel, dan mengurusnya menambah rumit tanpa menambah yang terlihat.
    """
    keluar = []
    for f in geo["features"]:
        g = f["geometry"]
        poligon = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for p in poligon:
            luar = p[0]
            xs = [c[0] for c in luar]
            ys = [c[1] for c in luar]
            keluar.append((luar, min(xs), max(xs), min(ys), max(ys)))
    return keluar


def _di_dalam(x, y, cincin):
    """Ray casting. Satu titik, satu cincin."""
    di = False
    n = len(cincin)
    j = n - 1
    for i in range(n):
        xi, yi = cincin[i][0], cincin[i][1]
        xj, yj = cincin[j][0], cincin[j][1]
        if (yi > y) != (yj > y):
            potong = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < potong:
                di = not di
        j = i
    return di


def _wilayah_di(x, y):
    for nama, x0, x1, y0, y1 in KOTAK:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return HURUF[nama]
    return LAIN


def bangun():
    geo = _unduh()
    cincin = _cincin(geo)

    kolom = int(round((LON1 - LON0) / LANGKAH))
    baris = int(round((LAT0 - LAT1) / LANGKAH))
    sel = []
    darat = 0
    for b in range(baris):
        y = LAT0 - (b + 0.5) * LANGKAH
        kandidat = [c for c in cincin if c[3] <= y <= c[4]]
        potong = []
        for k in range(kolom):
            x = LON0 + (k + 0.5) * LANGKAH
            ada = any(x0 <= x <= x1 and _di_dalam(x, y, r)
                      for r, x0, x1, _, _ in kandidat)
            if ada:
                darat += 1
                potong.append(_wilayah_di(x, y))
            else:
                potong.append(LAUT)
        sel.append("".join(potong))

    # Simpul bursa: satu per kota. Dua indeks di kota yang sama (SPX & Nasdaq
    # di New York) berbagi satu simpul, kodenya ditumpuk di label.
    kota = {}
    for i in INDICES:
        if "lon" not in i:
            continue
        k = kota.setdefault(i["kota"], {"kota": i["kota"], "lon": i["lon"],
                                        "lat": i["lat"], "kode": []})
        k["kode"].append(i["kode"])

    peta = {
        "kolom": kolom, "baris": baris,
        "lon0": LON0, "lat0": LAT0, "langkah": LANGKAH,
        "huruf": {v: k for k, v in HURUF.items()},
        "sel": sel,
        "bursa": list(kota.values()),
    }
    keluar = DATA_DIR / "peta.json"
    keluar.parent.mkdir(parents=True, exist_ok=True)
    with open(keluar, "w", encoding="utf-8") as f:
        json.dump(peta, f, ensure_ascii=False, separators=(",", ":"))
    print("  peta.json   %8.1f KB  (%dx%d sel, %d darat, %d simpul bursa)"
          % (keluar.stat().st_size / 1024, kolom, baris, darat, len(kota)))
    return peta


if __name__ == "__main__":
    bangun()
