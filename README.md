# Schedule Parser v3.2

A powerful OCR tool to parse vessel/shipping schedules from screenshots into formatted text for quick email communication.

Built for freight forwarding professionals who need to quickly extract and share vessel schedule information.

## Features

- **Multi-Carrier Support** - Maersk, CMA CGM, OOCL, Hapag-Lloyd, MSC, and more
- **GUI & CLI** - Drag-and-drop GUI or command-line interface
- **Smart OCR** - Tesseract OCR with image preprocessing (deskew, denoise, line removal)
- **Vessel Database** - Fuzzy matching with auto-learn for OCR corrections
- **Watch Mode** - Auto-process new screenshots dropped into folder
- **Email-Ready Output** - Formatted text copied to clipboard instantly
- **Offline First** - Works 100% offline, optional cloud sync

## Screenshots

```
╔═══════════════════════════════════════════════════════╗
║  SCHEDULE PARSER v3.2 - Offline Edition               ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Select file to process:                              ║
║    1. [MAERSK] m_schedule_jan.png                     ║
║    2. [OOCL] o_weekly_schedule.png                    ║
║    3. [CMA] c_rotation.png                            ║
║                                                       ║
║  Commands: [A]ll  [E]dit  [W]atch  [M]anual  [Q]uit   ║
╚═══════════════════════════════════════════════════════╝
```

## Quick Start

### Prerequisites
- Python 3.10+
- Tesseract OCR installed

### Installation

```bash
# Clone repository
git clone https://github.com/giangeralcus/schedule-parser.git
cd schedule-parser

# Install dependencies
pip install -r requirements.txt

# Run GUI
python schedule_gui.py

# Or run CLI
python schedule_parser.py
```

### Usage

**GUI Mode:**
```bash
python schedule_gui.py
# Drag & drop screenshot → Get formatted output → Copy to clipboard
```

**CLI Mode:**
```bash
# Interactive menu
python schedule_parser.py

# Process specific file
python schedule_parser.py screenshot.png

# Watch folder for new files
python schedule_parser.py --watch

# Manual entry
python schedule_parser.py --manual
```

## Output Format

```
=== VESSEL SCHEDULE ===

Option 1:
  Vessel : SPIL NISAKA
  Voyage : 602N
  ETD JKT: 16 Jan 2026 19:00
  ETA SIN: 24 Jan 2026 22:00

Option 2:
  Vessel : SINAR BANDUNG
  Voyage : 603N
  ETD JKT: 23 Jan 2026 19:00
  ETA SIN: 31 Jan 2026 22:00

========================
```

## Supported Carriers

| Carrier | Status | Auto-Detect |
|---------|--------|-------------|
| Maersk | ✅ Full | ✅ |
| CMA CGM | ✅ Full | ✅ |
| OOCL | ✅ Full | ✅ |
| Hapag-Lloyd | 🔄 Planned | - |
| MSC | 🔄 Planned | - |
| Evergreen | 🔄 Planned | - |

## Project Structure

```
schedule-parser/
├── schedule_gui.py       # GUI application (drag & drop)
├── schedule_parser.py    # CLI application
├── core/
│   ├── config.py         # Configuration
│   ├── models.py         # Data models
│   ├── parsers.py        # Carrier-specific parsers
│   └── vessel_db.py      # Vessel database with fuzzy matching
├── processors/
│   ├── ocr.py            # Tesseract OCR wrapper
│   └── image.py          # Image preprocessing
├── formatters/
│   └── output.py         # Email/table formatting
├── 1_screenshots/        # Input folder
├── 2_hasil/              # Output folder
└── migrations/           # Database migrations
```

## Tech Stack

- **Python 3.10+**
- **Tesseract OCR** - Optical character recognition
- **OpenCV** - Image preprocessing
- **ttkbootstrap** - Modern GUI
- **RapidFuzz** - Fuzzy string matching
- **Supabase** - Optional cloud database

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

### Recent Updates (v3.2.5)
- Carrier auto-detection with confirmation dialog
- OOCL parser rewrite for better accuracy
- Security improvements (file validation, size limits)
- Image deskew and table line removal

## Author

**Gian Geralcus**
Licensed Customs Broker | Freight Forwarding | Jakarta, Indonesia

[![LinkedIn](https://img.shields.io/badge/LinkedIn-giangeralcus-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/giangeralcus)
[![GitHub](https://img.shields.io/badge/GitHub-giangeralcus-181717?style=flat-square&logo=github)](https://github.com/giangeralcus)

## License

Personal Project - For personal and educational use.

---

`freight-forwarding` `vessel-schedule` `shipping` `logistics` `ocr` `python` `indonesia` `customs-broker`
