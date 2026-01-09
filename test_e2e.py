"""
End-to-End Testing for Schedule Parser
Tests all functionality without modifying production code
"""
import os
import sys
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.parsers import parse_schedules, get_carrier_from_filename, detect_carrier
from formatters.output import format_table, format_email, save_output
from processors.ocr import OCRProcessor
from core.models import Schedule


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title):
    """Print formatted subsection"""
    print(f"\n--- {title} ---")


def test_screenshot_discovery():
    """Test 1: Check what screenshot files exist"""
    print_section("TEST 1: Screenshot Discovery")

    screenshots_dir = "C:\\Users\\giang\\Desktop\\SCHEDULE\\1_screenshots"

    if not os.path.exists(screenshots_dir):
        print(f"[ERROR] Screenshots directory not found: {screenshots_dir}")
        return []

    files = [f for f in os.listdir(screenshots_dir)
             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

    print(f"\n[INFO] Found {len(files)} screenshot file(s):")
    for i, f in enumerate(files, 1):
        carrier = get_carrier_from_filename(f)
        size = os.path.getsize(os.path.join(screenshots_dir, f))
        print(f"  {i}. {f}")
        print(f"     - Carrier from filename: {carrier or 'UNKNOWN'}")
        print(f"     - Size: {size:,} bytes")

    return files


def test_ocr_setup():
    """Test 2: Verify OCR is available"""
    print_section("TEST 2: OCR Setup Verification")

    ocr = OCRProcessor()

    if ocr.is_available():
        print(f"[OK] Tesseract OCR is installed and available")
    else:
        print(f"[ERROR] Tesseract OCR not available")
        print(f"     Please install Tesseract OCR")
        return False

    return True


def test_parse_screenshot(filename):
    """Test 3: Parse a screenshot and verify outputs"""
    print_section(f"TEST 3: Parsing Screenshot - {filename}")

    screenshots_dir = "C:\\Users\\giang\\Desktop\\SCHEDULE\\1_screenshots"
    filepath = os.path.join(screenshots_dir, filename)

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return None

    # Step 1: Extract carrier
    carrier = get_carrier_from_filename(filename)
    print(f"\n[STEP 1] Carrier from filename: {carrier or 'UNKNOWN'}")

    # Step 2: OCR Extraction
    print_subsection("STEP 2: OCR Text Extraction")
    ocr = OCRProcessor()
    text_lines = ocr.extract_text(filepath)

    if not text_lines:
        print("[ERROR] No text extracted from image")
        return None

    print(f"[OK] Extracted {len(text_lines)} lines of text")
    print("\n[SAMPLE TEXT - First 10 lines]:")
    for i, line in enumerate(text_lines[:10], 1):
        print(f"  {i:2}. {line}")

    # Step 3: Auto-detect carrier if not from filename
    if not carrier:
        print_subsection("STEP 3: Auto-Detect Carrier")
        carrier = detect_carrier('\n'.join(text_lines))
        print(f"[AUTO-DETECT] Carrier: {carrier or 'UNKNOWN'}")

    # Step 4: Parse schedules
    print_subsection("STEP 4: Schedule Parsing")
    schedules = parse_schedules(text_lines, carrier)

    if not schedules:
        print("[WARNING] No schedules parsed")
        return None

    print(f"[OK] Parsed {len(schedules)} schedule(s)")

    # Step 5: Format as table
    print_subsection("STEP 5: Table Format Output")
    table_output = format_table(schedules)
    print(table_output)

    # Step 6: Format as email
    print_subsection("STEP 6: Email Format Output")
    email_output = format_email(schedules)
    print(email_output)

    # Step 7: Save to file
    print_subsection("STEP 7: Save to File")
    output_dir = "C:\\Users\\giang\\Desktop\\SCHEDULE\\test_output"
    os.makedirs(output_dir, exist_ok=True)

    saved_path = save_output(schedules, output_dir, carrier)
    print(f"[OK] Saved to: {saved_path}")

    # Verify file was created
    if os.path.exists(saved_path):
        size = os.path.getsize(saved_path)
        print(f"[OK] File verified ({size} bytes)")
    else:
        print(f"[ERROR] File not created")

    return {
        'filename': filename,
        'carrier': carrier,
        'text_lines': len(text_lines),
        'schedules': schedules,
        'saved_path': saved_path
    }


def test_edge_cases():
    """Test 4: Edge cases"""
    print_section("TEST 4: Edge Case Testing")

    # Test 4a: Invalid image path
    print_subsection("4a: Invalid Image Path")
    ocr = OCRProcessor()
    text = ocr.extract_text("C:\\nonexistent\\image.png")
    if text == []:
        print("[OK] Returns empty list for invalid path")
    else:
        print(f"[UNEXPECTED] Returned: {text}")

    # Test 4b: Empty text lines
    print_subsection("4b: Empty Text Lines")
    schedules = parse_schedules([], carrier_hint="MAERSK")
    if schedules == []:
        print("[OK] Returns empty list for empty text")
    else:
        print(f"[UNEXPECTED] Returned: {schedules}")

    # Test 4c: Garbage text
    print_subsection("4c: Garbage Text Input")
    garbage = ["asdfghjkl", "12345", "!@#$%^&*()"]
    schedules = parse_schedules(garbage)
    if schedules == []:
        print("[OK] Returns empty list for garbage text")
    else:
        print(f"[UNEXPECTED] Returned: {schedules}")

    # Test 4d: Format functions with empty list
    print_subsection("4d: Format Functions with Empty Data")
    empty_table = format_table([])
    print(f"[OK] format_table([]) returns:\n{empty_table}")

    empty_email = format_email([])
    print(f"[OK] format_email([]) returns: '{empty_email}'")


def generate_summary_report(results):
    """Generate final summary report"""
    print_section("FINAL TEST SUMMARY")

    total_schedules = sum(len(r['schedules']) for r in results if r)

    print(f"\n[STATISTICS]")
    print(f"  Total screenshots tested: {len(results)}")
    print(f"  Successful parses: {sum(1 for r in results if r and r['schedules'])}")
    print(f"  Total schedules parsed: {total_schedules}")

    print(f"\n[BREAKDOWN BY CARRIER]")
    carrier_counts = {}
    for r in results:
        if r and r['schedules']:
            carrier = r['carrier'] or 'UNKNOWN'
            carrier_counts[carrier] = carrier_counts.get(carrier, 0) + len(r['schedules'])

    for carrier, count in sorted(carrier_counts.items()):
        print(f"  {carrier:15} : {count} schedule(s)")

    print(f"\n[FILES GENERATED]")
    for r in results:
        if r and r.get('saved_path'):
            print(f"  - {r['saved_path']}")

    print(f"\n[SUGGESTIONS FOR IMPROVEMENT]")
    suggestions = []

    # Check for failed parses
    failed = sum(1 for r in results if r is None or not r.get('schedules'))
    if failed > 0:
        suggestions.append(f"- {failed} screenshot(s) failed to parse - review OCR quality")

    # Check carrier detection
    unknown = sum(1 for r in results if r and r['carrier'] is None)
    if unknown > 0:
        suggestions.append(f"- {unknown} file(s) without carrier detection - use filename prefixes")

    # General suggestions
    suggestions.append("- Add more carrier-specific parsers for better accuracy")
    suggestions.append("- Implement confidence scoring for parsed data")
    suggestions.append("- Add validation for date formats")
    suggestions.append("- Consider adding unit tests for parser functions")

    for s in suggestions:
        print(f"  {s}")


def main():
    """Run all tests"""
    print("=" * 70)
    print("  SCHEDULE PARSER - END-TO-END TESTING")
    print("  Test Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    # Test 1: Discover screenshots
    screenshot_files = test_screenshot_discovery()

    if not screenshot_files:
        print("\n[ABORT] No screenshot files found to test")
        return

    # Test 2: Verify OCR
    if not test_ocr_setup():
        print("\n[ABORT] OCR not available")
        return

    # Test 3: Parse each screenshot
    results = []
    for filename in screenshot_files:
        result = test_parse_screenshot(filename)
        results.append(result)

    # Test 4: Edge cases
    test_edge_cases()

    # Generate summary
    generate_summary_report([r for r in results if r])

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
