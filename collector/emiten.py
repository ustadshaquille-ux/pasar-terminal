"""Deteksi emiten dari judul berita: mana berita yang soal SATU saham.

Ini yang memisahkan berita MIKRO (satu emiten) dari MAKRO (IHSG, rupiah, Fed,
komoditas). Dua-duanya penting, tapi kalau dicampur di satu daftar, berita
"BNI Raih Penghargaan" berdesakan dengan "BI Tahan Suku Bunga" dan tidak ada
yang terbaca.

Tiga jalur deteksi, dari yang paling pasti ke yang paling longgar:

1. Kode dalam kurung -- "Adhi Karya (ADHI)". Nyaris selalu benar, dan sekalian
   dipakai buat MEMPELAJARI nama emiten: teks sebelum kurung adalah namanya.
   Dari situ daftar emiten tumbuh sendiri tanpa perlu diketik satu-satu.
2. Kode berdiri sendiri -- "Saham BBRI Diborong Asing". Hanya diterima kalau
   kodenya sudah dikenal (kurasi atau hasil belajar). Tanpa syarat itu, IHSG,
   BUMN, UMKM, APBN, QRIS, dan puluhan akronim lain ikut terbaca sebagai
   emiten -- di arsip ini IHSG saja muncul 237 kali, BUMN 117 kali.
3. Nama perusahaan -- "Bank Mandiri", "Astra". Mayoritas judul Indonesia
   menyebut nama, bukan kode, jadi tanpa jalur ini sebagian besar berita
   emiten lolos tak terdeteksi.

Alias sengaja panjang-panjang. "mandiri" saja salah: itu kata sifat biasa
("koperasi mandiri"), jadi yang dipakai "bank mandiri". "bri" harus dibatasi
kata utuh, kalau tidak "BRIN" (badan riset) ikut terbaca.
"""
import re

# kode -> (nama tampil, sektor, [alias tambahan])
# Alias ditulis huruf kecil; pencocokannya sebagai kata utuh.
EMITEN = {
    # --- perbankan ---
    "BBCA": ("Bank Central Asia", "bank", ["bca", "bank central asia"]),
    "BBRI": ("Bank Rakyat Indonesia", "bank", ["bri", "bank rakyat indonesia", "brimo"]),
    "BMRI": ("Bank Mandiri", "bank", ["bank mandiri", "livin"]),
    "BBNI": ("Bank Negara Indonesia", "bank", ["bni", "bank negara indonesia", "wondr"]),
    "BBTN": ("Bank Tabungan Negara", "bank", ["btn", "bank tabungan negara"]),
    "BRIS": ("Bank Syariah Indonesia", "bank", ["bsi", "bank syariah indonesia"]),
    "BNGA": ("CIMB Niaga", "bank", ["cimb niaga"]),
    "BDMN": ("Bank Danamon", "bank", ["danamon"]),
    "NISP": ("OCBC Indonesia", "bank", ["ocbc nisp", "bank ocbc"]),
    "BNLI": ("Bank Permata", "bank", ["bank permata"]),
    "PNBN": ("Bank Panin", "bank", ["bank panin"]),
    "BNII": ("Maybank Indonesia", "bank", ["maybank indonesia"]),
    "MEGA": ("Bank Mega", "bank", ["bank mega"]),
    "BTPN": ("SMBC Indonesia", "bank", ["btpn", "smbc indonesia"]),
    "ARTO": ("Bank Jago", "bank", ["bank jago"]),
    "BBHI": ("Allo Bank", "bank", ["allo bank"]),
    "BBYB": ("Bank Neo Commerce", "bank", ["bank neo commerce"]),
    "AMAR": ("Amar Bank", "bank", ["amar bank"]),
    "AGRO": ("Bank Raya", "bank", ["bank raya"]),
    "BJBR": ("Bank BJB", "bank", ["bank bjb", "bank jabar banten"]),
    "BJTM": ("Bank Jatim", "bank", ["bank jatim"]),
    "BVIC": ("Bank Victoria", "bank", ["bank victoria"]),
    "BANK": ("Bank Aladin", "bank", ["bank aladin", "aladin syariah"]),

    # --- finansial non-bank ---
    "BFIN": ("BFI Finance", "finansial", ["bfi finance"]),
    "ADMF": ("Adira Finance", "finansial", ["adira finance"]),
    "PNLF": ("Panin Financial", "finansial", []),
    "TUGU": ("Asuransi Tugu", "finansial", ["tugu insurance"]),
    "ASRM": ("Asuransi Ramayana", "finansial", []),
    "PANS": ("Panin Sekuritas", "finansial", []),
    "TRIM": ("Trimegah Sekuritas", "finansial", ["trimegah sekuritas"]),

    # --- energi & tambang ---
    "ADRO": ("Alamtri Resources", "tambang", ["adaro", "alamtri"]),
    "AADI": ("Adaro Andalan", "tambang", ["adaro andalan"]),
    "PTBA": ("Bukit Asam", "tambang", ["bukit asam"]),
    "ITMG": ("Indo Tambangraya", "tambang", ["indo tambangraya", "banpu"]),
    "HRUM": ("Harum Energy", "tambang", ["harum energy"]),
    "INDY": ("Indika Energy", "tambang", ["indika energy"]),
    "BUMI": ("Bumi Resources", "tambang", ["bumi resources"]),
    "BYAN": ("Bayan Resources", "tambang", ["bayan resources"]),
    "GEMS": ("Golden Energy Mines", "tambang", ["golden energy mines"]),
    "DSSA": ("Dian Swastatika", "tambang", ["dian swastatika"]),
    "DOID": ("Delta Dunia", "tambang", ["delta dunia"]),
    "PTRO": ("Petrosea", "tambang", ["petrosea"]),
    "ABMM": ("ABM Investama", "tambang", ["abm investama"]),
    "ANTM": ("Aneka Tambang", "tambang", ["antam", "aneka tambang"]),
    "INCO": ("Vale Indonesia", "tambang", ["vale indonesia"]),
    "TINS": ("Timah", "tambang", ["pt timah"]),
    "MDKA": ("Merdeka Copper Gold", "tambang", ["merdeka copper"]),
    "MBMA": ("Merdeka Battery", "tambang", ["merdeka battery"]),
    "NCKL": ("Trimegah Bangun Persada", "tambang", ["harita nickel", "trimegah bangun persada"]),
    "BRMS": ("Bumi Resources Minerals", "tambang", ["bumi resources minerals"]),
    "PSAB": ("J Resources", "tambang", ["j resources"]),
    "AMMN": ("Amman Mineral", "tambang", ["amman mineral", "amman"]),
    "HRTA": ("Hartadinata Abadi", "tambang", ["hartadinata"]),
    "MEDC": ("Medco Energi", "energi", ["medco"]),
    "PGAS": ("PGN", "energi", ["perusahaan gas negara", "pgn"]),
    "PGEO": ("Pertamina Geothermal", "energi", ["pertamina geothermal"]),
    "ELSA": ("Elnusa", "energi", ["elnusa"]),
    "AKRA": ("AKR Corporindo", "energi", ["akr corporindo"]),
    "RAJA": ("Rukun Raharja", "energi", ["rukun raharja"]),
    "ESSA": ("ESSA Industries", "energi", ["essa industries"]),
    "CUAN": ("Petrindo Jaya Kreasi", "energi", ["petrindo"]),
    "BREN": ("Barito Renewables", "energi", ["barito renewables"]),
    "KEEN": ("Kencana Energi", "energi", ["kencana energi"]),

    # --- industri dasar & kimia ---
    "BRPT": ("Barito Pacific", "industri", ["barito pacific"]),
    "TPIA": ("Chandra Asri", "industri", ["chandra asri"]),
    "CDIA": ("Chandra Daya Investasi", "industri", ["chandra daya"]),
    "KRAS": ("Krakatau Steel", "industri", ["krakatau steel"]),
    "SMGR": ("Semen Indonesia", "industri", ["semen indonesia", "semen gresik"]),
    "INTP": ("Indocement", "industri", ["indocement"]),
    "SMCB": ("Solusi Bangun Indonesia", "industri", ["solusi bangun"]),
    "SMBR": ("Semen Baturaja", "industri", ["semen baturaja"]),
    "ARNA": ("Arwana Citramulia", "industri", ["arwana citramulia"]),
    "AVIA": ("Avia Avian", "industri", ["avia avian", "cat avian"]),
    "ISSP": ("Steel Pipe Industry", "industri", ["spindo"]),
    "TKIM": ("Pabrik Kertas Tjiwi Kimia", "industri", ["tjiwi kimia"]),
    "INKP": ("Indah Kiat", "industri", ["indah kiat"]),

    # --- agri & sawit ---
    "AALI": ("Astra Agro Lestari", "agri", ["astra agro"]),
    "LSIP": ("London Sumatra", "agri", ["london sumatra", "lonsum"]),
    "SIMP": ("Salim Ivomas", "agri", ["salim ivomas"]),
    "TAPG": ("Triputra Agro Persada", "agri", ["triputra agro"]),
    "DSNG": ("Dharma Satya Nusantara", "agri", ["dharma satya"]),
    "SSMS": ("Sawit Sumbermas", "agri", ["sawit sumbermas"]),
    "SGRO": ("Sampoerna Agro", "agri", ["sampoerna agro"]),
    "BWPT": ("Eagle High Plantations", "agri", ["eagle high"]),
    "TBLA": ("Tunas Baru Lampung", "agri", ["tunas baru lampung"]),
    "SMAR": ("Sinar Mas Agro", "agri", ["sinar mas agro", "smart tbk"]),

    # --- konsumer ---
    "ICBP": ("Indofood CBP", "konsumer", ["indofood cbp"]),
    "INDF": ("Indofood Sukses Makmur", "konsumer", ["indofood sukses"]),
    "UNVR": ("Unilever Indonesia", "konsumer", ["unilever"]),
    "MYOR": ("Mayora Indah", "konsumer", ["mayora"]),
    "KLBF": ("Kalbe Farma", "kesehatan", ["kalbe farma", "kalbe"]),
    "SIDO": ("Sido Muncul", "kesehatan", ["sido muncul"]),
    "HMSP": ("HM Sampoerna", "konsumer", ["hm sampoerna", "sampoerna tbk"]),
    "GGRM": ("Gudang Garam", "konsumer", ["gudang garam"]),
    "WIIM": ("Wismilak", "konsumer", ["wismilak"]),
    "CPIN": ("Charoen Pokphand", "konsumer", ["charoen pokphand"]),
    "JPFA": ("Japfa Comfeed", "konsumer", ["japfa"]),
    "MAIN": ("Malindo Feedmill", "konsumer", ["malindo feedmill"]),
    "ROTI": ("Nippon Indosari", "konsumer", ["sari roti", "nippon indosari"]),
    "ULTJ": ("Ultrajaya", "konsumer", ["ultrajaya"]),
    "CMRY": ("Cisarua Mountain Dairy", "konsumer", ["cimory"]),
    "GOOD": ("Garudafood", "konsumer", ["garudafood"]),
    "ADES": ("Akasha Wira", "konsumer", ["akasha wira"]),
    "CLEO": ("Sariguna Primatirta", "konsumer", ["cleo"]),
    "FORE": ("Fore Kopi Indonesia", "konsumer", ["fore coffee"]),
    "YUPI": ("Yupi Indo Jelly Gum", "konsumer", ["yupi indo"]),

    # --- kesehatan ---
    "MIKA": ("Mitra Keluarga", "kesehatan", ["mitra keluarga"]),
    "SILO": ("Siloam Hospitals", "kesehatan", ["siloam"]),
    "HEAL": ("Medikaloka Hermina", "kesehatan", ["hermina"]),
    "PRDA": ("Prodia Widyahusada", "kesehatan", ["prodia"]),
    "KAEF": ("Kimia Farma", "kesehatan", ["kimia farma"]),
    "INAF": ("Indofarma", "kesehatan", ["indofarma"]),
    "TSPC": ("Tempo Scan Pacific", "kesehatan", ["tempo scan"]),

    # --- telko, media, teknologi ---
    "TLKM": ("Telkom Indonesia", "telko", ["telkom indonesia", "telkomsel", "pt telkom"]),
    "EXCL": ("XLSmart Telecom", "telko", ["xl axiata", "xlsmart"]),
    "ISAT": ("Indosat Ooredoo Hutchison", "telko", ["indosat"]),
    "MTEL": ("Dayamitra Telekomunikasi", "telko", ["mitratel"]),
    "TBIG": ("Tower Bersama", "telko", ["tower bersama"]),
    "TOWR": ("Sarana Menara Nusantara", "telko", ["sarana menara", "protelindo"]),
    "GOTO": ("GoTo Gojek Tokopedia", "teknologi", ["gojek", "tokopedia", "goto"]),
    "BUKA": ("Bukalapak", "teknologi", ["bukalapak"]),
    "BELI": ("Global Digital Niaga", "teknologi", ["blibli"]),
    "EMTK": ("Elang Mahkota Teknologi", "media", ["emtek"]),
    "SCMA": ("Surya Citra Media", "media", ["surya citra", "sctv"]),
    "MNCN": ("Media Nusantara Citra", "media", ["media nusantara citra"]),
    "DNET": ("Indoritel Makmur", "teknologi", ["indoritel"]),
    "MSTI": ("Metrodata Electronics", "teknologi", ["metrodata"]),
    "WIFI": ("Solusi Sinergi Digital", "teknologi", ["surge", "solusi sinergi digital"]),

    # --- properti & konstruksi ---
    "BSDE": ("Bumi Serpong Damai", "properti", ["bumi serpong damai", "bsd city"]),
    "CTRA": ("Ciputra Development", "properti", ["ciputra development"]),
    "SMRA": ("Summarecon Agung", "properti", ["summarecon"]),
    "PWON": ("Pakuwon Jati", "properti", ["pakuwon"]),
    "LPKR": ("Lippo Karawaci", "properti", ["lippo karawaci"]),
    "ASRI": ("Alam Sutera Realty", "properti", ["alam sutera"]),
    "DMAS": ("Puradelta Lestari", "properti", ["puradelta"]),
    "MTLA": ("Metropolitan Land", "properti", ["metropolitan land"]),
    "PANI": ("Pantai Indah Kapuk Dua", "properti", ["pantai indah kapuk", "pik 2", "pik2"]),
    "CBDK": ("Bangun Kosambi Sukses", "properti", ["bangun kosambi"]),
    "WIKA": ("Wijaya Karya", "konstruksi", ["wijaya karya"]),
    "WSKT": ("Waskita Karya", "konstruksi", ["waskita karya"]),
    "PTPP": ("PP (Persero)", "konstruksi", ["pt pp", "pp persero"]),
    "ADHI": ("Adhi Karya", "konstruksi", ["adhi karya"]),
    "JSMR": ("Jasa Marga", "infrastruktur", ["jasa marga"]),
    "TOTL": ("Total Bangun Persada", "konstruksi", ["total bangun persada"]),

    # --- ritel & distribusi ---
    "MAPI": ("Mitra Adiperkasa", "ritel", ["mitra adiperkasa"]),
    "MAPA": ("MAP Aktif Adiperkasa", "ritel", ["map aktif"]),
    "ACES": ("Aspirasi Hidup Indonesia", "ritel", ["ace hardware", "aspirasi hidup"]),
    "AMRT": ("Sumber Alfaria Trijaya", "ritel", ["alfamart", "sumber alfaria"]),
    "MIDI": ("Midi Utama Indonesia", "ritel", ["alfamidi", "midi utama"]),
    "RALS": ("Ramayana Lestari", "ritel", ["ramayana lestari"]),
    "LPPF": ("Matahari Department Store", "ritel", ["matahari department"]),
    "ERAA": ("Erajaya Swasembada", "ritel", ["erajaya"]),
    "CSAP": ("Catur Sentosa Adiprana", "ritel", ["catur sentosa"]),

    # --- transportasi & aneka ---
    "ASII": ("Astra International", "otomotif", ["astra international", "grup astra"]),
    "AUTO": ("Astra Otoparts", "otomotif", ["astra otoparts"]),
    "UNTR": ("United Tractors", "alat berat", ["united tractors"]),
    "HEXA": ("Hexindo Adiperkasa", "alat berat", ["hexindo"]),
    "IMAS": ("Indomobil Sukses", "otomotif", ["indomobil"]),
    "GJTL": ("Gajah Tunggal", "otomotif", ["gajah tunggal"]),
    "GIAA": ("Garuda Indonesia", "transportasi", ["garuda indonesia"]),
    "CMPP": ("AirAsia Indonesia", "transportasi", ["airasia indonesia", "indonesia airasia"]),
    "TMAS": ("Temas", "transportasi", ["temas line"]),
    "SMDR": ("Samudera Indonesia", "transportasi", ["samudera indonesia"]),
    "ASSA": ("Adi Sarana Armada", "transportasi", ["adi sarana armada", "anteraja"]),
    "BIRD": ("Blue Bird", "transportasi", ["blue bird"]),
    "IPCC": ("Indonesia Kendaraan Terminal", "transportasi", ["indonesia kendaraan terminal"]),
    "IPCM": ("Jasa Armada Indonesia", "transportasi", ["jasa armada"]),
    "SRTG": ("Saratoga Investama", "investasi", ["saratoga"]),
    "BNBR": ("Bakrie & Brothers", "investasi", ["bakrie & brothers"]),
    "DEWA": ("Darma Henwa", "tambang", ["darma henwa"]),
}

# Kode yang boleh dipelajari sendiri tapi jangan pernah ditebak dari singkatan
# huruf besar biasa. Daftar ini yang membuat jalur "kode berdiri sendiri" aman.
BUKAN_KODE = {
    "IHSG", "BUMN", "UMKM", "APBN", "APBD", "MSCI", "FTSE", "OPEC", "NATO",
    "ESDM", "BPJS", "QRIS", "SPBU", "PLTS", "PLTU", "PLTA", "PLTP", "PLTB",
    "PPPK", "CPNS", "KSSK", "ASDP", "RKAB", "RUPS", "SPHP", "ODOL", "PSEL",
    "KPPU", "CEPA", "PTPN", "PTDI", "BRIN", "LPDB", "FOMO", "CIMB", "KSEI",
    "BKPM", "AIIB", "BPKB", "FIFA", "IKEA", "BPOM", "LPEI", "PCPM", "NMAX",
    "FLPP", "BPKP", "TJSL", "KKKS", "HSSE", "SPPG", "RANS", "PFII", "IBMA",
    "DANA", "VISI", "SINI", "JELI", "DOKU", "VIVO", "SMBC", "BPKH", "INKA",
    "OSES", "BACH", "PSBI", "SLHS", "IIES", "PRDL", "IPO", "OJK", "BEI",
    "IDX", "LQ45", "BBM", "MBG", "IKN", "WIB", "WITA", "PHK", "PPN", "PPH",
    "THR", "BLT", "KUR", "KPR", "PDB", "GDP", "ETF", "REIT", "FOMC", "ECB",
    "PBOC", "BOJ", "IMF", "OECD", "ASEAN", "APEC", "BRICS", "WTO", "AS",
    "COVID", "AI", "EBITDA", "IPOT", "SUKUK", "SBN", "SUN", "DHE", "MSIG",
    "OCBC", "BTPS", "GRAB", "SEA", "TIKTOK", "ARB", "ARA", "SPAC", "ESG",
    "SDGS", "PMI", "CAD", "DXY", "WTI", "CPO", "LNG", "LPG", "PLN", "KAI",
    "MRT", "LRT", "KRL", "TNI", "POLRI", "KPK", "MPR", "DPR", "MK", "BPS",
    "KADIN", "APINDO", "HIPMI", "SOHO", "NASA", "OTOMOTIF", "SIM", "STNK",
}

# alias -> kode; dibangun sekali, dicocokkan sebagai kata utuh
_ALIAS = {}
for _k, (_n, _s, _al) in EMITEN.items():
    for _a in _al:
        _ALIAS.setdefault(_a, _k)

# alias terpanjang dulu supaya "bank rakyat indonesia" menang atas "bri"
_ALIAS_URUT = sorted(_ALIAS, key=len, reverse=True)
_RE_ALIAS = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(a) for a in _ALIAS_URUT)
                       + r")(?![a-z0-9])")

_RE_KURUNG = re.compile(r"\(([A-Z]{4})\)")
_RE_EKSPLISIT = re.compile(r"\b(?:saham|emiten|kode)\s+([A-Z]{4})\b")
_RE_CAPS = re.compile(r"\b([A-Z]{4})\b")
# "Adhi Karya (ADHI)" -> nama diambil dari kata-kata berhuruf besar tepat
# sebelum kurung. Ini yang bikin daftar emiten tumbuh sendiri.
_RE_BELAJAR = re.compile(
    r"((?:[A-Z][A-Za-z&.'-]*\s+){0,4}[A-Z][A-Za-z&.'-]*)\s*\(([A-Z]{4})\)")

AWALAN_NAMA = re.compile(r"^(pt|tbk|saham|emiten|milik|induk|anak usaha|grup|group)\s+",
                         re.I)

# Nama emiten yang juga dipakai sebagai nama PRODUK. "Harga Emas Antam Hari Ini
# Naik Rp 20.000" itu berita komoditas, bukan berita saham ANTM -- dan di arsip
# ini pola tersebut muncul 83 kali, cukup untuk menenggelamkan seluruh panel
# emiten kalau dibiarkan.
PENGECUALIAN = {
    "ANTM": re.compile(r"harga emas|emas antam|logam mulia|emas batangan|buyback emas"),
    "BBRI": re.compile(r"\bbri\s?liga\b|bri liga"),
}


def belajar(judul):
    """Pasangan (kode, nama) yang bisa dipetik dari pola 'Nama Panjang (KODE)'."""
    out = []
    for nama, kode in _RE_BELAJAR.findall(judul):
        nama = AWALAN_NAMA.sub("", nama.strip()).strip(" .,-")
        if kode in BUKAN_KODE or len(nama) < 3:
            continue
        out.append((kode, nama))
    return out


def deteksi(judul, dikenal=None):
    """Kode emiten yang disebut judul ini. Urut sesuai kemunculan, tanpa duplikat.

    `dikenal` = himpunan kode yang sudah dipercaya (kurasi + hasil belajar).
    Kode berdiri sendiri hanya diterima kalau ada di situ; tanpa syarat itu
    setiap akronim empat huruf jadi "emiten".
    """
    if dikenal is None:
        dikenal = set(EMITEN)
    hasil, dari_kode = [], set()

    def tambah(k, kode_tertulis):
        if not k or k in BUKAN_KODE:
            return
        if k not in hasil:
            hasil.append(k)
        if kode_tertulis:
            dari_kode.add(k)

    for k in _RE_KURUNG.findall(judul):
        tambah(k, True)
    for k in _RE_EKSPLISIT.findall(judul):
        tambah(k, True)
    for k in _RE_CAPS.findall(judul):
        if k in dikenal:
            tambah(k, True)
    for a in _RE_ALIAS.findall(judul.lower()):
        tambah(_ALIAS[a], False)

    # Pengecualian hanya berlaku untuk temuan lewat NAMA. Kalau kodenya
    # tertulis ("Saham ANTM Melesat Ikuti Harga Emas"), itu memang berita
    # sahamnya, dan penyaring produk tidak boleh membuangnya.
    t = judul.lower()
    return [k for k in hasil
            if k in dari_kode or not (k in PENGECUALIAN and PENGECUALIAN[k].search(t))]


def nama(kode, belajaran=None):
    if kode in EMITEN:
        return EMITEN[kode][0]
    if belajaran and kode in belajaran:
        return belajaran[kode]
    return kode


def sektor(kode):
    return EMITEN[kode][1] if kode in EMITEN else "lainnya"
