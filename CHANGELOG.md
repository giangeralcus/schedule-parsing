# Changelog

All notable changes to Schedule Parser will be documented in this file.

## [3.2.2] - 2026-01-07

### Database
- **New Maersk Vessels Added**
  - SPIL NIKEN
  - ARTOTINA
  - AS PIA
  - SEASPAN GUAYAQUIL
  - MARSA PRIDE
- Total vessels: 23
- Total aliases: 40+
- Synced to Supabase Cloud

---

## [3.2.1] - 2026-01-07

### Changed
- **Image Preprocessing Improvements** (`processors/image.py`)
  - Added `_deskew()` method using Hough transform
    - Auto-detects rotation angle from line detection
    - Corrects skewed/rotated screenshots
    - Only applies when angle > 0.5 degrees
  - Added `_remove_lines()` method
    - Removes horizontal table borders
    - Removes vertical table borders
    - Cleaner OCR results for tabular layouts

---

## [3.2.0] - 2026-01-07

### Changed
- **Maersk Parser No-Slash Format** (`core/parsers.py`)
  - Added `VESSEL_PATTERN_NO_SLASH` pattern
    - Supports: "SPIL NIKEN 602N" (space only)
    - Original: "SPIL NISAKA / 602N" (with slash)
  - Updated `can_parse()` logic
    - Slash format always accepted
    - No-slash requires date/time pattern
  - Added skip words filter for OCR false positives
    - VESSEL, VOYAGE, SERVICE, MAERSK, PORT, TERMINAL, etc.

---

## [3.1.0] - 2026-01-07

### Added
- **Vessel Database with Supabase** (`core/vessel_db.py`)
  - Dual-mode support: Docker (local) + Cloud (Supabase)
  - Fuzzy matching using RapidFuzz library
  - Auto-learn OCR variations as aliases
  - Offline fallback with local JSON cache
  - Sync between Docker and Cloud databases

- **Docker Supabase Setup** (`setup/docker_supabase.md`)
  - Documentation for local Supabase deployment
  - Sync workflow instructions

- **SQL Migrations** (`migrations/001_create_vessels_tables.sql`)
  - Vessels table with carrier info
  - Vessel aliases table for OCR corrections
  - Seed data with 10 common vessels

- **New Dependencies** (`requirements.txt`)
  - `supabase>=2.0.0` - Supabase client
  - `rapidfuzz>=3.0.0` - Fuzzy string matching
  - `python-dotenv>=1.0.0` - Environment variables

### Changed
- **OOCL Parser** (`core/parsers.py`)
  - New patterns for OOCL schedule format:
    - `Vessel Voyage: COSCO ISTANBUL 089S`
    - `CY Cutoff: 2026-01-07(Wed) 23:00`
  - Flexible regex to handle OCR errors (Cutof, Cute, Cuter)
  - Extract ETD from CY Cutoff date/time
  - Extract ETA from arrival dates
  - Filter false positives (SERVICE, JAKARTA, etc.)

- **CMA CGM Parser** (`core/parsers.py`)
  - Fixed vessel pattern: `(?:Main\s+)?[Vv]essel\s+...`
  - Now handles "Vessel DANUM 175" without "Main" prefix

- **Image Preprocessing** (`processors/image.py`)
  - Increased `min_width` from 1500 to 2500 for better OCR
  - More aggressive upscaling for complex layouts

- **OCR Processing** (`processors/ocr.py`)
  - Simplified from multi-pass (PSM 6,11,4) to single-pass (PSM 6)
  - Reduces duplicate text extraction
  - Cleaner results for tabular data

- **GUI** (`schedule_gui.py`)
  - Added Python 3.14 compatibility fix for ttkbootstrap

### Fixed
- CMA CGM parser showing "TBA" for vessel names
- OOCL parser returning "No schedule found"
- OCR quality issues with multi-column layouts

### Database
- 18 vessels in database
- 47+ aliases for OCR error correction
- Auto-sync between local Docker and Supabase Cloud

---

## [3.0.0] - 2026-01-06

### Added
- Initial release with multi-carrier support
- Maersk, CMA CGM, OOCL parsers
- GUI with drag-and-drop
- macOS and Windows support
