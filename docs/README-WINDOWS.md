# Schedule Parser - Windows Setup Guide

Quick setup guide untuk pengguna Windows.

## Requirements

- Windows 10/11
- Python 3.10+
- Tesseract OCR

## Quick Install (10 menit)

### Step 1: Install Python

1. Download Python dari [python.org](https://www.python.org/downloads/)
2. Saat install, **centang "Add Python to PATH"**
3. Klik Install

Verifikasi:
```cmd
python --version
```

### Step 2: Install Tesseract OCR

1. Download dari [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Pilih file `tesseract-ocr-w64-setup-xxx.exe`
3. Install ke `C:\Program Files\Tesseract-OCR\`

Atau jalankan script:
```cmd
setup\install_tesseract.bat
```

### Step 3: Install Python Dependencies

```cmd
pip install -r requirements.txt
pip install ttkbootstrap
```

### Step 4: Run!

```cmd
:: GUI Mode (Recommended)
scripts\run_gui.bat
:: atau
python schedule_gui.py

:: CLI Mode
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
1_screenshots\   <- Taruh screenshot disini
2_hasil\         <- Hasil parsing tersimpan disini
```

## Build Standalone EXE

Untuk membuat file .exe yang bisa dijalankan tanpa install Python:

```cmd
setup\build_exe.bat
```

Hasil: `dist\ScheduleParser.exe`

## Troubleshooting

### "Tesseract not found" atau "TesseractNotFoundError"

1. Pastikan Tesseract terinstall di `C:\Program Files\Tesseract-OCR\`
2. Atau tambahkan ke PATH:
   - Buka System Properties > Environment Variables
   - Edit PATH, tambahkan `C:\Program Files\Tesseract-OCR\`
   - Restart Command Prompt

### "Python not found"

1. Reinstall Python, pastikan centang "Add to PATH"
2. Atau tambahkan manual ke PATH

### "pip not recognized"

```cmd
python -m pip install -r requirements.txt
```

### GUI tidak muncul / crash

1. Pastikan semua dependencies terinstall:
   ```cmd
   pip install pytesseract pillow opencv-python pyperclip tkinterdnd2 numpy
   ```
2. Coba tanpa ttkbootstrap:
   ```cmd
   pip uninstall ttkbootstrap
   python schedule_gui.py
   ```

### Drag & Drop tidak bekerja

- Jalankan sebagai Administrator
- Atau gunakan tombol "Browse File"

## Support

Issues? Buka issue di GitHub repository.
