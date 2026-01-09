"""
OCR text extraction with confidence scoring
"""
import re
import os
from typing import List, Dict, Optional, Tuple
from .image import ImageProcessor

# Import logger
try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

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

    # Character blacklist - block garbage characters that appear in OCR errors
    # Using blacklist instead of whitelist to preserve word segmentation/spacing
    CHAR_BLACKLIST = "@#$%^&*+=[]{}|\\~`<>\"'"

    def __init__(self, confidence_threshold: int = 30):
        self.confidence_threshold = confidence_threshold
        self.image_processor = ImageProcessor()
        self.has_ocr = HAS_OCR
        self.psm_modes = [6]  # Single pass for cleaner results

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
            logger.warning("OCR not available - Tesseract not installed")
            return []

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []

        logger.debug(f"Processing image: {os.path.basename(image_path)}")

        # Preprocess image
        img = self.image_processor.preprocess(image_path)
        if img is None:
            logger.error(f"Failed to preprocess image: {image_path}")
            return []

        # OCR with timeout protection
        all_text = []
        for psm in self.psm_modes:
            try:
                # OEM 1 (LSTM only) for best accuracy, preserve spacing for tables
                # Using blacklist instead of whitelist to preserve word segmentation
                config = (
                    f'--oem 1 --psm {psm} '
                    f'-c preserve_interword_spaces=1 '
                    f'-c tessedit_char_blacklist={self.CHAR_BLACKLIST}'
                )
                text = pytesseract.image_to_string(img, config=config, timeout=timeout)

                for line in text.split('\n'):
                    line = self._clean_text(line)
                    if line and len(line) > 2 and line not in all_text:
                        all_text.append(line)
            except RuntimeError as e:
                # Timeout error
                if 'Tesseract process timeout' in str(e):
                    logger.warning(f"OCR timeout (PSM {psm}) - {timeout}s exceeded")
                    continue
            except Exception as e:
                logger.error(f"OCR error (PSM {psm}): {e}")
                continue

        logger.info(f"OCR extracted {len(all_text)} lines from {os.path.basename(image_path)}")
        if all_text:
            logger.debug(f"First 3 lines: {all_text[:3]}")

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

    def extract_table_data(self, image_path: str, timeout: int = 30) -> Dict:
        """
        ULTRATHINK: Extract table data using TSV + Bounding Box analysis

        This method uses spatial analysis to properly parse multi-column tables
        by analyzing word positions and grouping them into rows and columns.

        Returns:
            Dict with:
            - 'rows': List of rows, each row is a list of cells
            - 'raw_words': List of all words with positions
            - 'columns': Detected column boundaries
        """
        if not self.has_ocr:
            logger.warning("OCR not available")
            return {'rows': [], 'raw_words': [], 'columns': []}

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {'rows': [], 'raw_words': [], 'columns': []}

        img = self.image_processor.preprocess(image_path)
        if img is None:
            return {'rows': [], 'raw_words': [], 'columns': []}

        try:
            from pytesseract import Output

            # Use PSM 6 for table-like structure
            config = '--oem 1 --psm 6 -c preserve_interword_spaces=1'
            data = pytesseract.image_to_data(img, config=config, output_type=Output.DICT, timeout=timeout)

            # Extract words with positions
            words = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0

                if text and conf >= self.confidence_threshold:
                    words.append({
                        'text': self._clean_text(text),
                        'raw_text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'conf': conf,
                        'center_x': data['left'][i] + data['width'][i] // 2,
                        'center_y': data['top'][i] + data['height'][i] // 2
                    })

            if not words:
                return {'rows': [], 'raw_words': [], 'columns': []}

            # Group words into rows based on Y position
            rows = self._group_words_into_rows(words)

            # Detect column boundaries
            columns = self._detect_columns(words, rows)

            # Organize words into cells based on columns
            structured_rows = self._organize_into_cells(rows, columns)

            logger.info(f"Table extraction: {len(structured_rows)} rows, {len(columns)} columns detected")

            return {
                'rows': structured_rows,
                'raw_words': words,
                'columns': columns
            }

        except RuntimeError as e:
            if 'timeout' in str(e).lower():
                logger.warning(f"OCR timeout during table extraction")
            return {'rows': [], 'raw_words': [], 'columns': []}
        except Exception as e:
            logger.error(f"Table extraction error: {e}")
            return {'rows': [], 'raw_words': [], 'columns': []}

    def _group_words_into_rows(self, words: List[Dict], y_threshold: int = 15) -> List[List[Dict]]:
        """
        Group words into rows based on Y position (words on same horizontal line)

        Args:
            words: List of word dicts with position info
            y_threshold: Max Y difference to consider words on same row

        Returns:
            List of rows, each row is a list of words sorted by X position
        """
        if not words:
            return []

        # Sort words by Y position first
        sorted_words = sorted(words, key=lambda w: w['y'])

        rows = []
        current_row = [sorted_words[0]]
        current_y = sorted_words[0]['y']

        for word in sorted_words[1:]:
            # If word is on approximately the same Y level, add to current row
            if abs(word['y'] - current_y) <= y_threshold:
                current_row.append(word)
            else:
                # Start new row
                # Sort current row by X position before adding
                current_row.sort(key=lambda w: w['x'])
                rows.append(current_row)
                current_row = [word]
                current_y = word['y']

        # Don't forget the last row
        current_row.sort(key=lambda w: w['x'])
        rows.append(current_row)

        return rows

    def _detect_columns(self, words: List[Dict], rows: List[List[Dict]]) -> List[Dict]:
        """
        Detect column boundaries based on word positions

        Strategy: Find clusters of X positions that indicate column starts

        Returns:
            List of column dicts with 'start_x', 'end_x', 'center_x'
        """
        if not words or not rows:
            return []

        # Collect all X start positions
        x_positions = [w['x'] for w in words]

        if not x_positions:
            return []

        # Find column boundaries by clustering X positions
        min_x = min(x_positions)
        max_x = max(x_positions)
        width = max_x - min_x

        if width <= 0:
            return [{'start_x': min_x, 'end_x': max_x, 'center_x': (min_x + max_x) // 2}]

        # For Maersk format, expect ~3 columns: Departure, Arrival, Vessel/Voyage
        # Divide into 3 roughly equal sections
        col_width = width // 3

        columns = []
        for i in range(3):
            col_start = min_x + (i * col_width)
            col_end = min_x + ((i + 1) * col_width) if i < 2 else max_x + 100
            columns.append({
                'start_x': col_start,
                'end_x': col_end,
                'center_x': (col_start + col_end) // 2,
                'index': i
            })

        return columns

    def _organize_into_cells(self, rows: List[List[Dict]], columns: List[Dict]) -> List[List[str]]:
        """
        Organize words into table cells based on column boundaries

        Returns:
            List of rows, each row is a list of cell strings
        """
        if not rows or not columns:
            return []

        structured_rows = []

        for row_words in rows:
            cells = [[] for _ in columns]

            for word in row_words:
                word_center_x = word['center_x']

                # Find which column this word belongs to
                for i, col in enumerate(columns):
                    if col['start_x'] <= word_center_x < col['end_x']:
                        cells[i].append(word['text'])
                        break
                else:
                    # Word is past last column, add to last cell
                    if columns:
                        cells[-1].append(word['text'])

            # Join words in each cell
            cell_strings = [' '.join(cell_words) for cell_words in cells]
            structured_rows.append(cell_strings)

        return structured_rows

    def extract_maersk_schedules(self, image_path: str, timeout: int = 30) -> List[Dict]:
        """
        Specialized extractor for Maersk schedule format

        Uses TSV + bounding box to extract structured schedule data,
        filtering out Deadlines section.

        Returns:
            List of schedule dicts with 'departure', 'arrival', 'vessel', 'voyage'
        """
        table_data = self.extract_table_data(image_path, timeout)

        if not table_data['rows']:
            return []

        schedules = []
        rows = table_data['rows']

        # Date patterns - flexible to handle OCR spacing issues
        full_date_pattern = r'(\d{1,2})\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})'
        day_only_pattern = r'^(\d{1,2})$'
        month_year_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}'

        # Month names to exclude from vessel matching
        MONTH_NAMES = {'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                       'january', 'february', 'march', 'april', 'june', 'july', 'august',
                       'september', 'october', 'november', 'december'}

        # Skip words for filtering
        SKIP_WORDS = {'departure', 'arrival', 'vessel', 'voyage', 'deadline', 'empty',
                      'container', 'gate', 'shipping', 'instruction', 'verified',
                      'gross', 'mass', 'terminal', 'port', 'transit', 'time', 'days',
                      'hours', 'route', 'details', 'show', 'priok', 'chabang'}

        # Find all schedule blocks by looking at headers
        schedule_sections = []
        for i, row in enumerate(rows):
            row_text = ' '.join(row).lower()
            if 'departure' in row_text and ('arrival' in row_text or 'vessel' in row_text):
                schedule_sections.append(i)

        if not schedule_sections:
            logger.warning("Could not find any header rows in table")
            return []

        # Process each section
        for section_start in schedule_sections:
            # Get rows after this header until next header or deadline section
            section_end = len(rows)
            for i in range(section_start + 1, len(rows)):
                row_text = ' '.join(rows[i]).lower()
                if 'departure' in row_text and 'arrival' in row_text:
                    section_end = i
                    break
                if 'deadline' in row_text:
                    section_end = i
                    break

            # Process data rows in this section (usually just 1-2 rows after header)
            for row in rows[section_start + 1:min(section_start + 3, section_end)]:
                if len(row) < 2:
                    continue

                row_text_lower = ' '.join(row).lower()

                # Skip non-data rows
                if any(skip in row_text_lower for skip in SKIP_WORDS):
                    continue

                # Combine all cells to search for patterns
                full_row_text = ' '.join(row)

                # Extract dates more carefully - handle split dates like ['18', '27 Jan 2026']
                # First, find complete dates in the row
                complete_dates = re.findall(
                    r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})',
                    full_row_text, re.IGNORECASE
                )

                # Also check if first cell is just a day number that needs to be combined
                cell0 = row[0].strip() if len(row) > 0 else ''
                cell1 = row[1].strip() if len(row) > 1 else ''

                dates_found = []
                day_only_match = re.match(r'^(\d{1,2})$', cell0)

                if day_only_match:
                    # First cell is just a day number (e.g., "18")
                    # Look for month+year in next cell to construct departure date
                    month_year_match = re.search(
                        r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})',
                        cell1, re.IGNORECASE
                    )
                    if month_year_match:
                        # The month from cell1's date is likely the same month as cell0's day
                        dep_day = day_only_match.group(1)
                        month = month_year_match.group(2)[:3].capitalize()
                        year = month_year_match.group(3)
                        dates_found.append((dep_day, month, year))

                        # Cell1 has the arrival date
                        arr_day = month_year_match.group(1)
                        dates_found.append((arr_day, month, year))
                else:
                    # Standard case - dates are complete
                    dates_found = complete_dates

                # Find vessel/voyage - look for patterns like "VESSEL:603N" or "VESSEL 603N"
                # Voyage number format: 3-4 digits optionally followed by a letter
                vessel_voyage_patterns = [
                    # "JULIUS-S.:603N" or "JULIUS-S. 603N"
                    r'([A-Z][A-Za-z\-\.\_]+(?:[\s\-][A-Za-z\-\.\_]+)?)\s*[:\.\s]+(\d{3,4}[A-Z]?)',
                    # "MartinSchulte 605N" (CamelCase with number)
                    r'([A-Z][a-z]+[A-Z][a-z]+)\s*(\d{3,4}[A-Z]?)',
                    # "SKY PEACE 604N"
                    r'([A-Z]{2,}(?:\s+[A-Z]+)?)\s+(\d{3,4}[A-Z]?)',
                ]

                vessel_name = None
                voyage = None

                for pattern in vessel_voyage_patterns:
                    matches = re.findall(pattern, full_row_text)
                    for match in matches:
                        candidate_vessel = match[0].strip()
                        candidate_voyage = match[1].strip().upper()

                        # Clean vessel name
                        candidate_vessel = re.sub(r'[:\.\s]+$', '', candidate_vessel).strip()

                        # Skip if vessel name is a month or skip word
                        if candidate_vessel.lower() in MONTH_NAMES or candidate_vessel.lower() in SKIP_WORDS:
                            continue

                        # Skip if vessel name is too short
                        if len(candidate_vessel) < 4:
                            continue

                        # Valid vessel found
                        vessel_name = candidate_vessel
                        voyage = candidate_voyage
                        break

                    if vessel_name:
                        break

                # Need at least one date and vessel
                if dates_found and vessel_name:
                    # Get dates - dates_found is list of (day, month, year) tuples
                    dep_date = None
                    arr_date = None

                    if len(dates_found) >= 2:
                        dep_date = f"{dates_found[0][0]} {dates_found[0][1]} {dates_found[0][2]}"
                        arr_date = f"{dates_found[1][0]} {dates_found[1][1]} {dates_found[1][2]}"
                    elif len(dates_found) == 1:
                        dep_date = f"{dates_found[0][0]} {dates_found[0][1]} {dates_found[0][2]}"

                    if dep_date:
                        schedules.append({
                            'departure': self._normalize_date(dep_date),
                            'arrival': self._normalize_date(arr_date) if arr_date else '',
                            'vessel': vessel_name,
                            'voyage': voyage
                        })

        logger.info(f"Extracted {len(schedules)} schedules using TSV method")
        return schedules

    def _extract_month(self, text: str, occurrence: int = 0) -> str:
        """Extract the nth occurrence of a month name from text"""
        months = re.findall(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?',
                           text, re.IGNORECASE)
        if occurrence < len(months):
            return months[occurrence][:3].capitalize()
        return ''

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date format"""
        if not date_str:
            return None
        # Extract just the date part
        date_pattern = r'(\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})'
        match = re.search(date_pattern, date_str, re.IGNORECASE)
        if match:
            date_str = match.group(1)
        # Clean up spacing
        date_str = re.sub(r'\.', ' ', date_str)
        date_str = re.sub(r'(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', r'\1 \2', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{4})', r'\1 \2', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'\s+', ' ', date_str).strip()
        return date_str
