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
        return max(scores, key=scores.get)
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
    """Parser for OOCL format: Multiple formats supported"""

    name = "OOCL"

    # Vessel pattern: "Vessel Voyage: COSCO ISTANBUL 089S" or standalone
    VESSEL_VOYAGE_PATTERN = r'(?:Vessel\s*(?:/\s*)?Voyage:?\s*)?([A-Z][A-Z\s\.\-]{2,20}?)\s+(\d{3,4}[A-Z0-9]?\d*[A-Z]?)'

    # CY Cutoff - flexible for OCR errors: Cutof, Cute, Cuter, etc.
    # Also handles '(' read as '1' by OCR
    CY_CUTOFF_PATTERN = r'CY\s*Cut[oeu]?[fr]?[f]?:?\s*(\d{4}-\d{2}-\d{2})\d?\s*[\(\[]?\w{2,3}[\)\]]?\s*(\d{1,2}:\d{2})'

    # Date with weekday: "07 Jan (Wed)" or "07 Jan Wee" (OCR error)
    DATE_WEEKDAY_PATTERN = r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*[\(\[]?(\w{2,3})[\)\]]?'

    def can_parse(self, text: str) -> bool:
        text_lower = text.lower()
        return ('oocl' in text_lower or 'cy cut' in text_lower or
                'vessel voyage' in text_lower or 'transshipment' in text_lower)

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        full_text = '\n'.join(text_lines)
        schedules = []

        # Extract CY Cutoff dates (ETD with time)
        cutoff_matches = re.findall(self.CY_CUTOFF_PATTERN, full_text, re.IGNORECASE)

        # Extract vessel/voyage pairs
        vessel_matches = re.findall(self.VESSEL_VOYAGE_PATTERN, full_text)

        # Extract all dates for ETA calculation
        date_matches = re.findall(self.DATE_WEEKDAY_PATTERN, full_text, re.IGNORECASE)

        # Filter valid vessels
        skip_words = ['SERVICE', 'VOYAGE', 'VESSEL', 'CUTOFF', 'CY CUT', 'JAKARTA',
                      'CHENNAI', 'BANGALORE', 'DOOR', 'CARGO', 'NATURE', 'TANK',
                      'EMISSIONS', 'DAYS', 'TRANSSHIPMENT', 'SI CUT', 'FCS', 'SL',
                      'WELL', 'WAKE', 'TEU']
        valid_vessels = []
        for vessel, voyage in vessel_matches:
            v_upper = vessel.strip().upper()
            if v_upper not in skip_words and len(v_upper) >= 3:
                if re.search(r'[A-Z]{3,}', v_upper) and not v_upper.startswith('CY'):
                    valid_vessels.append((vessel.strip(), voyage.strip()))

        # Group dates by schedule row (approximately 4-5 dates per row)
        # Find unique date groups by looking at patterns
        
        # Build schedules
        seen = set()
        cutoff_idx = 0
        date_idx = 0
        
        for i, (vessel, voyage) in enumerate(valid_vessels):
            vessel_clean = self.normalize_vessel(vessel)
            voyage_clean = voyage.upper()

            key = f"{vessel_clean}|{voyage_clean}"
            if key in seen:
                continue
            seen.add(key)

            # ETD from CY Cutoff
            etd = None
            if cutoff_idx < len(cutoff_matches):
                date_part, time_part = cutoff_matches[cutoff_idx]
                from datetime import datetime
                try:
                    dt = datetime.strptime(date_part, "%Y-%m-%d")
                    etd = dt.strftime("%d %b %Y") + f", {time_part}"
                except:
                    etd = f"{date_part}, {time_part}"
                # Move to next cutoff every 2 vessels (transshipment pairs)
                if i % 2 == 1:
                    cutoff_idx += 1

            # ETA - find the last date in each schedule row
            # Each row has about 4-5 dates, we want the last one (arrival)
            eta = None
            if date_matches:
                # Calculate which date group we're in
                row_num = i // 2  # 2 vessels per row
                base_date_idx = row_num * 5 + 4  # 5 dates per row, get the 5th (last)
                if base_date_idx < len(date_matches):
                    day, month, _ = date_matches[base_date_idx]
                    eta = f"{day} {month} 2026"
                elif len(date_matches) > 0:
                    # Fallback to last date
                    day, month, _ = date_matches[-1]
                    eta = f"{day} {month} 2026"

            schedules.append(Schedule(
                vessel=vessel_clean,
                voyage=voyage_clean,
                etd=etd,
                eta=eta,
                carrier=self.name
            ))

        return schedules



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
    full_text = '\n'.join(text_lines)
    schedules = []

    # If carrier hint provided, try that parser first
    if carrier_hint:
        for parser in PARSERS:
            if parser.name == carrier_hint or carrier_hint in parser.name:
                schedules = parser.parse(text_lines)
                if schedules:
                    break

    # Try each parser in order if no schedules yet
    if not schedules:
        for parser in PARSERS:
            if parser.can_parse(full_text):
                schedules = parser.parse(text_lines)
                if schedules:
                    break

    # Validate and fix dates (swap if ETD > ETA)
    for schedule in schedules:
        schedule.swap_dates_if_needed()

    return schedules
