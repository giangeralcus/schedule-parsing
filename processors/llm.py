"""
LLM-based schedule extraction using Ollama (Qwen2.5)

This module provides a fallback parser when regex-based parsing fails.
Uses local LLM via Ollama for structured data extraction from OCR text.
"""
import json
import re
from typing import List, Optional, Dict, Any

# Import logger
try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Check for Ollama
HAS_OLLAMA = False
ollama = None

try:
    import ollama as _ollama
    ollama = _ollama
    HAS_OLLAMA = True
except ImportError:
    logger.warning("Ollama not installed. Run: pip install ollama")


class LLMProcessor:
    """
    LLM-based schedule extraction using Qwen2.5 via Ollama

    Usage:
        llm = LLMProcessor()
        if llm.is_available():
            schedules = llm.extract_schedules(ocr_text_lines)
    """

    # Default model - Qwen2.5 7B is excellent for structured extraction
    DEFAULT_MODEL = "qwen2.5:7b"

    # Extraction prompt template
    EXTRACTION_PROMPT = """Extract shipping schedule from this OCR text. Return JSON array.

TEXT:
{ocr_text}

RULES:
- Voyage: 3-4 digits + letter (e.g., 603N, 089S)
- Dates: format as "DD Mon YYYY"
- Fix typos: "Febi"->"Feb", "Jani"->"Jan"

OUTPUT FORMAT (use EXACT field names):
[{{"vessel": "NAME", "voyage": "603N", "etd": "18 Jan 2026", "eta": "27 Jan 2026"}}]

JSON:"""

    def __init__(self, model: str = None, timeout: int = 60):
        """
        Initialize LLM processor

        Args:
            model: Ollama model name (default: qwen2.5:7b)
            timeout: Request timeout in seconds
        """
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self.has_ollama = HAS_OLLAMA
        self._model_verified = False

    def is_available(self) -> bool:
        """Check if LLM is available and model is loaded"""
        if not self.has_ollama:
            return False

        # Verify model is available (only check once)
        if not self._model_verified:
            try:
                models = ollama.list()
                model_names = [m.model for m in models.models]
                # Check if our model (or base name) is in the list
                base_model = self.model.split(':')[0]
                self._model_verified = any(
                    self.model in name or base_model in name
                    for name in model_names
                )
                if not self._model_verified:
                    logger.warning(f"Model {self.model} not found. Run: ollama pull {self.model}")
            except Exception as e:
                logger.error(f"Failed to check Ollama models: {e}")
                return False

        return self._model_verified

    def extract_schedules(self, text_lines: List[str], carrier: str = None) -> List[Dict]:
        """
        Extract schedules from OCR text using LLM

        Args:
            text_lines: List of OCR text lines
            carrier: Optional carrier hint

        Returns:
            List of schedule dicts with vessel, voyage, etd, eta
        """
        if not self.is_available():
            logger.warning("LLM not available for extraction")
            return []

        # Combine text lines
        ocr_text = '\n'.join(text_lines)

        # Add carrier context if available
        if carrier:
            ocr_text = f"[CARRIER: {carrier}]\n{ocr_text}"

        # Build prompt
        prompt = self.EXTRACTION_PROMPT.format(ocr_text=ocr_text)

        try:
            logger.info(f"Sending {len(text_lines)} lines to LLM ({self.model})")

            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "num_predict": 1024,  # Limit output length
                }
            )

            # Extract response text
            response_text = response.message.content.strip()
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON from response
            schedules = self._parse_json_response(response_text)

            if schedules:
                logger.info(f"LLM extracted {len(schedules)} schedules")
                # Validate and clean each schedule
                schedules = [self._clean_schedule(s) for s in schedules if self._is_valid_schedule(s)]

            return schedules

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []

    def _parse_json_response(self, response: str) -> List[Dict]:
        """Parse JSON from LLM response, handling markdown code blocks"""
        # Try to find JSON array in response
        # Handle ```json ... ``` blocks
        json_match = re.search(r'```(?:json)?\s*([\[\{].*?[\]\}])\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)

        # Try to find raw JSON array
        array_match = re.search(r'\[.*\]', response, re.DOTALL)
        if array_match:
            response = array_match.group(0)

        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return []

    def _normalize_field_names(self, schedule: Dict) -> Dict:
        """Normalize field names from various LLM output formats"""
        # Map alternative field names to standard names
        field_maps = {
            'vessel': ['vessel', 'vessel_name', 'ship', 'ship_name', 'name'],
            'voyage': ['voyage', 'voyage_number', 'voyage_no', 'voy', 'voyage_ref'],
            'etd': ['etd', 'departure_date', 'departure', 'dep_date', 'sailing_date'],
            'eta': ['eta', 'arrival_date', 'arrival', 'arr_date', 'eta_date'],
        }

        normalized = {}
        for std_name, alternatives in field_maps.items():
            for alt in alternatives:
                if alt in schedule and schedule[alt]:
                    normalized[std_name] = schedule[alt]
                    break
            if std_name not in normalized:
                normalized[std_name] = ''

        return normalized

    def _is_valid_schedule(self, schedule: Dict) -> bool:
        """Check if schedule dict has minimum required fields"""
        if not isinstance(schedule, dict):
            return False

        # Normalize field names first
        schedule = self._normalize_field_names(schedule)

        vessel = schedule.get('vessel', '').strip()
        etd = schedule.get('etd', '').strip()
        eta = schedule.get('eta', '').strip()

        # Must have vessel and at least one date
        has_vessel = vessel and vessel.upper() not in ('TBA', 'UNKNOWN', 'N/A', '')
        has_date = (etd and etd.upper() not in ('TBA', 'UNKNOWN', 'N/A', '')) or \
                   (eta and eta.upper() not in ('TBA', 'UNKNOWN', 'N/A', ''))

        return has_vessel and has_date

    def _clean_schedule(self, schedule: Dict) -> Dict:
        """Clean and normalize schedule fields"""
        # Normalize field names first
        schedule = self._normalize_field_names(schedule)

        return {
            'vessel': self._clean_vessel(schedule.get('vessel', '')),
            'voyage': self._clean_voyage(schedule.get('voyage', '')),
            'etd': self._clean_date(schedule.get('etd', '')),
            'eta': self._clean_date(schedule.get('eta', '')),
        }

    def _clean_vessel(self, name: str) -> str:
        """Clean vessel name"""
        if not name:
            return 'TBA'
        name = name.strip().upper()
        # Add space between letters and numbers
        name = re.sub(r'([A-Z])(\d)', r'\1 \2', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def _clean_voyage(self, voyage: str) -> str:
        """Clean voyage number"""
        if not voyage:
            return '-'
        voyage = voyage.strip().upper()
        # Remove any non-alphanumeric except common suffixes
        voyage = re.sub(r'[^A-Z0-9]', '', voyage)
        return voyage if voyage else '-'

    def _clean_date(self, date_str: str) -> str:
        """Clean and normalize date string"""
        if not date_str:
            return 'TBA'

        date_str = date_str.strip()

        # Fix common OCR month errors
        month_fixes = {
            'Febi': 'Feb', 'Jani': 'Jan', 'Mari': 'Mar', 'Apri': 'Apr',
            'Juni': 'Jun', 'Juli': 'Jul', 'Augi': 'Aug', 'Sepi': 'Sep',
            'Octi': 'Oct', 'Novi': 'Nov', 'Deci': 'Dec'
        }
        for wrong, correct in month_fixes.items():
            date_str = date_str.replace(wrong, correct)

        # Normalize spacing
        date_str = re.sub(r'(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
                         r'\1 \2', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{4})',
                         r'\1 \2', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'\s+', ' ', date_str).strip()

        return date_str if date_str else 'TBA'

    def extract_single_field(self, text: str, field: str) -> Optional[str]:
        """
        Extract a single field from text using LLM

        Useful for specific extractions like vessel name correction.

        Args:
            text: Input text
            field: Field to extract (vessel, voyage, date)

        Returns:
            Extracted value or None
        """
        if not self.is_available():
            return None

        prompts = {
            'vessel': f"Extract the vessel name from this text. Return ONLY the vessel name, nothing else.\nText: {text}\nVessel:",
            'voyage': f"Extract the voyage number from this text. Return ONLY the voyage number (e.g., 603N), nothing else.\nText: {text}\nVoyage:",
            'date': f"Extract and format the date from this text as 'DD Mon YYYY'. Return ONLY the date, nothing else.\nText: {text}\nDate:",
        }

        prompt = prompts.get(field)
        if not prompt:
            return None

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 50}
            )
            return response.message.content.strip()
        except Exception as e:
            logger.error(f"Single field extraction failed: {e}")
            return None


def get_llm_processor(model: str = None) -> LLMProcessor:
    """Factory function to get LLM processor instance"""
    return LLMProcessor(model=model)
