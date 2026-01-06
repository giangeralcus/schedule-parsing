# Schedule Parser v3.0

Offline shipping schedule parser with OCR - extract vessel schedules from screenshots.

## About

**Author:** Gian Geralcus
**Created:** 06 January 2026
**Project Type:** Personal Project

### Tujuan / Purpose

Memudahkan small performance workflow yang dapat memiliki efek jangka panjang dalam pengurusan scheduling kapal - baik yang **delay**, **non-delay**, maupun **conjunction**.

Tool ini dibuat untuk:
- Mengotomatisasi ekstraksi data schedule dari screenshot shipping line
- Mengurangi manual data entry yang memakan waktu
- Meminimalisir human error dalam penginputan jadwal kapal
- Mempercepat workflow harian dalam pengurusan vessel scheduling

> *"Small efficiency improvements compound over time"* - Apa yang terlihat seperti penghematan kecil setiap hari, akan memberikan dampak signifikan dalam jangka panjang untuk operasional shipping schedule management.

## Quick Start Guides

- **[macOS Setup Guide](docs/README-MACOS.md)** - Full installation & usage guide untuk Mac
- **[Windows Setup Guide](docs/README-WINDOWS.md)** - Full installation & usage guide untuk Windows

## Features

- **Drag & Drop GUI** - Modern dark theme interface
- **Multi-Carrier Support** - Maersk, OOCL, CMA-CGM, Hapag-Lloyd, Evergreen, ONE, Yang Ming, MSC, ZIM, Wan Hai, PIL
- **Auto-Detection** - Automatically detects carrier from filename or content
- **OCR Powered** - Uses Tesseract OCR with advanced image preprocessing
- **Multiple Output Formats** - Table view, email format, clipboard copy
- **Organized Output** - Saves results in carrier-specific folders

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Tesseract OCR**

### Quick Setup (Recommended)

```bash
# macOS/Linux
./setup/install_dependencies.sh

# Windows
pip install -r requirements.txt
```

### Install Tesseract OCR

**macOS:**
```bash
./setup/install_tesseract_mac.sh
# or manually: brew install tesseract
```

**Windows:**
- Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Install to `C:\Program Files\Tesseract-OCR\`

### Optional: Install ttkbootstrap for modern UI

```bash
pip install ttkbootstrap
```

## Usage

### GUI Mode (Recommended)

```bash
# Direct
python schedule_gui.py

# macOS/Linux
./scripts/run_gui.sh

# Windows
scripts\run_gui.bat
```

1. Drag & drop screenshot onto the window
2. Results appear automatically
3. Click "Copy to Clipboard" or "Save to File"

### CLI Mode

```bash
# Direct
python schedule_parser.py

# macOS/Linux
./scripts/run_cli.sh
```

Options:
- `[A]ll` - Process all screenshots
- `[1-9]` - Process specific file
- `[E]dit` - Manual text editing mode
- `[W]atch` - Auto-process new files
- `[M]anual` - Manual entry mode

## File Naming Convention

Use prefixes to identify carriers:

| Prefix | Carrier |
|--------|---------|
| `m_` | MAERSK |
| `o_` | OOCL |
| `c_` | CMA-CGM |
| `h_` | HAPAG-LLOYD |
| `e_` | EVERGREEN |
| `n_` | ONE |
| `y_` | YANG-MING |
| `s_` | MSC |
| `z_` | ZIM |
| `w_` | WAN-HAI |
| `p_` | PIL |

Example: `m_schedule_jan.png` → Parsed as MAERSK

## Folder Structure

```
schedule-parsing/
│
├── 1_screenshots/        # [INPUT] Drop screenshots here
├── 2_hasil/              # [OUTPUT] Parsed results (by carrier)
│   ├── MAERSK/
│   ├── OOCL/
│   └── CMA-CGM/
│
├── schedule_gui.py       # Main GUI application
├── schedule_parser.py    # Main CLI application
├── requirements.txt      # Python dependencies
│
├── core/                 # Core logic modules
│   ├── config.py         # Configuration & carrier mappings
│   ├── models.py         # Data models (Schedule, ParseResult)
│   └── parsers.py        # Carrier-specific parsers
│
├── processors/           # Processing modules
│   ├── image.py          # Image preprocessing
│   └── ocr.py            # Tesseract OCR wrapper
│
├── formatters/           # Output modules
│   └── output.py         # Table/email formatting
│
├── scripts/              # Run scripts (cross-platform)
│   ├── run_gui.sh        # macOS/Linux GUI launcher
│   ├── run_gui.bat       # Windows GUI launcher
│   └── run_cli.sh        # macOS/Linux CLI launcher
│
└── setup/                # Installation & build scripts
    ├── install_dependencies.sh   # Install Python packages
    ├── install_tesseract_mac.sh  # Install Tesseract (macOS)
    ├── install_tesseract.bat     # Install Tesseract (Windows)
    └── build_exe.bat             # Build standalone .exe
```

## Build Standalone EXE (Windows)

```bash
# Using script
setup\build_exe.bat

# Manual
pyinstaller --onefile --windowed --name ScheduleParser schedule_gui.py
```

Output: `dist/ScheduleParser.exe`

## Output Format

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

## Dependencies

- `pytesseract` - OCR engine interface
- `pillow` - Image processing
- `opencv-python` - Advanced image preprocessing
- `pyperclip` - Clipboard support
- `tkinterdnd2` - Drag & drop support
- `ttkbootstrap` - Modern UI theme (optional)
- `numpy` - Numerical operations

## License

**Personal Project - Gian Geralcus**

This project is a personal project created by Gian Geralcus. All rights reserved.
Unauthorized copying, modification, or distribution is not permitted without explicit permission from the author.

