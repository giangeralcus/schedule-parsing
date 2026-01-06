# Installation & Cara Pake

Guide lengkap buat install dan pake Schedule Parser v3.0.

---

## Cara Pake (Quick Start)

### GUI Mode (Recommended)

1. **Run aplikasi:**
   ```bash
   python schedule_gui.py
   ```

2. **Drag & drop** screenshot schedule ke window

3. **Hasil otomatis muncul** - vessel, voyage, ETD, ETA

4. **Klik "Copy to Clipboard"** → paste ke email/system

### Tips

- Rename file pake prefix biar auto-detect carrier: `m_screenshot.png` = MAERSK
- Kalo hasil kurang akurat, coba screenshot yang lebih clear
- Output ke-save otomatis di folder `2_hasil/`

### Folder

```
1_screenshots/   ← Taruh screenshot disini
2_hasil/         ← Hasil parsing kesimpen disini
```

---

## Installation

## Platform-Specific Guides

- **[macOS Setup Guide](README-MACOS.md)** - Detailed guide untuk Mac users
- **[Windows Setup Guide](README-WINDOWS.md)** - Detailed guide untuk Windows users

## Prerequisites

1. **Python 3.10+**
2. **Tesseract OCR**

## Quick Setup

### macOS/Linux

```bash
# 1. Install Tesseract OCR
./setup/install_tesseract_mac.sh
# atau: brew install tesseract

# 2. Install Python dependencies
./setup/install_dependencies.sh
```

### Windows

```cmd
:: 1. Install Tesseract OCR
:: Download dari: https://github.com/UB-Mannheim/tesseract/wiki
:: Install ke: C:\Program Files\Tesseract-OCR\

:: 2. Install Python dependencies
pip install -r requirements.txt
```

## Manual Installation

### Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Windows:**
- Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Install to `C:\Program Files\Tesseract-OCR\`

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `pytesseract` - OCR engine interface
- `pillow` - Image processing
- `opencv-python` - Advanced image preprocessing
- `pyperclip` - Clipboard support
- `tkinterdnd2` - Drag & drop support
- `numpy` - Numerical operations

### Optional: Modern UI Theme

```bash
pip install ttkbootstrap
```

## Running the Application

### GUI Mode (Recommended)

```bash
# Direct
python schedule_gui.py

# macOS/Linux
./scripts/run_gui.sh

# Windows
scripts\run_gui.bat
```

### CLI Mode

```bash
# Direct
python schedule_parser.py

# macOS/Linux
./scripts/run_cli.sh
```

**CLI Options:**
- `[A]ll` - Process all screenshots
- `[1-9]` - Process specific file
- `[E]dit` - Manual text editing mode
- `[W]atch` - Auto-process new files
- `[M]anual` - Manual entry mode

## Build Standalone EXE (Windows)

```cmd
setup\build_exe.bat
:: atau
pyinstaller --onefile --windowed --name ScheduleParser schedule_gui.py
```

Output: `dist/ScheduleParser.exe`

## Folder Structure

```
schedule-parsing/
│
├── 1_screenshots/        # [INPUT] Drop screenshots here
├── 2_hasil/              # [OUTPUT] Parsed results (by carrier)
│
├── schedule_gui.py       # Main GUI application
├── schedule_parser.py    # Main CLI application
├── requirements.txt      # Python dependencies
│
├── core/                 # Core logic modules
├── processors/           # OCR processing modules
├── formatters/           # Output formatting modules
│
├── scripts/              # Run scripts (cross-platform)
│   ├── run_gui.sh        # macOS/Linux GUI launcher
│   ├── run_gui.bat       # Windows GUI launcher
│   └── run_cli.sh        # macOS/Linux CLI launcher
│
├── setup/                # Installation scripts
│   ├── install_dependencies.sh
│   ├── install_tesseract_mac.sh
│   ├── install_tesseract.bat
│   └── build_exe.bat
│
└── docs/                 # Documentation
    ├── INSTALLATION.md
    ├── README-MACOS.md
    └── README-WINDOWS.md
```

## Troubleshooting

### "Tesseract not found"
- Pastikan Tesseract terinstall
- macOS: `brew install tesseract`
- Windows: Install ke `C:\Program Files\Tesseract-OCR\`

### "tkinter not found" (macOS)
```bash
brew install python-tk
```

### Permission denied (macOS/Linux)
```bash
chmod +x scripts/*.sh setup/*.sh
```

### GUI tidak muncul
- Cek apakah window minimize di Dock/Taskbar
- Coba run langsung: `python schedule_gui.py`
