# Schedule Parser v3.0

Tool buat extract jadwal kapal dari screenshot - offline, pake OCR.

> **⚠️ Masih Development**
> Project ini masih dikembangin. Fitur bisa berubah kapan aja.

## About

**Author:** Gian Geralcus
**Created:** 06 January 2026
**Type:** Personal Project
**Status:** 🚧 Development

---

## Kenapa Bikin Ini?

Biar kerjaan ngurus schedule kapal lebih gampang - yang **delay**, **non-delay**, atau **conjunction**.

### Masalahnya Apa?

Tiap hari kita harus:
1. Terima screenshot schedule dari shipping line
2. Ketik ulang manual data vessel, voyage, ETD, ETA
3. Cek lagi biar ga typo

Capek kan? Makan waktu lagi. **Schedule Parser** otomatisin ini semua.

### Bedanya Gimana?

| Sebelum | Sesudah |
|---------|---------|
| Ketik manual dari screenshot | Drag & drop, auto extract |
| Sering typo | OCR + validasi otomatis |
| 5-10 menit per schedule | < 30 detik aja |
| Copy satu-satu | Copy semua sekaligus |

> *"Small improvements compound over time"*
> Yang keliatan kecil tiap hari, lama-lama ngaruh gede.

---

## Cara Kerja

```
Screenshot  →  OCR Extract  →  Parse Data  →  Format  →  Copy/Save
  (input)      (Tesseract)    (by carrier)   (email)    (clipboard)
```

### Carrier yang Support

| Carrier | Auto-detect | Prefix File |
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

**Tips:** Rename file pake prefix biar auto-detect.
Contoh: `m_schedule_jan.png` → ke-detect sebagai MAERSK.

### Output-nya

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

Tinggal copy, paste ke email. Beres.

---

## Fitur

- **Drag & Drop** - Tinggal drag screenshot ke window
- **11 Shipping Lines** - Maersk, CMA, OOCL, dll
- **Auto-Detect Carrier** - Dari nama file atau isi screenshot
- **OCR** - Pake Tesseract, ada preprocessing juga
- **Smart Validation** - Kalo ETD/ETA kebalik, auto-swap
- **Copy to Clipboard** - Langsung copy hasil
- **Organized** - Hasil ke-save per folder carrier

---

## Folder

```
1_screenshots/   ← Taruh screenshot disini
2_hasil/         ← Hasil parsing kesimpen disini
```

---

## Install & Cara Pake

Cek guide lengkap:

- **[Installation Guide](docs/INSTALLATION.md)** - Setup lengkap
- **[macOS Guide](docs/README-MACOS.md)** - Buat Mac user
- **[Windows Guide](docs/README-WINDOWS.md)** - Buat Windows user

**Quick Start:**
```bash
python schedule_gui.py
```

---

## License

**Personal Project - Gian Geralcus**

Project pribadi, hak cipta Gian Geralcus. Ga boleh copy/modif/distribute tanpa izin.
