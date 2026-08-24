"""Ekspor SQLite -> JSON statis buat situs.

Dipecah beberapa lapis supaya situs enteng dibuka:
  meta.json            - status update, daftar indeks, rentang data
  emiten.json          - daftar kode saham + nama + sektor (dipakai panel MIKRO)
  pasar.json           - seluruh bar indeks + dua acuan divergensi (sekali muat)
  hari.json            - ringkasan per hari bursa + 3 klaster teratas (scrub/ribbon)
  berita/YYYY-MM.json  - detail lengkap per bulan, dimuat saat dibutuhkan saja
"""
import json
from collections import defaultdict
from datetime import datetime

from config import (AMBANG_DIVERGENSI, AMBANG_HEADLINE, AMBANG_MOVE, DATA_DIR,
                    INDICES, REF_ASIA, REF_GLOBAL, SUMBER)
import sintesis
from store import db, url_hash


def _tulis(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return path.stat().st_size


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _ret_tergeser(bars, kode, lag):
    """Return harian `kode`, dipetakan ke tanggal IDX yang bisa mencernanya.

    Bursa yang tutup setelah IDX (Wall Street, lag=1) baru berpengaruh sehari
    kemudian; bursa Asia (lag=0) sudah selesai sebelum IDX tutup, jadi dipakai
    apa adanya. Menyamaratakan lag untuk semua bursa asing membalik arah
    sebab-akibat untuk Asia.
    """
    baris = sorted(bars.get(kode, []))
    tgl = [t for t, *_ in baris]
    ret = {t: r for t, _, r, _ in baris}
    if not lag:
        return ret
    return {tgl[i + lag]: ret[tgl[i]] for i in range(len(tgl) - lag)}


def jalankan():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db() as con:
        bars = defaultdict(list)
        for r in con.execute("SELECT kode,tanggal,c,ret_pct,v FROM bars ORDER BY tanggal"):
            bars[r["kode"]].append((r["tanggal"], r["c"], r["ret_pct"], r["v"]))

        klaster = [dict(r) for r in con.execute(
            "SELECT id,judul_wakil,session_date,kategori,skala,ukuran,skor FROM clusters"
            " ORDER BY session_date, skor DESC")]
        artikel = [dict(r) for r in con.execute(
            "SELECT id,cluster_id,url,domain,judul,ringkasan,published_wib,"
            "session_date,luar_jam,kategori,skala,emiten,wilayah,skor FROM articles"
            " WHERE cluster_id IS NOT NULL ORDER BY skor DESC")]
        daftar_emiten = {r["kode"]: [r["nama"], r["sektor"]] for r in con.execute(
            "SELECT kode,nama,sektor FROM emiten ORDER BY kode")}

    ihsg = {t: (c, r) for t, c, r, _ in bars.get("IHSG", [])}
    hari_ihsg = [t for t, *_ in bars.get("IHSG", [])]

    # --- dua acuan divergensi ------------------------------------------------
    # Global: IHSG vs S&P 500 sesi sebelumnya -- selera risiko dunia.
    # Asia:   IHSG vs median tetangga sesi yang sama -- pembanding yang secara
    #         empiris jauh lebih nyambung (SET .35, KOSPI .33, STI .31,
    #         NIKKEI .30 vs SPX .24, diukur Agu 2023-Agu 2026).
    lag = {i["kode"]: i["lag"] for i in INDICES}
    ret_global = _ret_tergeser(bars, REF_GLOBAL, lag.get(REF_GLOBAL, 1))
    ret_asia = {k: _ret_tergeser(bars, k, lag.get(k, 0))
                for k in REF_ASIA if bars.get(k)}

    div_global, div_asia = {}, {}
    for t in hari_ihsg:
        ri = ihsg[t][1]
        if ri is None:
            continue
        rg = ret_global.get(t)
        if rg is not None:
            div_global[t] = round(ri - rg, 3)
        tetangga = [r[t] for r in ret_asia.values() if r.get(t) is not None]
        if tetangga:
            div_asia[t] = round(ri - _median(tetangga), 3)

    pasar = {
        "indeks": [
            {"kode": i["kode"], "nama": i["nama"], "negara": i["negara"],
             "utama": i["utama"], "awal": i["awal"],
             "lag": i["lag"],
             "bar": [[t, c, r] for t, c, r, _ in bars.get(i["kode"], [])]}
            for i in INDICES if bars.get(i["kode"])
        ],
        "divergensi": {"global": div_global, "asia": div_asia},
        "ref": {"global": REF_GLOBAL, "asia": REF_ASIA},
    }

    # --- ringkasan harian ----------------------------------------------------
    kunci_klaster = {}
    for a in sorted(artikel, key=lambda x: (x["cluster_id"], -x["skor"])):
        kunci_klaster.setdefault(a["cluster_id"], url_hash(a["url"])[:12])

    klaster_per_hari = defaultdict(list)
    for k in klaster:
        klaster_per_hari[k["session_date"]].append(k)
    jml_kat = defaultdict(lambda: defaultdict(int))
    jml_skala = defaultdict(lambda: defaultdict(int))
    # Hitungan per wilayah ikut ke hari.json, bukan ke berkas bulanan: peta
    # harus bisa dianimasikan lintas tahun tanpa menarik satu pun berkas
    # berita. Isinya cuma belasan angka per hari, jadi murah.
    jml_wil = defaultdict(lambda: defaultdict(int))
    for a in artikel:
        jml_kat[a["session_date"]][a["kategori"]] += 1
        jml_skala[a["session_date"]][a["skala"] or "UMUM"] += 1
        for w in (a["wilayah"] or "").split(","):
            if w:
                jml_wil[a["session_date"]][w] += 1

    def top3(t):
        """Headline hari: hanya klaster berskala pasar.

        Berita satu emiten sengaja tidak boleh jadi headline hari. Tanpa batas
        ini, satu hari dengan lima pengumuman dividen menutupi hari ketika BI
        memangkas suku bunga -- padahal yang menggerakkan papan itu yang kedua.
        Emiten punya panelnya sendiri.
        """
        return [{"j": k["judul_wakil"], "k": k["kategori"], "u": k["ukuran"],
                 "s": k["skor"], "id": kunci_klaster.get(k["id"])}
                for k in klaster_per_hari.get(t, [])[:6]
                if k["skor"] >= AMBANG_HEADLINE and k["skala"] != "MIKRO"][:3]

    hari = {}
    for t in hari_ihsg:
        ks = klaster_per_hari.get(t, [])
        c, ret = ihsg[t]
        skor_maks = max((k["skor"] for k in ks), default=0)
        dg, da = div_global.get(t), div_asia.get(t)
        div_maks = max(abs(dg or 0), abs(da or 0))
        hari[t] = {
            "c": c, "r": ret, "dg": dg, "da": da,
            "n": sum(jml_kat[t].values()),
            "kat": dict(jml_kat[t]),
            "sk": dict(jml_skala[t]),
            "w": dict(jml_wil[t]),
            "s": round(skor_maks, 2),
            # Penanda hari penting = hari yang GERAKNYA menonjol, bukan yang
            # beritanya ramai. Sempat memakai "skor >= 7" juga; setelah berita
            # bursa punya kategori sendiri, ambang itu tercapai hampir tiap
            # hari dan chartnya berubah jadi pagar garis vertikal.
            "p": 1 if (abs(ret or 0) >= AMBANG_MOVE
                       or div_maks >= AMBANG_DIVERGENSI) else 0,
            "top": top3(t),
        }

    # Sesi yang barnya belum terbit (mis. berita akhir pekan yang menempel ke
    # Senin) tetap harus muncul, kalau tidak berita terbaru justru tak terlihat
    # -- padahal itu yang paling sering dilihat. Harganya null.
    sesi_mendatang = sorted({a["session_date"] for a in artikel
                             if hari_ihsg and a["session_date"] > hari_ihsg[-1]})
    for t in sesi_mendatang:
        ks = klaster_per_hari.get(t, [])
        hari[t] = {
            "c": None, "r": None, "dg": None, "da": None,
            "n": sum(jml_kat[t].values()), "kat": dict(jml_kat[t]),
            "sk": dict(jml_skala[t]), "w": dict(jml_wil[t]),
            "s": round(max((k["skor"] for k in ks), default=0), 2),
            "p": 1, "mendatang": 1, "top": top3(t),
        }

    # --- kesimpulan lintas-sumber --------------------------------------------
    ringkas, tema_stat = sintesis.hitung()
    for t, r in ringkas.items():
        if t in hari:
            hari[t]["sin"] = r

    # --- detail berita per bulan ---------------------------------------------
    per_bulan = defaultdict(lambda: defaultdict(list))
    for a in artikel:
        per_bulan[a["session_date"][:7]][a["session_date"]].append({
            "id": url_hash(a["url"])[:12], "c": kunci_klaster.get(a["cluster_id"]),
            "j": a["judul"], "r": (a["ringkasan"] or "")[:280] or None,
            "u": a["url"], "d": a["domain"],
            "nm": SUMBER.get(a["domain"], {}).get("nama", a["domain"]),
            "t": a["published_wib"], "lj": a["luar_jam"],
            "k": a["kategori"], "sk": a["skala"] or "UMUM",
            "e": a["emiten"].split(",") if a["emiten"] else None,
            "s": a["skor"],
        })

    total = 0
    for bln, isi in per_bulan.items():
        total += _tulis(DATA_DIR / "berita" / (bln + ".json"), isi)

    meta = {
        "diperbarui": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "indeks": [
            {"kode": i["kode"], "nama": i["nama"], "negara": i["negara"],
             "awal": i["awal"],
             "last": bars[i["kode"]][-1][1] if bars.get(i["kode"]) else None,
             "ret": bars[i["kode"]][-1][2] if bars.get(i["kode"]) else None,
             "tgl": bars[i["kode"]][-1][0] if bars.get(i["kode"]) else None}
            for i in INDICES if bars.get(i["kode"])
        ],
        "berita": {"artikel": len(artikel), "klaster": len(klaster),
                   "bulan": sorted(per_bulan.keys()),
                   "mikro": sum(1 for a in artikel if a["skala"] == "MIKRO"),
                   "makro": sum(1 for a in artikel if a["skala"] == "MAKRO")},
        "sumber": sorted({SUMBER.get(a["domain"], {}).get("nama", a["domain"])
                          for a in artikel}),
        "rentang": [hari_ihsg[0], hari_ihsg[-1]] if hari_ihsg else None,
        "sesi_mendatang": sesi_mendatang,
        "ambang": {"move": AMBANG_MOVE, "divergensi": AMBANG_DIVERGENSI},
    }

    n5 = _tulis(DATA_DIR / "emiten.json", daftar_emiten)
    n4 = _tulis(DATA_DIR / "tema.json", tema_stat)
    n1 = _tulis(DATA_DIR / "pasar.json", pasar)
    n2 = _tulis(DATA_DIR / "hari.json", hari)
    n3 = _tulis(DATA_DIR / "meta.json", meta)
    print("  pasar.json  %8.1f KB  (%d indeks, %d bar)"
          % (n1 / 1024, len(pasar["indeks"]), sum(len(b) for b in bars.values())))
    print("  hari.json   %8.1f KB  (%d hari)" % (n2 / 1024, len(hari)))
    print("  berita/     %8.1f KB  (%d bulan, %d artikel)"
          % (total / 1024, len(per_bulan), len(artikel)))
    print("  tema.json   %8.1f KB  (%d tema, %d sesi terliput%s)"
          % (n4 / 1024, len(tema_stat["tema"]), tema_stat["n_sesi"],
             "" if tema_stat["cukup"] else ", belum cukup untuk event-study"))
    print("  emiten.json %8.1f KB  (%d kode)" % (n5 / 1024, len(daftar_emiten)))
    print("  meta.json   %8.1f KB  (%d berita mikro, %d makro)"
          % (n3 / 1024, meta["berita"]["mikro"], meta["berita"]["makro"]))
    return meta
