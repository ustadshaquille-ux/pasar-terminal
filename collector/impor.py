"""Baca balik site/data/berita/*.json ke SQLite.

Arsip yang sesungguhnya adalah JSON di dalam repo, bukan pasar.db. Database
cuma file kerja: GitHub Actions membangunnya ulang tiap kali jalan, menambah
berita baru, lalu mengekspor JSON lagi. Dengan begitu tidak ada blob biner
yang di-commit 48 kali sehari, dan arsipnya tetap bisa dibaca manusia.
"""
import json

from config import DATA_DIR
from store import simpan_artikel


def jalankan():
    dir_berita = DATA_DIR / "berita"
    if not dir_berita.exists():
        print("[impor] belum ada arsip JSON, lewati")
        return 0

    total, berkas = 0, sorted(dir_berita.glob("*.json"))
    for f in berkas:
        try:
            isi = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print("[impor] %s dilewati: %s" % (f.name, e))
            continue
        item = []
        for sesi, arts in isi.items():
            for a in arts:
                item.append({
                    "url": a["u"], "domain": a["d"], "judul": a["j"],
                    "ringkasan": a.get("r"), "published_wib": a.get("t"),
                    "session_date": sesi, "luar_jam": a.get("lj", 0),
                    "diambil_pada": None,
                })
        total += simpan_artikel(item)
    print("[impor] %d berkas bulan, %d artikel dipulihkan" % (len(berkas), total))
    return total


if __name__ == "__main__":
    import store
    store.init()
    jalankan()
