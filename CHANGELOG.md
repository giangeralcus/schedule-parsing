# Changelog

All notable changes to Schedule Parser will be documented in this file.

## [3.2.7] - 2026-01-08

### Fixed (Deep Code Review)
- **CRITICAL: Dynamic Year** (`core/parsers.py`)
  - Hardcoded 2026 → `datetime.now().year`
  - Auto-handle Dec→Jan year rollover
  - Parser sekarang future-proof untuk 2027+

- **HIGH: Voyage OCR Correction** (`core/parsers.py`)
  - Lebih conservative - tidak corrupt valid voyages
  - Pattern matching lebih strict (hanya 0XX, 1XX, 2XX)
  - "1238" sekarang tetap "1238", bukan jadi "123S"

- **HIGH: Preserve Parentheses** (`processors/ocr.py`)
  - `()[]` sekarang dipertahankan dalam text
  - OOCL date "(Wed)" tidak lagi hilang

- **MEDIUM: Division Guard** (`processors/image.py`)
  - Minimum kernel size 10px untuk tiny images
  - Prevent crash pada images < 300px

---

## [3.2.6] - 2026-01-08

### Fixed
- **Line Removal Bug** (`processors/image.py`)
  - `cv2.add()` → `cv2.bitwise_or()` dengan inverted image
  - Table borders sekarang benar-benar dihapus, bukan ditambahkan
  - Cleaner OCR results untuk tabular layouts

### Improved
- **OCR Engine Upgrade** (`processors/ocr.py`)
  - OEM 3 → OEM 1 (LSTM only) untuk akurasi lebih tinggi
  - Added `preserve_interword_spaces=1` untuk table columns
  - Date preservation: `10.Jan` → `10 Jan` sebelum time conversion

---

## [3.2.5] - 2026-01-08

### Added
- **Carrier Confirmation Dialog** (`schedule_gui.py`)
  - Auto-detect carrier dari OCR text
  - Popup konfirmasi: "Carrier terdeteksi: OOCL. Lanjutkan?"
  - User bisa confirm atau pilih carrier manual
  - Cache OCR results untuk avoid re-processing

- **Changelog Viewer** (`schedule_gui.py`)
  - Tombol "Changelog" di header
  - Popup window menampilkan CHANGELOG.md
  - Version updated ke v3.2.5
  - Contact info: giangeralcus

### Fixed
- **OOCL Parser Rewrite** (`core/parsers.py`)
  - ETD dari kolom ke-2 (Jakarta departure), bukan CY Cutoff
  - ETA dari kolom terakhir (final arrival)
  - Line-based parsing: dates dari 1-5 baris sebelum vessel
  - Voyage OCR fix: 0389S→089S, 0809S→090S, 2268→226S
  - Pattern lebih flexible: "Vessel Voyaga:" (OCR error)

---

## [3.2.4] - 2026-01-07

### Security
- **File Size Limit** (`schedule_gui.py`)
  - Max 50MB untuk prevent DoS attack
  - Error message jika file terlalu besar

- **Magic Bytes Validation** (`schedule_gui.py`)
  - Validasi header file, bukan hanya extension
  - Support PNG, JPEG, GIF, BMP, TIFF

- **Hide Full Paths** (`schedule_gui.py`)
  - Error messages hanya tampilkan filename
  - Tidak expose directory structure

- **Cache File Permissions** (`core/vessel_db.py`)
  - Set 0o600 (owner read/write only) pada Unix
  - Protect local cache dari unauthorized access

- **Sanitized .env.example**
  - URL placeholder untuk public repo

---

## [3.2.3] - 2026-01-07

### Improved
- **GUI Error Messages** (`schedule_gui.py`)
  - Detailed error reporting dengan alasan spesifik
  - Show OCR sample text saat "No schedules found"
  - Tips troubleshooting dalam bahasa Indonesia
  - File validation sebelum processing

- **OCR Timeout Protection** (`processors/ocr.py`)
  - Default timeout 30 detik per image
  - Prevent GUI hang pada image besar/corrupt

---

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
