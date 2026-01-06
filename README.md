# Schedule Parser v3.0

Offline shipping schedule parser with OCR - extract vessel schedules from screenshots.

## About

**Author:** Gian Geralcus
**Created:** 06 January 2026
**Project Type:** Personal Project

---

## Tujuan / Purpose

Memudahkan small performance workflow yang dapat memiliki efek jangka panjang dalam pengurusan scheduling kapal - baik yang **delay**, **non-delay**, maupun **conjunction**.

### Mengapa Tool Ini Dibuat?

Dalam pekerjaan sehari-hari mengelola jadwal kapal, sering kali kita harus:
1. Menerima screenshot schedule dari berbagai shipping line
2. Manually ketik ulang data vessel, voyage, ETD, ETA ke sistem
3. Double-check untuk menghindari typo

Proses ini memakan waktu dan rentan kesalahan. **Schedule Parser** mengotomatisasi proses ini.

### Manfaat

| Sebelum | Sesudah |
|---------|---------|
| Manual ketik dari screenshot | Drag & drop, otomatis extract |
| Rentan typo | OCR + validation |
| 5-10 menit per schedule | < 30 detik per schedule |
| Copy-paste satu per satu | Copy semua sekaligus |

> *"Small efficiency improvements compound over time"*
> Apa yang terlihat seperti penghematan kecil setiap hari, akan memberikan dampak signifikan dalam jangka panjang.

---

## Workflow

### Cara Kerja

```
Screenshot Schedule  →  OCR Extract  →  Parse Data  →  Format Output  →  Copy/Save
     (input)            (Tesseract)     (by carrier)    (table/email)    (clipboard)
```

### Supported Carriers

| Carrier | Auto-detect | File Prefix |
|---------|-------------|-------------|
| MAERSK | ✅ | `m_` |
| OOCL | ✅ | `o_` |
| CMA-CGM | ✅ | `c_` |
| HAPAG-LLOYD | ✅ | `h_` |
| EVERGREEN | ✅ | `e_` |
| ONE | ✅ | `n_` |
| YANG-MING | ✅ | `y_` |
| MSC | ✅ | `s_` |
| ZIM | ✅ | `z_` |
| WAN-HAI | ✅ | `w_` |
| PIL | ✅ | `p_` |

**Tip:** Rename file dengan prefix untuk auto-detect carrier.
Contoh: `m_schedule_jan.png` → otomatis diparse sebagai MAERSK.

### Output Format

```
Carrier: MAERSK
----------------------------------------
Option 1:
  Vessel  : SPIL NISAKA
  Voyage  : 602N
  ETD     : 16 Jan 2026, 19:00
  ETA     : 24 Jan 2026, 22:00

Option 2:
  Vessel  : JULIUS-S.
  Voyage  : 603N
  ETD     : 15 Jan 2026, 10:00
  ETA     : 18 Jan 2026, 23:00
```

Output bisa langsung di-copy ke clipboard dan paste ke email.

---

## Features

- **Drag & Drop GUI** - Modern dark theme interface, tinggal drag screenshot
- **Multi-Carrier Support** - 11 shipping lines supported
- **Auto-Detection** - Otomatis detect carrier dari filename atau content
- **OCR Powered** - Tesseract OCR dengan image preprocessing
- **Smart Validation** - Auto-swap ETD/ETA jika terbalik
- **Multiple Output** - Table view, email format, clipboard copy
- **Organized Output** - Hasil tersimpan di folder per carrier

---

## Folder Input/Output

```
1_screenshots/   ← Taruh screenshot disini
2_hasil/         ← Hasil parsing tersimpan disini (per carrier)
```

---

## Installation & Usage

Untuk panduan instalasi lengkap, lihat:

- **[Installation Guide](docs/INSTALLATION.md)** - Setup lengkap
- **[macOS Guide](docs/README-MACOS.md)** - Khusus pengguna Mac
- **[Windows Guide](docs/README-WINDOWS.md)** - Khusus pengguna Windows

**Quick Start:**
```bash
python schedule_gui.py
```

---

## License

**Personal Project - Gian Geralcus**

This project is a personal project created by Gian Geralcus. All rights reserved.
Unauthorized copying, modification, or distribution is not permitted without explicit permission from the author.
