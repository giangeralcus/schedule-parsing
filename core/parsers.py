"""
Carrier-specific schedule parsers
"""
import re
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .models import Schedule, ParseResult
from .config import CARRIER_MAP, VESSEL_DB
from .vessel_db import match_vessel, get_vessel_db
from .logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def get_carrier_from_filename(filename: str) -> Optional[str]:
    """Extract carrier from filename prefix (e.g., m_screenshot.png -> MAERSK)"""
    basename = os.path.basename(filename).lower()
    if len(basename) >= 2 and basename[1] == '_':
        prefix = basename[0]
        if prefix in CARRIER_MAP:
            return CARRIER_MAP[prefix]
    return None


def detect_carrier(text: str) -> Optional[str]:
    """Auto-detect carrier from text content"""
    text_lower = text.lower()

    signatures = {
        'MAERSK': ['maersk', 'vessel/voyage', '/voyage'],
        'OOCL': ['oocl', 'cy cut-off', 'laden pickup'],
        'CMA-CGM': ['cma', 'cnc', 'vessel'],
        'EVERGREEN': ['evergreen', 'service'],
        'MSC': ['msc', 'm/v'],
        'ONE': ['one', 'ocean network'],
        'HAPAG-LLOYD': ['hapag', 'lloyd'],
    }

    scores = {}
    for carrier, keywords in signatures.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[carrier] = score

    if scores:
        detected = max(scores, key=scores.get)
        logger.info(f"Carrier detected: {detected} (scores: {scores})")
        return detected

    logger.warning("No carrier detected from text")
    return None


class CarrierParser(ABC):
    """Abstract base class for carrier-specific parsers"""

    name: str = "generic"

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Check if this parser can handle the text format"""
        pass

    @abstractmethod
    def parse(self, text_lines: List[str]) -> List[Schedule]:
        """Parse text lines into Schedule objects"""
        pass

    def normalize_vessel(self, name: str) -> str:
        """Normalize vessel name using Supabase + fuzzy matching"""
        name = name.strip()
        # Add space between letters and numbers
        name = re.sub(r'([A-Z])(\d)', r'\1 \2', name)
        name = re.sub(r'\s+', ' ', name).strip()

        # Use vessel_db for smart matching (Supabase + fuzzy)
        matched = match_vessel(name)
        if matched:
            return matched

        # Fallback to local VESSEL_DB if no match
        name_key = name.upper().replace('.', '').replace('-', ' ')
        for key, value in VESSEL_DB.items():
            if key.replace('-', ' ').replace('.', '') in name_key:
                return value
        return name


class MaerskParser(CarrierParser):
    """Parser for Maersk format: VESSEL / VOYAGE or VESSEL VOYAGE with datetime"""

    name = "MAERSK"

    # Pattern 1: "SPIL NISAKA / 602N" (with slash separator)
    VESSEL_PATTERN_SLASH = r'([A-Za-z][A-Za-z\s\.\-]{2,25}?)\s*/\s*(\d{3,4}[A-Z]?)'

    # Pattern 2: "SPIL NIKEN 602N" (no slash, space only)
    # Matches: vessel name (2+ words or single word) + voyage (3-4 digits + letter)
    VESSEL_PATTERN_NO_SLASH = r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(\d{3,4}[A-Z])\b'

    # Pattern: "16 Jan 2026, 19:00"
    DATE_PATTERN = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})[,\s]+(\d{1,2}:\d{2})'

    def can_parse(self, text: str) -> bool:
        has_slash = bool(re.search(self.VESSEL_PATTERN_SLASH, text))
        has_no_slash = bool(re.search(self.VESSEL_PATTERN_NO_SLASH, text))
        has_date_time = bool(re.search(self.DATE_PATTERN, text, re.IGNORECASE))
        has_maersk = 'maersk' in text.lower() or '/voyage' in text.lower()
        # Slash format always works, no-slash requires date/time pattern
        return has_slash or (has_no_slash and has_date_time) or has_maersk

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        full_text = '\n'.join(text_lines)
        schedules = []

        # Try slash pattern first, then no-slash pattern
        vessel_matches = re.findall(self.VESSEL_PATTERN_SLASH, full_text)
        if not vessel_matches:
            vessel_matches = re.findall(self.VESSEL_PATTERN_NO_SLASH, full_text)

        # Skip words that aren't vessel names (common OCR false positives)
        skip_words = ['VESSEL', 'VOYAGE', 'SERVICE', 'MAERSK', 'PORT', 'TERMINAL',
                      'DEPARTURE', 'ARRIVAL', 'CUTOFF', 'CUT', 'OFF', 'DATE', 'TIME']

        vessels = {}
        for v, voyage in vessel_matches:
            voyage = voyage.strip().upper()
            v_clean = v.strip()
            v_upper = v_clean.upper()

            # Skip false positives
            if v_upper in skip_words or any(skip in v_upper for skip in skip_words):
                continue

            v_normalized = self.normalize_vessel(v_clean)
            if len(v_normalized) >= 3 and voyage[-1:].isalpha() and voyage not in vessels:
                vessels[voyage] = v_normalized

        # Find dates with times
        date_matches = re.findall(self.DATE_PATTERN, full_text, re.IGNORECASE)

        # Deduplicate dates
        unique_dates = []
        seen = set()
        for d in date_matches:
            key = f"{d[0]},{d[1]}"
            if key not in seen:
                seen.add(key)
                unique_dates.append(d)

        # Pair dates (ETD, ETA)
        date_pairs = []
        for i in range(0, len(unique_dates), 2):
            etd = f"{unique_dates[i][0]}, {unique_dates[i][1]}"
            eta = f"{unique_dates[i+1][0]}, {unique_dates[i+1][1]}" if i+1 < len(unique_dates) else None
            date_pairs.append((etd, eta))

        # Build schedules
        for i, voyage in enumerate(vessels.keys()):
            etd, eta = date_pairs[i] if i < len(date_pairs) else (None, None)
            schedules.append(Schedule(
                vessel=vessels[voyage],
                voyage=voyage,
                etd=etd,
                eta=eta,
                carrier=self.name
            ))

        return schedules


class CMAParser(CarrierParser):
    """Parser for CMA/CNC format: Vessel NAME + weekday dates + Voyage Ref"""

    name = "CMA-CGM"

    # Pattern: "Vessel DANUM 175" or "Vessel CNC JUPITER" (with optional "Main" prefix)
    # Also handles OCR errors like "DANUM175" (no space)
    VESSEL_PATTERN = r'(?:Main\s+)?[Vv]essel\s+([A-Z]+(?:\s*[A-Z]+)?(?:\s*\d+)?)'

    # Pattern: "Voyage Ref. 0SQ3CN1MA"
    VOYAGE_PATTERN = r'Voyage\s+Ref\.?\s*([A-Z0-9]{6,15})'

    # Pattern: "Sunday, 11-JAN-2026"
    DATE_PATTERN = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]+(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4})'

    def can_parse(self, text: str) -> bool:
        has_vessel = bool(re.search(self.VESSEL_PATTERN, text, re.IGNORECASE))
        has_weekday = bool(re.search(self.DATE_PATTERN, text, re.IGNORECASE))
        has_cnc = 'cnc' in text.lower() or 'cma' in text.lower() or 'tix2cnc' in text.lower()
        return has_vessel or (has_weekday and has_cnc)

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        full_text = '\n'.join(text_lines)
        schedules = []

        # Find all vessels (keep order, normalize names)
        vessel_matches_raw = re.findall(self.VESSEL_PATTERN, full_text, re.IGNORECASE)
        vessel_matches = [self.normalize_vessel(v.strip()) for v in vessel_matches_raw]

        # Find all voyages (keep order, dedupe OCR errors)
        voyage_matches_raw = re.findall(self.VOYAGE_PATTERN, full_text, re.IGNORECASE)
        voyage_matches = []
        seen_voyages = set()
        for v in voyage_matches_raw:
            v_upper = v.upper()
            if v_upper not in seen_voyages:
                voyage_matches.append(v_upper)
                seen_voyages.add(v_upper)

        # Find unique dates (dedupe OCR duplicates)
        date_matches_raw = re.findall(self.DATE_PATTERN, full_text, re.IGNORECASE)
        date_matches = []
        seen_dates = set()
        for d in date_matches_raw:
            d_upper = d.upper()
            if d_upper not in seen_dates:
                date_matches.append(d)
                seen_dates.add(d_upper)

        # Number of schedules = number of date pairs
        num_schedules = len(date_matches) // 2

        # Build schedules - match vessel+voyage with date pairs
        for i in range(num_schedules):
            etd_idx = i * 2
            eta_idx = i * 2 + 1

            etd = date_matches[etd_idx].replace('-', ' ') if etd_idx < len(date_matches) else None
            eta = date_matches[eta_idx].replace('-', ' ') if eta_idx < len(date_matches) else None

            if not etd:
                continue

            # Get vessel and voyage for this schedule
            vessel = vessel_matches[i] if i < len(vessel_matches) else "TBA"
            voyage = voyage_matches[i] if i < len(voyage_matches) else "-"

            schedules.append(Schedule(
                vessel=vessel,
                voyage=voyage,
                etd=etd,
                eta=eta,
                carrier=self.name
            ))

        return schedules


class OOCLParser(CarrierParser):
    """
    Parser for OOCL schedule format

    Screenshot structure (each row):
    - Col1: Origin date (Jakarta load)
    - Col2: ETD (Jakarta departure) ← THIS is the real ETD
    - Transit time (e.g., "14 Days")
    - Col3: Arrival date 1 (transshipment)
    - Col4: Arrival date 2 (final destination) ← THIS is the ETA
    - Right side: CY Cutoff, Vessel Voyage
    """

    name = "OOCL"

    # Vessel Voyage pattern: "Vessel Voyage: COSCO ISTANBUL 089S"
    # Flexible for OCR errors: Voyaga, Voyge, Vayage, etc.
    VESSEL_VOYAGE_PATTERN = r'[Vv]essel\s*(?:[Vv][oay]+g[ae]?)?:?\s*([A-Z][A-Z\s\.\-]{2,20}?)\s+(\d{2,4}[SNsn8]?)'

    # CY Cutoff pattern: "CY Cutoff: 2026-01-07(Wed) 23:00"
    CY_CUTOFF_PATTERN = r'CY\s*Cut[oeu]?[fr]?[f]?:?\s*(\d{4}-\d{2}-\d{2})\s*[\(\[]?(\w{2,3})[\)\]]?\s*(\d{1,2}:\d{2})'

    # Date with weekday: "07 Jan (Wed)" or "10 Jan Sat" or "10.Jan Sat" (dot separator)
    DATE_PATTERN = r'(\d{1,2})[\s\.](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*[\(\[]?([A-Za-z]{2,3})[\)\]]?'

    def can_parse(self, text: str) -> bool:
        text_lower = text.lower()
        return ('oocl' in text_lower or 'cy cut' in text_lower or
                'vessel voyage' in text_lower or 'transshipment' in text_lower)

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        from datetime import datetime, timedelta

        schedules = []
        seen = set()

        # Skip words for vessel name filtering
        skip_words = {'SERVICE', 'VOYAGE', 'VESSEL', 'CUTOFF', 'JAKARTA', 'CHENNAI',
                      'BANGALORE', 'BRISBANE', 'DOOR', 'CARGO', 'NATURE', 'TANK',
                      'EMISSIONS', 'DAYS', 'TRANSSHIPMENT', 'WELL', 'WAKE', 'TEU',
                      'SORT', 'FILTER', 'MORE', 'BOOKING', 'DIRECT', 'FCS', 'SL'}

        # Line-based parsing: find vessel lines and look back for dates
        for line_idx, line in enumerate(text_lines):
            # Find Vessel Voyage in this line
            vessel_match = re.search(self.VESSEL_VOYAGE_PATTERN, line)
            if not vessel_match:
                continue

            vessel_name = vessel_match.group(1).strip().upper()
            voyage = vessel_match.group(2).strip().upper()

            # Skip invalid vessels
            if vessel_name in skip_words or len(vessel_name) < 3:
                continue
            if not re.search(r'[A-Z]{3,}', vessel_name):
                continue

            vessel_clean = self.normalize_vessel(vessel_name)

            # Fix voyage OCR errors
            voyage = self._fix_voyage_ocr(voyage)

            # Skip exact duplicates
            key = f"{vessel_clean}|{voyage}"
            if key in seen:
                continue
            seen.add(key)

            # Look for dates in previous 3-5 lines
            # Find the line with MOST dates (usually the main date row has 4-5 dates)
            dates = []
            best_line_dates = []
            for lookback in range(1, 6):
                if line_idx - lookback < 0:
                    break
                prev_line = text_lines[line_idx - lookback]

                # Stop if we hit another vessel line (previous schedule)
                if re.search(r'Vessel\s*[Vv]', prev_line):
                    break

                line_dates = re.findall(self.DATE_PATTERN, prev_line, re.IGNORECASE)
                if line_dates:
                    # Filter out invalid dates (OCR errors like 48 Jan)
                    valid_dates = [(d, m) for d, m, _ in line_dates if int(d) <= 31]
                    # Keep the line with the MOST dates (main date row usually has 4+ dates)
                    if len(valid_dates) > len(best_line_dates):
                        best_line_dates = valid_dates
            dates = best_line_dates

            # Extract ETD (2nd date) and ETA (last date)
            etd = None
            eta = None
            current_year = datetime.now().year
            current_month = datetime.now().month

            def get_year_for_month(month_str: str) -> int:
                """Determine year based on month - handle Dec->Jan rollover"""
                month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                month_num = month_map.get(month_str.lower()[:3], current_month)
                # If current is Dec and date is Jan-Mar, use next year
                if current_month >= 11 and month_num <= 3:
                    return current_year + 1
                return current_year

            if len(dates) >= 2:
                # ETD is the 2nd date (departure from Jakarta)
                etd_year = get_year_for_month(dates[1][1])
                etd = f"{int(dates[1][0]):02d} {dates[1][1]} {etd_year}"
                # ETA is the last date (final arrival)
                eta_year = get_year_for_month(dates[-1][1])
                eta = f"{int(dates[-1][0]):02d} {dates[-1][1]} {eta_year}"
            elif len(dates) == 1:
                etd_year = get_year_for_month(dates[0][1])
                etd = f"{int(dates[0][0]):02d} {dates[0][1]} {etd_year}"

            # Fallback: look for CY Cutoff and estimate ETD
            if not etd:
                for lookback in range(1, 4):
                    if line_idx - lookback < 0:
                        break
                    prev_line = text_lines[line_idx - lookback]
                    cy_match = re.search(self.CY_CUTOFF_PATTERN, prev_line, re.IGNORECASE)
                    if cy_match:
                        try:
                            cutoff_date = datetime.strptime(cy_match.group(1), "%Y-%m-%d")
                            etd_dt = cutoff_date + timedelta(days=3)
                            etd = etd_dt.strftime("%d %b %Y")
                        except:
                            pass
                        break

            schedules.append(Schedule(
                vessel=vessel_clean,
                voyage=voyage,
                etd=etd,
                eta=eta,
                carrier=self.name
            ))

        return schedules

    def _fix_voyage_ocr(self, voyage: str) -> str:
        """Fix common OCR errors in voyage numbers.

        Standard OOCL voyage format: 3 digits + direction (N/S/E/W)
        Examples: 089S, 090N, 226S

        Common OCR errors:
        - 'S' misread as '8' (226S -> 2268)
        - Extra garbage digit inserted (089S -> 0389S)
        """
        original = voyage

        # Already has valid format (3 digits + letter)? Keep it
        if re.match(r'^\d{3}[SNEW]$', voyage, re.IGNORECASE):
            return voyage.upper()

        # 4 digits ending with 8: likely OCR misread S as 8
        # Only apply if pattern looks like voyage (not random number)
        # 2268 -> 226S, but NOT 1238 -> 123S (could be valid)
        if re.match(r'^[012]\d{2}8$', voyage):
            # Starts with 0, 1, or 2 - likely voyage with 8->S error
            voyage = voyage[:-1] + 'S'

        # 5-char voyages: OCR inserted extra digit
        # 0389S -> 089S, 0809S -> 090S
        if len(voyage) == 5 and voyage[-1].upper() in 'SNEW':
            digits = voyage[:-1]
            suffix = voyage[-1].upper()
            if digits[0] == '0':
                # Likely format 0XXX -> 0XX (remove middle garbage)
                if digits[2] == '0':
                    # 0809 -> 090 (0 + 9 + 0)
                    voyage = digits[0] + digits[3] + digits[2] + suffix
                else:
                    # 0389 -> 089 (0 + 8 + 9)
                    voyage = digits[0] + digits[2] + digits[3] + suffix

        # 4-char with letter: first digit might be garbage
        # 389S -> 089S (3 is garbage OCR)
        if len(voyage) == 4 and voyage[-1].upper() in 'SNEW':
            if voyage[0] in '3456789' and voyage[1] in '0123456789':
                # First digit looks wrong for voyage, replace with 0
                voyage = '0' + voyage[1:]

        # If still no letter suffix but looks like voyage, add S (most common)
        # Only for 3-digit numbers that look like voyages
        if re.match(r'^[012]\d{2}$', voyage):
            voyage = voyage + 'S'

        return voyage.upper()



class GenericParser(CarrierParser):
    """Fallback parser for unknown formats"""

    name = "GENERIC"

    def can_parse(self, text: str) -> bool:
        return True  # Always can try

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        full_text = '\n'.join(text_lines)
        schedules = []

        # Try multiple vessel patterns
        vessel_patterns = [
            r'([A-Z][A-Z\s\.\-]{2,25}?)\s*/\s*(\d{3,4}[A-Z]?)',  # Vessel / Voyage
            r'Vessel[\s:]+([A-Z][A-Z0-9\s\.\-]{2,25})',  # Vessel: NAME
            r'M/V\s+([A-Z][A-Z\s\.\-]{2,30})',  # M/V NAME
        ]

        vessels = []
        for pattern in vessel_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                for m in matches:
                    if isinstance(m, tuple):
                        vessels.append((self.normalize_vessel(m[0]), m[1] if len(m) > 1 else "-"))
                    else:
                        vessels.append((self.normalize_vessel(m), "-"))
                break

        # Find any dates
        date_patterns = [
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})[,\s]+(\d{1,2}:\d{2})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4})',
        ]

        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                for m in matches:
                    if isinstance(m, tuple):
                        dates.append(f"{m[0]}, {m[1]}" if len(m) > 1 else m[0])
                    else:
                        dates.append(m.replace('-', ' '))
                break

        # Pair vessels with dates
        seen = set()
        for i, (vessel, voyage) in enumerate(vessels):
            etd_idx = i * 2
            eta_idx = i * 2 + 1

            etd = dates[etd_idx] if etd_idx < len(dates) else None
            eta = dates[eta_idx] if eta_idx < len(dates) else None

            if not etd:
                continue

            key = f"{vessel}|{etd}"
            if key in seen:
                continue
            seen.add(key)

            schedules.append(Schedule(
                vessel=vessel,
                voyage=voyage,
                etd=etd,
                eta=eta
            ))

        return schedules


# Parser registry
PARSERS = [
    MaerskParser(),
    CMAParser(),
    OOCLParser(),
    GenericParser(),  # Fallback
]


def parse_schedules(text_lines: List[str], carrier_hint: Optional[str] = None) -> List[Schedule]:
    """
    Parse schedules using appropriate carrier parser

    Args:
        text_lines: OCR extracted text lines
        carrier_hint: Optional carrier name hint

    Returns:
        List of Schedule objects
    """
    logger.debug(f"Parsing {len(text_lines)} text lines, carrier_hint={carrier_hint}")
    full_text = '\n'.join(text_lines)
    schedules = []
    used_parser = None

    # If carrier hint provided, try that parser first
    if carrier_hint:
        for parser in PARSERS:
            if parser.name == carrier_hint or carrier_hint in parser.name:
                logger.debug(f"Trying parser: {parser.name} (from hint)")
                schedules = parser.parse(text_lines)
                if schedules:
                    used_parser = parser.name
                    break

    # Try each parser in order if no schedules yet
    if not schedules:
        for parser in PARSERS:
            if parser.can_parse(full_text):
                logger.debug(f"Trying parser: {parser.name} (auto-detect)")
                schedules = parser.parse(text_lines)
                if schedules:
                    used_parser = parser.name
                    break

    # Validate and fix dates (swap if ETD > ETA)
    for schedule in schedules:
        schedule.swap_dates_if_needed()

    if schedules:
        logger.info(f"Parsed {len(schedules)} schedules using {used_parser}")
        for s in schedules[:3]:
            logger.debug(f"  Schedule: {s.vessel}/{s.voyage} ETD:{s.etd} ETA:{s.eta}")
    else:
        logger.warning(f"No schedules parsed from {len(text_lines)} lines")

    return schedules
