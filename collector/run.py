"""Runner. Dipakai manual maupun oleh GitHub Actions.

  python run.py impor            pulihkan arsip JSON -> SQLite
  python run.py indices          bar indeks terbaru (cepat)
  python run.py rss              tarik semua RSS (jalur maju)
  python run.py backfill 30      indeks Detik+CNBC mundur N hari
  python run.py backfill 30 2024-06-30   mundur N hari dari tanggal tertentu
  python run.py proses           kategori + klaster + skor ulang
  python run.py export           tulis JSON ke site/data
  python run.py peta             bangun ulang kisi PETA DAMPAK (jarang perlu)
  python run.py update           indices + rss + proses + export   <- dipakai cron
"""
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta

import export
import impor
import indices
import news
import peta as peta_mod
import skor
import store
from config import DB_PATH
from waktu import Kalender


def kalender():
    con = sqlite3.connect(DB_PATH)
    hari = [r[0] for r in con.execute("SELECT tanggal FROM bars WHERE kode='IHSG'")]
    con.close()
    if not hari:
        sys.exit("Belum ada bar IHSG. Jalankan dulu: python run.py indices")
    return Kalender(hari)


def tarik_indices():
    print("[indeks]")
    baris, _ = indices.ambil_semua()
    store.simpan_bars(baris)
    print("  %d bar tersimpan" % len(baris))


def tarik_rss():
    print("[rss]")
    item = news.semua_rss()
    baru = store.simpan_artikel(news.lengkapi(item, kalender()))
    print("  %d item ditarik, %d baru" % (len(item), baru))
    return baru


# (kunci_log, domain, pengambil, maks_halaman, ambang_anggap_lengkap)
# Ambang dicek PER SUMBER, bukan sekali untuk seluruh hari. Kalau tidak,
# menambah sumber baru jadi percuma: hari yang sudah pernah diambil Detik akan
# dilewati seluruhnya dan sumber barunya tidak pernah ikut tertarik.
SUMBER_BACKFILL = [
    ("detik",    "finance.detik.com",     lambda d, p: news.detik_indeks(d, p),    10, 15),
    ("liputan6", "www.liputan6.com",      lambda d, p: news.liputan6_indeks(d, p),  7, 10),
    ("cnbc",     "www.cnbcindonesia.com", lambda d, p: news.cnbc_indeks(d, p),      2,  3),
]


def backfill(n_hari, mulai=None):
    kal = kalender()
    akhir = datetime.strptime(mulai, "%Y-%m-%d").date() if mulai else date.today()
    print("[backfill] %d hari mundur dari %s | sumber: %s"
          % (n_hari, akhir, ", ".join(k for k, *_ in SUMBER_BACKFILL)))
    total_baru = 0
    for i in range(n_hari):
        d = akhir - timedelta(days=i)
        item, lewat = [], []
        for kunci, domain, ambil, maks_hal, ambang in SUMBER_BACKFILL:
            if store.liputan_harian(d, domain) >= ambang:
                lewat.append(kunci)
                continue
            for hal in range(1, maks_hal + 1):
                klog = "%s:%s:p%d" % (kunci, d, hal)
                if store.sudah_diambil(klog):
                    continue
                got = ambil(d, hal)
                store.catat_ambil(klog, len(got),
                                  datetime.now().isoformat(timespec="seconds"))
                if not got:
                    break
                item += got
                time.sleep(news.JEDA)

        baru = store.simpan_artikel(news.lengkapi(item, kal)) if item else 0
        total_baru += baru
        catatan = (" lewat=" + ",".join(lewat)) if lewat else ""
        print("  %s  ambil=%4d  baru=%4d  (kumulatif %d)%s"
              % (d, len(item), baru, total_baru, catatan), flush=True)
    print("[backfill] selesai, %d artikel baru" % total_baru)


def perbaiki_sesi_terbaru(hari_mundur=21):
    """Hitung ulang session_date artikel terbaru.

    Sesi artikel yang jatuh sesudah bar terakhir cuma proyeksi hari kerja, yang
    tidak tahu libur bursa. Begitu bar aslinya masuk, ekor itu dikoreksi.
    """
    kal = kalender()
    batas = (datetime.strptime(kal.hari[-1], "%Y-%m-%d")
             - timedelta(days=hari_mundur)).strftime("%Y-%m-%d")
    ubah = 0
    with store.db() as con:
        rows = con.execute(
            "SELECT id,published_wib,session_date FROM articles WHERE published_wib >= ?",
            (batas,)).fetchall()
        for r in rows:
            dt = datetime.fromisoformat(r["published_wib"])
            sesi, luar = kal.sesi_untuk(dt)
            if sesi and sesi != r["session_date"]:
                con.execute("UPDATE articles SET session_date=?,luar_jam=? WHERE id=?",
                            (sesi, luar, r["id"]))
                ubah += 1
    print("[koreksi sesi] %d dari %d artikel terbaru disesuaikan" % (ubah, len(rows)))


def proses():
    n_art, n_klu, n_emiten = skor.proses()
    print("[proses] %d artikel -> %d klaster, %d kode emiten dipelajari"
          % (n_art, n_klu, n_emiten))


if __name__ == "__main__":
    store.init()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    if cmd == "indices":
        tarik_indices()
    elif cmd == "rss":
        tarik_rss()
    elif cmd == "backfill":
        backfill(int(sys.argv[2]) if len(sys.argv) > 2 else 30,
                 sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "proses":
        perbaiki_sesi_terbaru()
        proses()
    elif cmd == "export":
        print("[export]")
        export.jalankan()
    elif cmd == "peta":
        print("[peta]")
        peta_mod.bangun()
    elif cmd == "impor":
        impor.jalankan()
    elif cmd == "update":
        impor.jalankan()
        tarik_indices()
        tarik_rss()
        perbaiki_sesi_terbaru()
        proses()
        print("[export]")
        export.jalankan()
    else:
        sys.exit(__doc__)
