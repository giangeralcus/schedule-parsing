"""
OCR text extraction with confidence scoring
"""
import re
import os
from typing import List, Dict, Optional, Tuple
from .image import ImageProcessor

# Check for Tesseract
HAS_OCR = False
pytesseract = None

try:
    import pytesseract as _pytesseract
    import shutil
    pytesseract = _pytesseract

    # Find Tesseract executable
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'/usr/bin/tesseract',
        r'/opt/homebrew/bin/tesseract',  # macOS Apple Silicon (Homebrew)
        r'/usr/local/bin/tesseract',     # macOS Intel (Homebrew)
    ]

    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            HAS_OCR = True
            break

    # Fallback: check if tesseract is in PATH
    if not HAS_OCR:
        tesseract_in_path = shutil.which('tesseract')
        if tesseract_in_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_in_path
            HAS_OCR = True
except ImportError:
    pass


class OCRProcessor:
    """OCR text extraction with multiple passes and confidence scoring"""

    def __init__(self, confidence_threshold: int = 30):
        self.confidence_threshold = confidence_threshold
        self.image_processor = ImageProcessor()
        self.has_ocr = HAS_OCR
        self.psm_modes = [6]  # Single pass for cleaner results  # Different page segmentation modes

    def is_available(self) -> bool:
        """Check if OCR is available"""
        return self.has_ocr

    def extract_text(self, image_path: str, timeout: int = 30) -> List[str]:
        """
        Extract text from image using OCR

        Args:
            image_path: Path to image file
            timeout: OCR timeout in seconds (default 30)

        Returns:
            List of cleaned text lines
        """
        if not self.has_ocr:
            return []

        if not os.path.exists(image_path):
            return []

        # Preprocess image
        img = self.image_processor.preprocess(image_path)
        if img is None:
            return []

        # OCR with timeout protection
        all_text = []
        for psm in self.psm_modes:
            try:
                # OEM 1 (LSTM only) for best accuracy, preserve spacing for tables
                config = f'--oem 1 --psm {psm} -c preserve_interword_spaces=1'
                text = pytesseract.image_to_string(img, config=config, timeout=timeout)

                for line in text.split('\n'):
                    line = self._clean_text(line)
                    if line and len(line) > 2 and line not in all_text:
                        all_text.append(line)
            except RuntimeError as e:
                # Timeout error
                if 'Tesseract process timeout' in str(e):
                    continue
            except Exception:
                continue

        return all_text

    def extract_with_confidence(self, image_path: str) -> List[Dict]:
        """
        Extract text with confidence scores

        Returns:
            List of dicts with text, confidence, and bounding box
        """
        if not self.has_ocr:
            return []

        img = self.image_processor.preprocess(image_path)
        if img is None:
            return []

        try:
            from pytesseract import Output
            data = pytesseract.image_to_data(img, output_type=Output.DICT)

            results = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])

                if text and conf >= self.confidence_threshold:
                    results.append({
                        'text': self._clean_text(text),
                        'confidence': conf,
                        'box': (
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        )
                    })

            return results
        except Exception:
            return []

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts from text"""
        text = text.strip()
        if not text:
            return ""

        # FIRST: Preserve date patterns with dot separators (10.Jan -> 10 Jan)
        text = re.sub(r'(\d{1,2})\.(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', r'\1 \2', text, flags=re.IGNORECASE)

        # Fix common OCR errors in times (AFTER date preservation)
        text = re.sub(r'(\d{1,2})\.(\d{2})(?!\d)', r'\1:\2', text)
        text = re.sub(r'(\d{1,2}),(\d{2})(?!\d)', r'\1:\2', text)

        # Fix month spacing
        text = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{4})', r'\1 \2', text)

        # Remove garbage characters but keep essential punctuation and parentheses
        # Parentheses needed for OOCL date format like "07 Jan (Wed)"
        text = re.sub(r'[^A-Za-z0-9\s\-\.,:\/\(\)\[\]]', '', text)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def get_raw_text(self, image_path: str) -> str:
        """Get raw OCR text without processing"""
        if not self.has_ocr:
            return ""

        img = self.image_processor.preprocess(image_path)
        if img is None:
            return ""

        try:
            return pytesseract.image_to_string(img)
        except Exception:
            return ""
