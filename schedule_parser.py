"""
SCHEDULE PARSER - Offline Edition v3.0
======================================
Parse shipping schedules from screenshots (Multi-carrier support)
100% Offline - No internet required

Folder Structure:
  SCHEDULE/
  ├── 1_screenshots/   <- [1] Drop your screenshots here
  ├── 2_hasil/         <- [2] Parsed results (by carrier)
  ├── core/            <- Parser logic
  ├── processors/      <- OCR processing
  ├── formatters/      <- Output formatting
  └── schedule_parser.py

Usage:
  python schedule_parser.py              # Interactive menu
  python schedule_parser.py --watch      # Watch folder for new files
  python schedule_parser.py --manual     # Manual entry mode
"""

import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import SCREENSHOTS_DIR, OUTPUT_DIR, CARRIER_MAP
from core.parsers import parse_schedules, get_carrier_from_filename, detect_carrier
from core.models import Schedule
from processors.ocr import OCRProcessor
from formatters.output import format_table, format_email, save_output, copy_to_clipboard


# ============================================================
# CLI INTERFACE
# ============================================================

def show_menu():
    """Display interactive menu"""
    print("\n" + "=" * 55)
    print("  SCHEDULE PARSER v3.0 - Offline Edition")
    print("=" * 55)

    # Get image list
    images = get_image_list()

    # Show files with carrier detection
    if images:
        print("\nSelect file to process:")
        for i, img in enumerate(images, 1):
            carrier = get_carrier_from_filename(img)
            tag = f"[{carrier}]" if carrier else "[?]"
            print(f"  {i}. {tag} {img}")
    else:
        print(f"\n[!] No images in 1_screenshots/")
        print(f"    Drop screenshots here: {SCREENSHOTS_DIR}")

    print("\n" + "-" * 55)
    print("Commands: [A]ll  [E]dit  [W]atch  [M]anual  [Q]uit")
    print("Prefix:   m_=Maersk o_=OOCL c_=CMA h_=Hapag s_=MSC...")

    return input("\nChoice: ").strip()


def get_image_list():
    """Get list of image files in screenshots folder"""
    if not os.path.exists(SCREENSHOTS_DIR):
        return []
    return [f for f in os.listdir(SCREENSHOTS_DIR)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]


# ============================================================
# PROCESSING
# ============================================================

def process_image(image_path: str, edit_mode: bool = False, save: bool = True):
    """Process a single image file"""
    if not os.path.exists(image_path):
        print(f"[!] File not found: {image_path}")
        return None

    filename = os.path.basename(image_path)
    carrier = get_carrier_from_filename(filename)

    print(f"\n[*] Processing: {filename}")
    if carrier:
        print(f"[*] Carrier: {carrier}")

    # Initialize OCR
    ocr = OCRProcessor()
    if not ocr.is_available():
        print("[!] Tesseract OCR not installed")
        return None

    # Extract text
    text_lines = ocr.extract_text(image_path)
    if not text_lines:
        print("[!] No text extracted from image")
        return None

    # Auto-detect carrier if not from filename
    if not carrier:
        carrier = detect_carrier('\n'.join(text_lines))
        if carrier:
            print(f"[*] Auto-detected carrier: {carrier}")

    # Parse schedules
    schedules = parse_schedules(text_lines, carrier)
    print(f"[*] Found {len(schedules)} schedule(s)")

    if not schedules:
        print("[!] No schedules found. Try Edit mode or Manual entry.")
        return None

    # Edit mode - allow corrections
    if edit_mode:
        schedules = edit_schedules(schedules)

    # Display results
    print("\n" + format_table(schedules))
    email_text = format_email(schedules)
    print("\n[EMAIL FORMAT]")
    print("-" * 40)
    print(email_text)
    print("-" * 40)

    # Save output
    if save:
        saved_path = save_output(schedules, OUTPUT_DIR, carrier)
        rel_path = os.path.relpath(saved_path, os.path.dirname(OUTPUT_DIR))
        print(f"\n[*] Saved: {rel_path}")

    # Copy to clipboard
    if copy_to_clipboard(email_text):
        print("[*] Copied to clipboard!")

    return schedules


def process_folder(edit_mode: bool = False):
    """Process all images in screenshots folder"""
    images = get_image_list()

    if not images:
        print(f"\n[!] No images in 1_screenshots/")
        print(f"    Drop your screenshots here: {SCREENSHOTS_DIR}")
        return

    print(f"\n[*] Found {len(images)} image(s)")

    for i, img in enumerate(images, 1):
        print(f"\n{'=' * 55}")
        print(f"  [{i}/{len(images)}] {img}")
        print('=' * 55)

        image_path = os.path.join(SCREENSHOTS_DIR, img)
        process_image(image_path, edit_mode=edit_mode)

        if i < len(images):
            cont = input("\nProcess next? [Y/n]: ").strip().lower()
            if cont == 'n':
                break


def watch_folder():
    """Watch screenshots folder for new files"""
    print(f"\n[*] Watching: {SCREENSHOTS_DIR}")
    print("[*] Drop screenshots to auto-process")
    print("[*] Press Ctrl+C to stop\n")

    processed = set(os.listdir(SCREENSHOTS_DIR)) if os.path.exists(SCREENSHOTS_DIR) else set()

    try:
        while True:
            if os.path.exists(SCREENSHOTS_DIR):
                current = set(os.listdir(SCREENSHOTS_DIR))
                new_files = current - processed

                for f in new_files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        print(f"\n[+] New file: {f}")
                        process_image(os.path.join(SCREENSHOTS_DIR, f))

                processed = current
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopped watching")


# ============================================================
# MANUAL ENTRY
# ============================================================

def manual_entry():
    """Manual schedule entry"""
    print("\n" + "=" * 55)
    print("  MANUAL ENTRY")
    print("=" * 55)
    print("\nFormat: VESSEL / VOYAGE / ETD / ETA")
    print("Example: SPIL NISAKA / 602N / 16 Jan 19:00 / 24 Jan 22:00")
    print("Enter blank line to finish.\n")

    schedules = []
    while True:
        line = input("> ").strip()
        if not line:
            break

        parts = [p.strip() for p in line.split('/')]
        if len(parts) >= 4:
            schedules.append(Schedule(
                vessel=parts[0],
                voyage=parts[1],
                etd=parts[2],
                eta=parts[3],
            ))
            print(f"  + Added: {parts[0]} / {parts[1]}")
        elif len(parts) == 3:
            schedules.append(Schedule(
                vessel=parts[0],
                voyage=parts[1],
                etd=parts[2],
            ))
            print(f"  + Added: {parts[0]} / {parts[1]}")
        else:
            print("  ! Invalid format. Use: VESSEL / VOYAGE / ETD / ETA")

    return schedules


def edit_schedules(schedules):
    """Edit parsed schedules"""
    print("\n" + "=" * 55)
    print("  EDIT MODE - Press Enter to keep current value")
    print("=" * 55)

    edited = []
    for i, s in enumerate(schedules):
        print(f"\n--- Option {i+1} ---")

        vessel = getattr(s, 'vessel', s.get('vessel', '')) if hasattr(s, 'vessel') else s.get('vessel', '')
        voyage = getattr(s, 'voyage', s.get('voyage', '')) if hasattr(s, 'voyage') else s.get('voyage', '')
        etd = getattr(s, 'etd', s.get('etd', '')) if hasattr(s, 'etd') else s.get('etd', '')
        eta = getattr(s, 'eta', s.get('eta', '')) if hasattr(s, 'eta') else s.get('eta', '')

        new_vessel = input(f"Vessel [{vessel}]: ").strip() or vessel
        new_voyage = input(f"Voyage [{voyage}]: ").strip() or voyage
        new_etd = input(f"ETD    [{etd}]: ").strip() or etd
        new_eta = input(f"ETA    [{eta}]: ").strip() or eta

        edited.append(Schedule(
            vessel=new_vessel,
            voyage=new_voyage,
            etd=new_etd,
            eta=new_eta,
        ))

    # Option to add more
    print("\nAdd more? (Format: VESSEL / VOYAGE / ETD / ETA, blank to finish)")
    while True:
        line = input("> ").strip()
        if not line:
            break
        parts = [p.strip() for p in line.split('/')]
        if len(parts) >= 4:
            edited.append(Schedule(
                vessel=parts[0],
                voyage=parts[1],
                etd=parts[2],
                eta=parts[3],
            ))
            print(f"  + Added: {parts[0]}")

    return edited


# ============================================================
# MAIN
# ============================================================

def main():
    """Main entry point"""
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    manual = '--manual' in sys.argv or '-m' in sys.argv
    edit = '--edit' in sys.argv or '-e' in sys.argv
    watch = '--watch' in sys.argv or '-w' in sys.argv

    # Manual mode
    if manual:
        schedules = manual_entry()
        if schedules:
            print("\n" + format_table(schedules))
            email_text = format_email(schedules)
            print("\n[EMAIL FORMAT]")
            print("-" * 40)
            print(email_text)
            print("-" * 40)
            if copy_to_clipboard(email_text):
                print("\n[*] Copied to clipboard!")
        return

    # Watch mode
    if watch:
        watch_folder()
        return

    # Process specific file
    if args:
        filepath = args[0]
        if not os.path.isabs(filepath):
            if os.path.exists(os.path.join(SCREENSHOTS_DIR, filepath)):
                filepath = os.path.join(SCREENSHOTS_DIR, filepath)
        process_image(filepath, edit_mode=edit)
        return

    # Interactive menu
    while True:
        choice = show_menu().lower()

        if choice in ['a', 'all']:
            process_folder(edit_mode=False)
        elif choice in ['e', 'edit']:
            process_folder(edit_mode=True)
        elif choice in ['w', 'watch']:
            watch_folder()
        elif choice in ['m', 'manual']:
            schedules = manual_entry()
            if schedules:
                print("\n" + format_table(schedules))
                email_text = format_email(schedules)
                print("\n" + email_text)
                copy_to_clipboard(email_text)
        elif choice in ['q', 'quit', 'exit']:
            break
        elif choice.isdigit():
            images = get_image_list()
            idx = int(choice) - 1
            if 0 <= idx < len(images):
                process_image(
                    os.path.join(SCREENSHOTS_DIR, images[idx]),
                    edit_mode=edit
                )
            else:
                print(f"[!] Invalid number. Enter 1-{len(images)}")
                continue
        else:
            print("[!] Invalid choice")
            continue

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
