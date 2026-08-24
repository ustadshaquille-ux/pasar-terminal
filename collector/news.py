"""Pengumpul berita: indeks Detik & CNBC (backfill historis) + RSS (jalur maju).

Semua artikel disimpan apa adanya. Penyaringan makro/relevansi dikerjakan
di lapisan skor (skor.py) supaya aturannya bisa diubah tanpa scrape ulang.
"""
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from config import UA, RSS_FEEDS
from waktu import parse_cnbc_url, parse_detik, parse_iso, parse_rfc822

JEDA = 2.0  # detik antar request, sopan


def _get(url, timeout=40, coba=3):
    for i in range(coba):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                return None            # halaman memang tidak ada / ditolak
            if i == coba - 1:
                return None
        except Exception:
            if i == coba - 1:
                return None
        time.sleep(3 * (i + 1))
    return None


def _bersih(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


# --- Detik ------------------------------------------------------------------
def detik_indeks(tanggal, halaman=1):
    """tanggal: date/datetime. Balikin list artikel mentah."""
    url = (f"https://finance.detik.com/indeks?date={tanggal:%m/%d/%Y}"
           + (f"&page={halaman}" if halaman > 1 else ""))
    h = _get(url)
    if not h:
        return []
    out = []
    for blok in re.findall(r"<article.*?</article>", h, re.S):
        m_url = re.search(r'href="(https?://[^"]+)"', blok)
        m_jud = re.search(r'class="media__title".*?>(.*?)</a>', blok, re.S) \
             or re.search(r"<h3[^>]*>(.*?)</h3>", blok, re.S)
        m_tgl = re.search(r'class="media__date".*?title="([^"]+)"', blok, re.S)
        if not (m_url and m_jud):
            continue
        dt = parse_detik(m_tgl.group(1)) if m_tgl else None
        judul = _bersih(m_jud.group(1))
        if not judul:
            continue
        out.append({
            "url": m_url.group(1), "domain": "finance.detik.com",
            "judul": judul, "ringkasan": None, "dt": dt,
        })
    return out


# --- CNBC Indonesia ---------------------------------------------------------
def cnbc_indeks(tanggal, halaman=1):
    url = (f"https://www.cnbcindonesia.com/indeks?date={tanggal:%Y/%m/%d}"
           + (f"&page={halaman}" if halaman > 1 else ""))
    h = _get(url)
    if not h:
        return []
    out, lihat = [], set()
    for blok in re.findall(r"<article.*?</article>", h, re.S):
        m_url = re.search(r'href="(https?://www\.cnbcindonesia\.com/[^"]+)"', blok)
        m_jud = re.search(r"<h2[^>]*>(.*?)</h2>", blok, re.S) \
             or re.search(r"<h3[^>]*>(.*?)</h3>", blok, re.S)
        if not (m_url and m_jud):
            continue
        u = m_url.group(1)
        if u in lihat:
            continue
        lihat.add(u)
        judul = _bersih(m_jud.group(1))
        if not judul:
            continue
        out.append({
            "url": u, "domain": "www.cnbcindonesia.com",
            "judul": judul, "ringkasan": None, "dt": parse_cnbc_url(u),
        })
    return out


# --- Liputan6 ---------------------------------------------------------------
def liputan6_indeks(tanggal, halaman=1):
    """Indeks bisnis Liputan6. Paling bersih dari semua: waktu terbitnya ISO
    lengkap dengan zona waktu, jadi tidak perlu menebak apa pun."""
    url = (f"https://www.liputan6.com/bisnis/indeks/{tanggal:%Y/%m/%d}"
           + (f"?page={halaman}" if halaman > 1 else ""))
    h = _get(url)
    if not h:
        return []
    out, lihat = [], set()
    for blok in re.findall(r"<article.*?</article>", h, re.S):
        m_url = re.search(r'href="(https?://www\.liputan6\.com/[^"]*/read/[^"]+)"', blok)
        m_jud = re.search(r'title="([^"]+)"', blok)              or re.search(r"<h[234][^>]*>(.*?)</h[234]>", blok, re.S)
        m_tgl = re.search(r'datetime="([^"]+)"', blok)
        if not (m_url and m_jud):
            continue
        u = m_url.group(1)
        if u in lihat:
            continue
        lihat.add(u)
        judul = _bersih(m_jud.group(1))
        if not judul:
            continue
        out.append({
            "url": u, "domain": "www.liputan6.com",
            "judul": judul, "ringkasan": None,
            "dt": parse_iso(m_tgl.group(1)) if m_tgl else None,
        })
    return out


# --- RSS --------------------------------------------------------------------
def domain_dari(tautan, cadangan):
    """Domain diambil dari URL artikelnya, bukan dari baris feed.

    Satu situs bisa punya beberapa feed (Detik punya rubrik umum dan rubrik
    bursa & valas). Kalau domain diambil dari konfigurasi feed, satu situs
    yang sama bisa tercatat dua kali sebagai dua "sumber" -- dan hitungan
    korroborasi lintas-situs jadi bohong: satu media terlihat seperti dua.
    """
    try:
        h = urllib.parse.urlparse(tautan).netloc.lower()
    except ValueError:
        return cadangan
    return h.removeprefix("amp.") or cadangan


def rss(url, domain):
    h = _get(url, timeout=25)
    if not h:
        return []
    out = []
    for item in re.findall(r"<item[ >].*?</item>", h, re.S):
        m_jud = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.S)
        m_url = re.search(r"<link>(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?</link>", item, re.S)
        m_tgl = re.search(r"<pubDate>(.*?)</pubDate>", item, re.S)
        m_des = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.S)
        if not (m_jud and m_url):
            continue
        u = _bersih(m_url.group(1))
        if not u.startswith("http"):
            continue
        out.append({
            "url": u, "domain": domain_dari(u, domain),
            "judul": _bersih(m_jud.group(1)),
            "ringkasan": _bersih(m_des.group(1))[:400] if m_des else None,
            "dt": parse_rfc822(m_tgl.group(1)) if m_tgl else None,
        })
    return out


def semua_rss():
    hasil = []
    for url, domain in RSS_FEEDS:
        n = len(hasil)
        hasil.extend(rss(url, domain))
        print(f"  rss {domain:24} +{len(hasil)-n}")
        time.sleep(1)
    return hasil


def lengkapi(items, kalender):
    """Isi published_wib / session_date / luar_jam. Buang yang tanpa waktu."""
    keluar, sekarang = [], datetime.now().isoformat(timespec="seconds")
    for it in items:
        dt = it.get("dt")
        if dt is None:
            continue
        sesi, luar = kalender.sesi_untuk(dt)
        if sesi is None:
            continue  # di luar rentang kalender bursa yang kita punya
        keluar.append({
            "url": it["url"], "domain": it["domain"], "judul": it["judul"],
            "ringkasan": it.get("ringkasan"),
            "published_wib": dt.isoformat(timespec="seconds"),
            "session_date": sesi, "luar_jam": luar, "diambil_pada": sekarang,
        })
    return keluar
