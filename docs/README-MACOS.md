# Schedule Parser - macOS Setup Guide

Quick setup guide untuk pengguna macOS.

## Requirements

- macOS 10.15+ (Catalina atau lebih baru)
- Python 3.10+
- Tesseract OCR

## Quick Install (5 menit)

### Step 1: Install Tesseract OCR

```bash
# Jika belum punya Homebrew, install dulu:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract
brew install tesseract
```

Atau jalankan script:
```bash
./setup/install_tesseract_mac.sh
```

### Step 2: Install Python Dependencies

```bash
./setup/install_dependencies.sh
```

Atau manual:
```bash
pip install -r requirements.txt
pip install ttkbootstrap  # Optional: untuk dark theme
```

### Step 3: Run!

```bash
# GUI Mode (Recommended)
./scripts/run_gui.sh
# atau
python schedule_gui.py

# CLI Mode
./scripts/run_cli.sh
# atau
python schedule_parser.py
```

## Cara Pakai

1. **Drag & Drop** screenshot schedule ke window GUI
2. Pilih carrier (atau biarkan Auto-detect)
3. Klik **Copy to Clipboard** untuk copy hasil
4. Paste ke email/dokumen

## File Naming Tips

Tambahkan prefix untuk auto-detect carrier:

| Prefix | Carrier |
|--------|---------|
| `m_` | MAERSK |
| `o_` | OOCL |
| `c_` | CMA-CGM |
| `h_` | HAPAG-LLOYD |
| `e_` | EVERGREEN |
| `s_` | MSC |

Contoh: `m_schedule.png` akan otomatis diparse sebagai MAERSK.

## Folder Penting

```
1_screenshots/   <- Taruh screenshot disini
2_hasil/         <- Hasil parsing tersimpan disini
```

## Troubleshooting

### "Tesseract not found"
```bash
# Cek instalasi
which tesseract
tesseract --version

# Jika tidak ada, install ulang
brew install tesseract
```

### "tkinter not found"
```bash
# Install tkinter via Homebrew
brew install python-tk
```

### GUI tidak muncul
- Cek Dock, mungkin window minimize
- Gunakan `Cmd+Tab` untuk switch window
- Coba run dari Terminal langsung: `python schedule_gui.py`

### Permission denied saat run script
```bash
chmod +x scripts/*.sh setup/*.sh
```

## Support

Issues? Buka issue di GitHub repository.
