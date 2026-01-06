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

## Tujuan

Bikin kerjaan ngurus schedule kapal jadi lebih **cepat** dan **efisien** - yang **delay**, **non-delay**, atau **conjunction**.

### Problem

Tiap hari kita harus:
1. Terima screenshot schedule dari shipping line
2. Ketik ulang manual data vessel, voyage, ETD, ETA
3. Cek lagi biar ga typo

Makan waktu. Capek. Rawan salah.

### Solution

**Schedule Parser** otomatisin semuanya. Drag screenshot → dapet data. Done.

| Sebelum | Sesudah |
|---------|---------|
| Ketik manual | Auto extract |
| Sering typo | OCR + validasi |
| 5-10 menit | < 30 detik |
| Copy satu-satu | Copy semua |

---

## Business Use Case

Tool ini cocok buat:

- **Freight Forwarder** - Cepet dapet info schedule buat customer
- **Shipping Ops** - Update jadwal kapal tanpa ketik manual
- **Customer Service** - Quick response buat inquiry schedule
- **Documentation** - Data vessel/voyage langsung ready

### Workflow Integration

```
Email masuk (screenshot)
       ↓
  Schedule Parser
       ↓
  Copy to clipboard
       ↓
  Paste ke system/email
       ↓
     Done ✓
```

Hemat waktu = hemat cost = kerja lebih produktif.

---

## Supported Carriers

| Carrier | Auto-detect | Prefix |
|---------|-------------|--------|
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

---

## Output

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

Copy → Paste ke email → Beres.

---

## Fitur

- **Drag & Drop** - Tinggal drag screenshot
- **11 Shipping Lines** - Major carriers supported
- **Auto-Detect** - Carrier ke-detect otomatis
- **OCR** - Tesseract + preprocessing
- **Smart Validation** - ETD/ETA auto-swap kalo kebalik
- **Clipboard** - Langsung copy hasil

---

## Documentation

- **[Installation & Cara Pake](docs/INSTALLATION.md)**
- **[macOS Guide](docs/README-MACOS.md)**
- **[Windows Guide](docs/README-WINDOWS.md)**

---

## License

**Personal Project - Gian Geralcus**

For personal project & hobbies use only.
