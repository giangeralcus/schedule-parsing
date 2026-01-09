# Schedule Parser v3.2.7

Tool OCR untuk mengubah screenshot jadwal kapal menjadi text yang siap dikirim via email.

Dibuat untuk mempermudah pekerjaan freight forwarding - cukup screenshot jadwal, langsung dapat text formatted.

## Fitur Utama

- **Multi-Carrier** - Support Maersk, CMA CGM, OOCL, dan lainnya
- **GUI & CLI** - Drag-and-drop atau command line
- **Smart OCR** - Tesseract OCR dengan image preprocessing otomatis
- **Database Kapal** - Fuzzy matching untuk koreksi OCR
- **Watch Mode** - Auto-process screenshot baru
- **Copy Otomatis** - Hasil langsung ke clipboard, tinggal paste ke email
- **100% Offline** - Tidak perlu internet

## Cara Pakai

### Persiapan
- Python 3.10+
- Tesseract OCR terinstall

### Instalasi

```bash
# Clone repository
git clone https://github.com/giangeralcus/schedule-parsing.git
cd schedule-parsing

# Install dependencies
pip install -r requirements.txt
```

### Menjalankan

**Mode GUI (Recommended):**
```bash
python schedule_gui.py
```
Drag & drop screenshot → Dapat hasil → Otomatis copy ke clipboard

**Mode CLI:**
```bash
# Menu interaktif
python schedule_parser.py

# Process file langsung
python schedule_parser.py screenshot.png

# Watch folder (auto-process file baru)
python schedule_parser.py --watch

# Input manual
python schedule_parser.py --manual
```

## Contoh Output

```
=== JADWAL KAPAL ===

Opsi 1:
  Kapal  : SPIL NISAKA
  Voyage : 602N
  ETD JKT: 16 Jan 2026 19:00
  ETA SIN: 24 Jan 2026 22:00

Opsi 2:
  Kapal  : SINAR BANDUNG
  Voyage : 603N
  ETD JKT: 23 Jan 2026 19:00
  ETA SIN: 31 Jan 2026 22:00

========================
```

## Carrier yang Didukung

| Carrier | Status | Auto-Detect |
|---------|--------|-------------|
| Maersk | ✅ Full | ✅ |
| CMA CGM | ✅ Full | ✅ |
| OOCL | ✅ Full | ✅ |
| Evergreen | 🟡 Partial | ✅ |
| ONE (Ocean Network Express) | 🟡 Partial | ✅ |
| Hapag-Lloyd | 🔄 Planned | - |
| MSC | 🔄 Planned | - |

## Struktur Folder

```
schedule-parsing/
├── schedule_gui.py       # Aplikasi GUI (drag-and-drop)
├── schedule_parser.py    # Aplikasi CLI (menu interaktif)
├── core/                 # Logic parser
│   ├── parsers.py       # Carrier-specific parsers
│   ├── models.py        # Schedule/ParseResult dataclasses
│   ├── vessel_db.py     # Database vessel (Supabase/offline)
│   └── config.py        # Konfigurasi
├── processors/           # OCR & image processing
│   ├── ocr.py           # Tesseract wrapper
│   └── image.py         # Preprocessing pipeline
├── formatters/           # Format output
│   └── output.py        # Table & email formatter
├── data/                 # Database files
│   └── vessels_cache.json
├── tests/               # Unit tests
├── 1_screenshots/        # Input: taruh screenshot disini
└── 2_hasil/              # Output: hasil parsing
```

## Teknologi

- **Python 3.10+**
- **Tesseract OCR** - Baca text dari gambar
- **OpenCV** - Preprocessing gambar
- **ttkbootstrap** - GUI modern
- **RapidFuzz** - Fuzzy matching nama kapal

## Changelog

Lihat [CHANGELOG.md](CHANGELOG.md) untuk history lengkap.

### Update Terbaru (v3.2.7)
- Dynamic year handling (future-proof untuk 2027+)
- Conservative voyage OCR correction
- Parentheses preservation untuk dates
- Auto-detect carrier dengan konfirmasi
- Parser OOCL lebih akurat
- Security improvements (file size limit, magic bytes validation)

## Author

**Gian Geralcus**
Licensed Customs Broker | Freight Forwarding | Jakarta, Indonesia

[![LinkedIn](https://img.shields.io/badge/LinkedIn-giangeralcus-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/giangeralcus)
[![GitHub](https://img.shields.io/badge/GitHub-giangeralcus-181717?style=flat-square&logo=github)](https://github.com/giangeralcus)

## Lisensi

Personal Project - Untuk penggunaan pribadi dan edukasi.

---

`freight-forwarding` `jadwal-kapal` `shipping` `logistics` `ocr` `python` `indonesia` `customs-broker`
