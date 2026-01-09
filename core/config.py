"""
Configuration and constants
"""
import os

# Paths
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(SCRIPT_DIR, "1_screenshots")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "2_hasil")

# Default browse location for file dialog (Windows Screenshots folder)
DEFAULT_BROWSE_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")

# Create folders
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Carrier prefix mapping
CARRIER_MAP = {
    'm': 'MAERSK',
    'o': 'OOCL',
    'c': 'CMA-CGM',
    'h': 'HAPAG-LLOYD',
    'e': 'EVERGREEN',
    'n': 'ONE',
    'y': 'YANG-MING',
    's': 'MSC',
    'z': 'ZIM',
    'w': 'WAN-HAI',
    'p': 'PIL',
    'x': 'OTHER',
}

# Vessel name corrections (OCR fixes)
VESSEL_DB = {
    'SPILNISAKA': 'SPIL NISAKA',
    'SPIL NISAKA': 'SPIL NISAKA',
    'JULIUS S': 'JULIUS-S.',
    'JULIUS-S': 'JULIUS-S.',
    'JULTUS': 'JULIUS-S.',
    'SKY PEACE': 'SKY PEACE',
    'SKYPEACE': 'SKY PEACE',
    'MARTIN SCHULTE': 'MARTIN SCHULTE',
    'MARTINSCHULTE': 'MARTIN SCHULTE',
    'COSCO ISTANBUL': 'COSCO ISTANBUL',
    'COSCOISTANBUL': 'COSCO ISTANBUL',
    'DANUM175': 'DANUM 175',
    'DANUM 175': 'DANUM 175',
    'CNC JUPITER': 'CNC JUPITER',
    'CNCJUPITER': 'CNC JUPITER',
}

# OCR settings
OCR_MIN_WIDTH = 1500
OCR_PSM_MODES = [6, 11, 4]
OCR_CONFIDENCE_THRESHOLD = 30

# Tesseract paths
TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'/usr/bin/tesseract',
    r'/opt/homebrew/bin/tesseract',  # macOS Apple Silicon (Homebrew)
    r'/usr/local/bin/tesseract',     # macOS Intel (Homebrew)
]


class Config:
    """Runtime configuration"""
    def __init__(self):
        self.screenshots_dir = SCREENSHOTS_DIR
        self.output_dir = OUTPUT_DIR
        self.carrier_map = CARRIER_MAP
        self.vessel_db = VESSEL_DB
