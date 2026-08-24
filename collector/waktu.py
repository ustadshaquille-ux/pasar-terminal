"""Atribusi waktu: dari jam terbit artikel ke sesi bursa yang kena dampaknya.

Ini inti anti-lookahead-nya. Artikel terbit 19:00 Selasa TIDAK menggerakkan
candle Selasa -- dia menggerakkan Rabu. Berita Sabtu nempel ke Senin.
"""
import bisect
from datetime import datetime, timedelta

from config import JAM_TUTUP_IDX

BULAN_ID = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
    "jul": 7, "agu": 8, "ags": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


class Kalender:
    """Daftar tanggal bursa IDX, dipakai buat lompat ke sesi berikutnya."""

    def __init__(self, tanggal_bursa):
        self.hari = sorted(set(tanggal_bursa))
        self._set = set(self.hari)

    def sesi_berikut(self, tgl_str):
        """Sesi bursa pertama yang >= tgl_str.

        Kalau tgl_str melewati bar terakhir yang kita punya, sesi diproyeksikan
        ke hari kerja terdekat. Ini perlu supaya berita hari ini tidak terbuang
        cuma karena bar besok memang belum terbit. Proyeksi tidak tahu hari
        libur bursa, jadi `perbaiki_sesi_terbaru()` menghitung ulang bagian
        ekor ini tiap kali bar baru masuk.
        """
        if tgl_str in self._set:
            return tgl_str
        i = bisect.bisect_left(self.hari, tgl_str)
        if i < len(self.hari):
            return self.hari[i]
        d = datetime.strptime(tgl_str, "%Y-%m-%d")
        for _ in range(10):
            if d.weekday() < 5:          # Senin-Jumat
                return d.strftime("%Y-%m-%d")
            d += timedelta(days=1)
        return None

    def sesi_untuk(self, dt: datetime):
        """datetime terbit (WIB) -> (session_date, luar_jam)."""
        batas = dt.replace(hour=JAM_TUTUP_IDX[0], minute=JAM_TUTUP_IDX[1],
                           second=0, microsecond=0)
        tgl = dt.strftime("%Y-%m-%d")
        maju = (dt + timedelta(days=1)).strftime("%Y-%m-%d")

        if tgl in self._set:
            # hari bursa yang barnya sudah kita punya
            return (tgl, 0) if dt <= batas else (self.sesi_berikut(maju), 1)

        if tgl > self.hari[-1]:
            # Melewati bar terakhir: kalendernya belum ada, jadi diproyeksikan.
            # Bagian ini pernah salah dan salahnya tidak kelihatan: berita yang
            # terbit Senin 05:45 -- jam terbit paling padat, sebelum bursa buka
            # -- dianggap "bukan hari bursa" hanya karena bar Senin memang
            # belum terbit, lalu didorong ke sesi Selasa. Akibatnya seluruh
            # berita pagi menempel di hari yang salah, tepat pada hari yang
            # paling sering dibuka orang.
            if dt.weekday() < 5 and dt <= batas:
                return tgl, 0
            return self.sesi_berikut(maju), 1

        # di dalam rentang kalender tapi bukan hari bursa -> libur
        return self.sesi_berikut(maju), 1


def parse_detik(teks):
    """'Senin, 15 Jan 2024 23:03 WIB' -> datetime"""
    t = teks.replace(",", " ").split()
    # buang nama hari kalau ada
    if t and not t[0][0].isdigit():
        t = t[1:]
    try:
        hari = int(t[0])
        bln = BULAN_ID[t[1][:3].lower()]
        thn = int(t[2])
        jam, menit = (int(x) for x in t[3].split(":")[:2])
        return datetime(thn, bln, hari, jam, menit)
    except (IndexError, ValueError, KeyError):
        return None


def parse_cnbc_url(url):
    """CNBC nyelipin timestamp di URL: /news/20240115190155-4-506085/..."""
    import re
    m = re.search(r"/(\d{14})-", url)
    if not m:
        return None
    s = m.group(1)
    try:
        return datetime.strptime(s, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def parse_rfc822(teks):
    """'Sun, 23 Aug 2026 20:56:48 +0700' -> datetime WIB (offset dinormalkan)."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(teks)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is not None:
        # normalkan ke WIB (UTC+7), lalu buang tzinfo biar seragam dgn parser lain
        utc = dt.utctimetuple()
        dt = datetime(*utc[:6]) + timedelta(hours=7)
    return dt


def parse_iso(teks):
    """'2026-03-10T21:45:25+07:00' -> datetime WIB tanpa tzinfo."""
    if not teks:
        return None
    try:
        dt = datetime.fromisoformat(teks.strip())
    except ValueError:
        return None
    if dt.tzinfo is not None:
        utc = dt.utctimetuple()
        dt = datetime(*utc[:6]) + timedelta(hours=7)
    return dt
