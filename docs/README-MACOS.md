# macOS Setup

## Quick Install

```bash
# 1. Install Tesseract
brew install tesseract

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python schedule_gui.py
```

## Optional

Dark theme:
```bash
pip install ttkbootstrap
```

## Troubleshooting

**Tesseract not found:**
```bash
brew install tesseract
```

**Permission denied:**
```bash
chmod +x scripts/*.sh setup/*.sh
```
