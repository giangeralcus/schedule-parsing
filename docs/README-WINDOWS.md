# Windows Setup

## Quick Install

1. **Install Python 3.10+**
   - Download dari [python.org](https://www.python.org/downloads/)
   - Centang "Add Python to PATH"

2. **Install Tesseract OCR**
   - Download dari [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install ke `C:\Program Files\Tesseract-OCR\`

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run**
   ```cmd
   python schedule_gui.py
   ```

## Optional

Dark theme:
```cmd
pip install ttkbootstrap
```

## Troubleshooting

**Tesseract not found:**
- Pastikan install ke `C:\Program Files\Tesseract-OCR\`
- Atau tambahkan ke PATH

**pip not recognized:**
```cmd
python -m pip install -r requirements.txt
```
