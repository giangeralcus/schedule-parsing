"""
Output formatting for schedules
"""
import os
from datetime import datetime
from typing import List, Optional

# Try to import pyperclip for clipboard
HAS_CLIPBOARD = False
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    pass


def _get_attr(obj, name: str, default: str = 'TBA') -> str:
    """Get attribute from object (works with dataclass or dict)"""
    if hasattr(obj, name):
        return getattr(obj, name, default) or default
    elif isinstance(obj, dict):
        return obj.get(name, default) or default
    return default


def format_table(schedules: List) -> str:
    """Format schedules as ASCII table"""
    lines = ["+" + "-" * 68 + "+"]
    lines.append(f"|{'VESSEL':<18}|{'VOYAGE':<8}|{'ETD':<20}|{'ETA':<18}|")
    lines.append("+" + "-" * 68 + "+")

    for s in schedules:
        vessel = _get_attr(s, 'vessel')
        voyage = _get_attr(s, 'voyage')
        etd = _get_attr(s, 'etd')
        eta = _get_attr(s, 'eta')

        v = vessel[:16]
        voy = voyage[:6]
        etd_str = etd[:18]
        eta_str = eta[:16]
        lines.append(f"|{v:<18}|{voy:<8}|{etd_str:<20}|{eta_str:<18}|")

    lines.append("+" + "-" * 68 + "+")
    return '\n'.join(lines)


def format_email(schedules: List) -> str:
    """Format schedules for email"""
    lines = []

    if len(schedules) == 1:
        s = schedules[0]
        lines.extend([
            f"Vessel  : {_get_attr(s, 'vessel')}",
            f"Voyage  : {_get_attr(s, 'voyage')}",
            f"ETD     : {_get_attr(s, 'etd')}",
            f"ETA     : {_get_attr(s, 'eta')}",
        ])
    else:
        for i, s in enumerate(schedules, 1):
            lines.extend([
                f"Option {i}:",
                f"  Vessel  : {_get_attr(s, 'vessel')}",
                f"  Voyage  : {_get_attr(s, 'voyage')}",
                f"  ETD     : {_get_attr(s, 'etd')}",
                f"  ETA     : {_get_attr(s, 'eta')}",
                "",
            ])

    return '\n'.join(lines)


def save_output(schedules: List, output_dir: str, carrier: Optional[str] = None) -> str:
    """
    Save schedules to output file

    Args:
        schedules: List of Schedule objects
        output_dir: Base output directory
        carrier: Optional carrier name for subfolder

    Returns:
        Path to saved file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    if carrier:
        carrier_dir = os.path.join(output_dir, carrier)
        os.makedirs(carrier_dir, exist_ok=True)
        filename = f"{timestamp}.txt"
        filepath = os.path.join(carrier_dir, filename)
    else:
        filename = f"SCHEDULE_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        if carrier:
            f.write(f"Carrier: {carrier}\n")
            f.write("-" * 40 + "\n")
        f.write(format_email(schedules))

    return filepath


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard"""
    if HAS_CLIPBOARD:
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            pass
    return False
