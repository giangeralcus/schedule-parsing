# Installation & Cara Pake

## Quick Start

1. Install Python 3.10+
2. Install Tesseract OCR
3. `pip install -r requirements.txt`
4. `python schedule_gui.py`

---

## Cara Pake

1. Run `python schedule_gui.py`
2. Drag & drop screenshot ke window
3. Copy hasil

---

## Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Windows:**
- Download dari [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Install ke `C:\Program Files\Tesseract-OCR\`

**Linux:**
```bash
sudo apt install tesseract-ocr
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

Optional (dark theme):
```bash
pip install ttkbootstrap
```

---

## Folder

```
1_screenshots/   ← Input
2_hasil/         ← Output
```

---

## Troubleshooting

**Tesseract not found:**
- Pastikan sudah install Tesseract
- macOS: `brew install tesseract`

**Permission denied (macOS/Linux):**
```bash
chmod +x scripts/*.sh setup/*.sh
```
