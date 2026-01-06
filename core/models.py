"""
Data models for schedule parsing
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import re


@dataclass
class Schedule:
    """Represents a single shipping schedule"""
    vessel: str = "TBA"
    voyage: str = "TBA"
    etd: Optional[str] = None
    eta: Optional[str] = None
    carrier: Optional[str] = None
    confidence: float = 1.0

    def __post_init__(self):
        # Normalize vessel name
        if self.vessel:
            self.vessel = self._normalize_vessel(self.vessel)

        # Set defaults
        if not self.etd:
            self.etd = "TBA"
        if not self.eta:
            self.eta = "TBA"

    def _normalize_vessel(self, name: str) -> str:
        """Normalize vessel name"""
        # Add space between letters and numbers: "DANUM175" -> "DANUM 175"
        name = re.sub(r'([A-Z])(\d)', r'\1 \2', name)
        # Clean up multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def is_valid(self) -> bool:
        """Check if schedule has minimum required data"""
        return (
            self.vessel and self.vessel != "TBA" and
            (self.etd and self.etd != "TBA" or self.eta and self.eta != "TBA")
        )

    def __str__(self) -> str:
        return f"{self.vessel} / {self.voyage}"


@dataclass
class ParseResult:
    """Result of parsing an image"""
    schedules: List[Schedule] = field(default_factory=list)
    carrier: Optional[str] = None
    source_file: Optional[str] = None
    raw_text: List[str] = field(default_factory=list)
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)

    def has_schedules(self) -> bool:
        return len(self.schedules) > 0

    def valid_schedules(self) -> List[Schedule]:
        return [s for s in self.schedules if s.is_valid()]
