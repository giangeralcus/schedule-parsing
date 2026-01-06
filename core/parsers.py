"""
Carrier-specific schedule parsers
"""
import re
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .models import Schedule, ParseResult
from .config import CARRIER_MAP, VESSEL_DB


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
        """Normalize vessel name using database"""
        name = name.strip()
        # Add space between letters and numbers
        name = re.sub(r'([A-Z])(\d)', r'\1 \2', name)
        name = re.sub(r'\s+', ' ', name).strip()

        # Check vessel database
        name_key = name.upper().replace('.', '').replace('-', ' ')
        for key, value in VESSEL_DB.items():
            if key.replace('-', ' ').replace('.', '') in name_key:
                return value
        return name


class MaerskParser(CarrierParser):
    """Parser for Maersk format: VESSEL / VOYAGE with datetime"""

    name = "MAERSK"

    # Pattern: "SPIL NISAKA / 602N"
    VESSEL_PATTERN = r'([A-Za-z][A-Za-z\s\.\-]{2,25}?)\s*/\s*(\d{3,4}[A-Z]?)'

    # Pattern: "16 Jan 2026, 19:00"
    DATE_PATTERN = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})[,\s]+(\d{1,2}:\d{2})'

    def can_parse(self, text: str) -> bool:
        return bool(re.search(self.VESSEL_PATTERN, text))

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        full_text = '\n'.join(text_lines)
        schedules = []

        # Find vessels with voyage numbers
        vessel_matches = re.findall(self.VESSEL_PATTERN, full_text)

        vessels = {}
        for v, voyage in vessel_matches:
            voyage = voyage.strip().upper()
            v = self.normalize_vessel(v)
            if len(v) >= 3 and voyage[-1:].isalpha() and voyage not in vessels:
                vessels[voyage] = v

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
    """Parser for CMA/CNC format: Vessel NAME + weekday dates"""

    name = "CMA-CGM"

    # Pattern: "Vessel DANUM 175 CO2..."
    VESSEL_PATTERN = r'Vessel\s+([A-Z][A-Z0-9\s]{2,20}?)(?:\s+CO2|\s*$)'

    # Pattern: "Sunday, 11-Jan-2026"
    DATE_PATTERN = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]+(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4})'

    def can_parse(self, text: str) -> bool:
        has_vessel = bool(re.search(self.VESSEL_PATTERN, text, re.IGNORECASE))
        has_weekday = bool(re.search(self.DATE_PATTERN, text, re.IGNORECASE))
        return has_vessel and has_weekday

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        full_text = '\n'.join(text_lines)
        schedules = []

        # Find vessels
        vessel_matches = re.findall(self.VESSEL_PATTERN, full_text, re.IGNORECASE)

        # Find weekday dates
        date_matches = re.findall(self.DATE_PATTERN, full_text, re.IGNORECASE)

        # Pair vessels with dates
        seen = set()
        for i, vessel in enumerate(vessel_matches):
            vessel = self.normalize_vessel(vessel)

            etd_idx = i * 2
            eta_idx = i * 2 + 1

            etd = date_matches[etd_idx].replace('-', ' ') if etd_idx < len(date_matches) else None
            eta = date_matches[eta_idx].replace('-', ' ') if eta_idx < len(date_matches) else None

            if not etd:
                continue

            # Deduplicate
            key = f"{vessel}|{etd}"
            if key in seen:
                continue
            seen.add(key)

            schedules.append(Schedule(
                vessel=vessel,
                voyage="-",
                etd=etd,
                eta=eta,
                carrier=self.name
            ))

        return schedules


class OOCLParser(CarrierParser):
    """Parser for OOCL format: Location + event with times"""

    name = "OOCL"

    # Pattern: "7 Jan 23:00 -> Location"
    EVENT_PATTERN = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(\d{1,2}:\d{2})\s*(.*)'

    def can_parse(self, text: str) -> bool:
        return 'oocl' in text.lower() or 'cy cut-off' in text.lower()

    def parse(self, text_lines: List[str]) -> List[Schedule]:
        # OOCL format is complex, use simplified extraction
        full_text = '\n'.join(text_lines)
        schedules = []

        # Try to find vessel names
        vessel_pattern = r'([A-Z][A-Z\s\.\-]{3,20})\s+\d{3,4}[A-Z]?'
        vessel_matches = re.findall(vessel_pattern, full_text)

        # Find dates
        date_pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)[,\s]+(\d{1,2}:\d{2})'
        date_matches = re.findall(date_pattern, full_text, re.IGNORECASE)

        if vessel_matches and date_matches:
            for i, vessel in enumerate(vessel_matches):
                etd_idx = i * 2
                eta_idx = i * 2 + 1

                etd = f"{date_matches[etd_idx][0]}, {date_matches[etd_idx][1]}" if etd_idx < len(date_matches) else None
                eta = f"{date_matches[eta_idx][0]}, {date_matches[eta_idx][1]}" if eta_idx < len(date_matches) else None

                schedules.append(Schedule(
                    vessel=self.normalize_vessel(vessel),
                    voyage="-",
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

    # If carrier hint provided, try that parser first
    if carrier_hint:
        for parser in PARSERS:
            if parser.name == carrier_hint or carrier_hint in parser.name:
                schedules = parser.parse(text_lines)
                if schedules:
                    return schedules

    # Try each parser in order
    for parser in PARSERS:
        if parser.can_parse(full_text):
            schedules = parser.parse(text_lines)
            if schedules:
                return schedules

    return []
