# Schedule Parser v3.0

Offline shipping schedule parser with OCR - extract vessel schedules from screenshots.

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
2. **Tesseract OCR** - [Download](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to `C:\Program Files\Tesseract-OCR\`

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Optional: Install ttkbootstrap for modern UI

```bash
pip install ttkbootstrap
```

## Usage

### GUI Mode (Recommended)

```bash
python schedule_gui.py
# or
run_gui.bat
```

1. Drag & drop screenshot onto the window
2. Results appear automatically
3. Click "Copy to Clipboard" or "Save to File"

### CLI Mode

```bash
python schedule_parser.py
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
SCHEDULE/
├── 1_screenshots/     # Drop screenshots here
├── 2_hasil/           # Output files (organized by carrier)
│   ├── MAERSK/
│   ├── OOCL/
│   └── CMA-CGM/
├── core/              # Configuration, models, parsers
├── processors/        # Image & OCR processing
├── formatters/        # Output formatting
├── schedule_gui.py    # GUI application
├── schedule_parser.py # CLI application
└── requirements.txt
```

## Build Standalone EXE

```bash
build_exe.bat
# or
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

MIT License
