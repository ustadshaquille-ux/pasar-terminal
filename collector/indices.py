"""Ambil bar harian indeks dari Yahoo Finance (stdlib saja)."""
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from config import INDICES, UA

# range=max diam-diam diturunkan Yahoo jadi bar BULANAN. period1/period2 tetap harian.
BASE = ("https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        "?period1={p1}&period2=9999999999&interval=1d")
MULAI_DEFAULT = 1136073600  # 2006-01-01 UTC


def _get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def ambil(kode, yahoo_sym, p1=MULAI_DEFAULT):
    """Balikin (list_baris, meta). Baris: (kode, 'YYYY-MM-DD', o,h,l,c,v)."""
    raw = _get(BASE.format(sym=urllib.request.quote(yahoo_sym), p1=p1))
    res = json.loads(raw)["chart"]["result"][0]
    meta = res["meta"]
    off = timedelta(seconds=meta.get("gmtoffset", 0))
    ts = res.get("timestamp") or []
    q = res["indicators"]["quote"][0]

    baris = []
    for i, t in enumerate(ts):
        c = q["close"][i]
        if c is None:
            continue  # hari libur / bar bolong: dibuang, bukan diisi 0
        # geser ke waktu bursa lokal dulu, baru ambil tanggalnya
        tgl = (datetime.fromtimestamp(t, timezone.utc) + off).strftime("%Y-%m-%d")
        baris.append((
            kode, tgl,
            q["open"][i], q["high"][i], q["low"][i], c,
            q["volume"][i] if q.get("volume") else None,
        ))
    return baris, meta


def ambil_semua(p1=MULAI_DEFAULT, jeda=1.5):
    hasil, metas = [], {}
    for idx in INDICES:
        baris, meta = ambil(idx["kode"], idx["yahoo"], p1)
        hasil.extend(baris)
        metas[idx["kode"]] = {
            "nama": idx["nama"],
            "tz": meta.get("exchangeTimezoneName"),
            "last": meta.get("regularMarketPrice"),
            "prev": meta.get("chartPreviousClose") or meta.get("previousClose"),
            "bars": len(baris),
            "awal": baris[0][1] if baris else None,
            "akhir": baris[-1][1] if baris else None,
        }
        print(f"  {idx['kode']:7} {len(baris):5} bar  {metas[idx['kode']]['awal']} -> {metas[idx['kode']]['akhir']}")
        time.sleep(jeda)
    return hasil, metas


if __name__ == "__main__":
    import store
    store.init()
    baris, metas = ambil_semua()
    store.simpan_bars(baris)
    print("tersimpan:", len(baris))
