"""Lapisan SQLite. Semua tulis bersifat idempoten lewat url_hash / (kode,tanggal)."""
import hashlib
import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SKEMA = """
CREATE TABLE IF NOT EXISTS bars (
    kode      TEXT NOT NULL,
    tanggal   TEXT NOT NULL,          -- YYYY-MM-DD, tanggal bursa lokal
    o REAL, h REAL, l REAL, c REAL, v REAL,
    ret_pct   REAL,                   -- % vs close sebelumnya
    PRIMARY KEY (kode, tanggal)
);

CREATE TABLE IF NOT EXISTS articles (
    id            INTEGER PRIMARY KEY,
    url_hash      TEXT UNIQUE NOT NULL,
    url           TEXT NOT NULL,
    domain        TEXT NOT NULL,
    judul         TEXT NOT NULL,
    ringkasan     TEXT,
    published_wib TEXT,               -- ISO 'YYYY-MM-DDTHH:MM:SS', waktu terbit asli
    session_date  TEXT,               -- sesi bursa yang kena dampak
    luar_jam      INTEGER DEFAULT 0,  -- 1 = terbit di luar jam bursa
    kategori      TEXT,             -- soal apa (BURSA, MAKRO_DOMESTIK, ...)
    wilayah       TEXT,             -- dari mana (US,CN,ID -- boleh lebih dari satu)
    skala         TEXT,             -- seluas apa (MAKRO / MIKRO / UMUM)
    emiten        TEXT,             -- kode saham yang disebut judul, dipisah koma
    skor          REAL DEFAULT 0,
    cluster_id    INTEGER,
    diambil_pada  TEXT
);
CREATE INDEX IF NOT EXISTS ix_art_sesi  ON articles(session_date);
CREATE INDEX IF NOT EXISTS ix_art_clu   ON articles(cluster_id);
CREATE INDEX IF NOT EXISTS ix_art_terbit ON articles(published_wib);

CREATE TABLE IF NOT EXISTS clusters (
    id           INTEGER PRIMARY KEY,
    judul_wakil  TEXT NOT NULL,
    session_date TEXT NOT NULL,
    kategori     TEXT,
    skala        TEXT,
    ukuran       INTEGER DEFAULT 1,
    skor         REAL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_clu_sesi ON clusters(session_date);

-- Daftar emiten: sebagian dikurasi tangan (emiten.py), sebagian dipelajari
-- sendiri dari pola "Nama Perusahaan (KODE)" di judul berita.
CREATE TABLE IF NOT EXISTS emiten (
    kode   TEXT PRIMARY KEY,
    nama   TEXT NOT NULL,
    sektor TEXT,
    sumber TEXT                     -- 'kurasi' | 'belajar'
);

-- catatan halaman indeks yang sudah diambil, biar backfill bisa dijeda-lanjut
CREATE TABLE IF NOT EXISTS fetch_log (
    kunci     TEXT PRIMARY KEY,       -- mis. 'detik:2024-01-15:p3'
    jumlah    INTEGER,
    waktu     TEXT
);
"""


def url_hash(url: str) -> str:
    """Normalisasi ringan sebelum hash supaya ?utm= nggak bikin duplikat."""
    u = url.split("?")[0].split("#")[0].rstrip("/")
    return hashlib.sha1(u.encode("utf-8")).hexdigest()


@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    # Backfill panjang jalan berjam-jam di latar; tanpa ini, proses lain yang
    # ikut menulis langsung kena "database is locked" alih-alih menunggu.
    con.execute("PRAGMA busy_timeout=30000")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init():
    with db() as con:
        con.executescript(SKEMA)
        # Database lama dibangun sebelum sumbu skala ada. Menambah kolomnya di
        # sini lebih murah daripada memaksa hapus-bangun-ulang pasar.db orang.
        punya = {r[1] for r in con.execute("PRAGMA table_info(articles)")}
        for kol in ("skala TEXT", "emiten TEXT", "wilayah TEXT"):
            if kol.split()[0] not in punya:
                con.execute("ALTER TABLE articles ADD COLUMN " + kol)
        punya = {r[1] for r in con.execute("PRAGMA table_info(clusters)")}
        if "skala" not in punya:
            con.execute("ALTER TABLE clusters ADD COLUMN skala TEXT")


def simpan_bars(rows):
    """rows: iterable of (kode, tanggal, o,h,l,c,v)"""
    with db() as con:
        con.executemany(
            "INSERT INTO bars(kode,tanggal,o,h,l,c,v) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(kode,tanggal) DO UPDATE SET "
            "o=excluded.o,h=excluded.h,l=excluded.l,c=excluded.c,v=excluded.v",
            list(rows),
        )
        # hitung ulang ret_pct per kode
        for (kode,) in con.execute("SELECT DISTINCT kode FROM bars"):
            con.execute("""
                UPDATE bars SET ret_pct = (
                    SELECT ROUND((bars.c / prev.c - 1) * 100, 4)
                    FROM bars prev
                    WHERE prev.kode = bars.kode AND prev.tanggal < bars.tanggal
                    ORDER BY prev.tanggal DESC LIMIT 1
                ) WHERE kode = ?
            """, (kode,))


def simpan_artikel(items):
    """items: dict dengan url, domain, judul, ringkasan, published_wib,
    session_date, luar_jam, diambil_pada. Balikin jumlah baris baru."""
    baru = 0
    with db() as con:
        for it in items:
            cur = con.execute(
                "INSERT OR IGNORE INTO articles"
                "(url_hash,url,domain,judul,ringkasan,published_wib,session_date,"
                " luar_jam,diambil_pada) VALUES(?,?,?,?,?,?,?,?,?)",
                (url_hash(it["url"]), it["url"], it["domain"], it["judul"],
                 it.get("ringkasan"), it.get("published_wib"), it.get("session_date"),
                 int(it.get("luar_jam", 0)), it.get("diambil_pada")),
            )
            baru += cur.rowcount
    return baru


def sudah_diambil(kunci: str) -> bool:
    with db() as con:
        return con.execute("SELECT 1 FROM fetch_log WHERE kunci=?", (kunci,)).fetchone() is not None


def catat_ambil(kunci: str, jumlah: int, waktu: str):
    with db() as con:
        con.execute("INSERT OR REPLACE INTO fetch_log(kunci,jumlah,waktu) VALUES(?,?,?)",
                    (kunci, jumlah, waktu))


def liputan_harian(tanggal, domain):
    """Berapa artikel domain ini yang sudah kita punya untuk tanggal TERBIT itu.

    Dipakai backfill supaya bisa dilanjut lintas run GitHub Actions: fetch_log
    ikut hilang saat database dibangun ulang, tapi artikelnya sendiri pulih
    dari arsip JSON, jadi liputan nyata inilah penanda kemajuan yang jujur.
    """
    with db() as con:
        return con.execute(
            "SELECT COUNT(*) FROM articles WHERE domain=? AND published_wib LIKE ?",
            (domain, str(tanggal) + "%")).fetchone()[0]
