"""
Test script for output formatting functions
DO NOT COMMIT - TEMPORARY TEST FILE
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.models import Schedule
from formatters.output import (
    format_table,
    format_email,
    save_output,
    copy_to_clipboard,
    HAS_CLIPBOARD
)


def create_sample_schedules():
    """Create sample Schedule objects for testing"""
    schedules = [
        Schedule(
            vessel="MAERSK OSLO",
            voyage="425N",
            etd="15 JAN 2026",
            eta="25 JAN 2026",
            carrier="MAERSK",
            confidence=0.95
        ),
        Schedule(
            vessel="MSC PARIS",
            voyage="301S",
            etd="18 JAN 2026",
            eta="28 JAN 2026",
            carrier="MSC",
            confidence=0.90
        ),
        Schedule(
            vessel="COSCO SHANGHAI",
            voyage="102E",
            etd="20 JAN 2026",
            eta="30 JAN 2026",
            carrier="COSCO",
            confidence=0.88
        )
    ]
    return schedules


def test_format_table():
    """Test format_table() function"""
    print("=" * 70)
    print("TEST 1: format_table() - Multiple Schedules")
    print("=" * 70)

    schedules = create_sample_schedules()
    result = format_table(schedules)

    print(result)
    print()

    # Verify structure
    lines = result.split('\n')
    # Should be: top border + header + separator + 3 data rows + bottom border = 7 lines
    assert len(lines) == 7, f"Expected 7 lines, got {len(lines)}"
    assert lines[0].startswith('+'), "First line should be border"
    assert lines[-1].startswith('+'), "Last line should be border"
    assert 'VESSEL' in lines[1], "Header should contain VESSEL"
    assert 'VOYAGE' in lines[1], "Header should contain VOYAGE"
    assert 'ETD' in lines[1], "Header should contain ETD"
    assert 'ETA' in lines[1], "Header should contain ETA"

    print("[PASS] format_table() - Multiple schedules test PASSED")
    print()


def test_format_table_single():
    """Test format_table() with single schedule"""
    print("=" * 70)
    print("TEST 2: format_table() - Single Schedule")
    print("=" * 70)

    schedules = [create_sample_schedules()[0]]
    result = format_table(schedules)

    print(result)
    print()

    lines = result.split('\n')
    # Should be: top border + header + separator + 1 data row + bottom border = 5 lines
    assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}"

    print("[PASS] format_table() - Single schedule test PASSED")
    print()


def test_format_table_with_tba():
    """Test format_table() with TBA values"""
    print("=" * 70)
    print("TEST 3: format_table() - With TBA Values")
    print("=" * 70)

    schedules = [
        Schedule(vessel="TEST VESSEL", voyage="TBA"),
        Schedule(vessel="ANOTHER VESSEL", etd="TBA", eta="TBA")
    ]
    result = format_table(schedules)

    print(result)
    print()

    assert 'TBA' in result, "Result should contain TBA"

    print("[PASS] format_table() - TBA values test PASSED")
    print()


def test_format_email_multiple():
    """Test format_email() with multiple schedules"""
    print("=" * 70)
    print("TEST 4: format_email() - Multiple Schedules")
    print("=" * 70)

    schedules = create_sample_schedules()
    result = format_email(schedules)

    print(result)
    print()

    # Verify structure
    assert 'Option 1:' in result, "Should have Option 1"
    assert 'Option 2:' in result, "Should have Option 2"
    assert 'Option 3:' in result, "Should have Option 3"
    assert 'Vessel' in result, "Should contain Vessel field"
    assert 'Voyage' in result, "Should contain Voyage field"
    assert 'ETD' in result, "Should contain ETD field"
    assert 'ETA' in result, "Should contain ETA field"

    print("[PASS] format_email() - Multiple schedules test PASSED")
    print()


def test_format_email_single():
    """Test format_email() with single schedule"""
    print("=" * 70)
    print("TEST 5: format_email() - Single Schedule")
    print("=" * 70)

    schedules = [create_sample_schedules()[0]]
    result = format_email(schedules)

    print(result)
    print()

    # Verify structure
    assert 'Option' not in result, "Should NOT have Option prefix for single schedule"
    assert 'Vessel' in result, "Should contain Vessel field"
    assert 'MAERSK OSLO' in result, "Should contain vessel name"
    assert '425N' in result, "Should contain voyage number"

    print("[PASS] format_email() - Single schedule test PASSED")
    print()


def test_save_output_with_carrier():
    """Test save_output() with carrier subfolder"""
    print("=" * 70)
    print("TEST 6: save_output() - With Carrier Subfolder")
    print("=" * 70)

    schedules = create_sample_schedules()
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")

    # Clean up previous test files
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)

    filepath = save_output(schedules, output_dir, carrier="MAERSK")

    print(f"File saved to: {filepath}")
    print()

    # Verify file exists
    assert os.path.exists(filepath), f"File should exist at {filepath}"

    # Verify carrier directory created
    carrier_dir = os.path.join(output_dir, "MAERSK")
    assert os.path.exists(carrier_dir), f"Carrier directory should exist at {carrier_dir}"

    # Read and display content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    print("File contents:")
    print("-" * 70)
    print(content)
    print("-" * 70)
    print()

    # Verify content
    assert 'Carrier: MAERSK' in content, "Should contain carrier header"
    assert 'Vessel' in content, "Should contain vessel info"

    print(f"[PASS] save_output() - With carrier test PASSED")
    print(f"  Created: {filepath}")
    print()

    return filepath


def test_save_output_without_carrier():
    """Test save_output() without carrier subfolder"""
    print("=" * 70)
    print("TEST 7: save_output() - Without Carrier")
    print("=" * 70)

    schedules = [create_sample_schedules()[0]]
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")

    filepath = save_output(schedules, output_dir)

    print(f"File saved to: {filepath}")
    print()

    # Verify file exists
    assert os.path.exists(filepath), f"File should exist at {filepath}"

    # Verify filename format
    assert 'SCHEDULE_' in os.path.basename(filepath), "Filename should start with SCHEDULE_"

    # Read and display content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    print("File contents:")
    print("-" * 70)
    print(content)
    print("-" * 70)
    print()

    # Verify content (should NOT have carrier header)
    assert 'Carrier:' not in content, "Should NOT contain carrier header"
    assert 'Vessel' in content, "Should contain vessel info"

    print(f"[PASS] save_output() - Without carrier test PASSED")
    print(f"  Created: {filepath}")
    print()

    return filepath


def test_copy_to_clipboard():
    """Test copy_to_clipboard() function"""
    print("=" * 70)
    print("TEST 8: copy_to_clipboard()")
    print("=" * 70)

    print(f"Clipboard support available: {HAS_CLIPBOARD}")

    if HAS_CLIPBOARD:
        test_text = "Test clipboard content"
        result = copy_to_clipboard(test_text)
        print(f"Copy operation result: {result}")

        if result:
            print("[PASS] copy_to_clipboard() test PASSED")
            print("  Content copied to clipboard successfully")
        else:
            print("[WARN] copy_to_clipboard() returned False (operation failed)")
    else:
        print("[INFO] pyperclip not installed - clipboard functionality disabled")
        print("  This is expected if pyperclip is not installed")
        result = copy_to_clipboard("test")
        assert result == False, "Should return False when pyperclip not available"
        print("[PASS] copy_to_clipboard() fallback test PASSED")

    print()


def test_long_vessel_names():
    """Test formatting with long vessel names (truncation)"""
    print("=" * 70)
    print("TEST 9: Long Vessel Names - Truncation Test")
    print("=" * 70)

    schedules = [
        Schedule(
            vessel="VERY LONG VESSEL NAME THAT EXCEEDS COLUMN WIDTH",
            voyage="LONGVOY123",
            etd="15 JANUARY 2026 10:00",
            eta="25 JANUARY 2026 14:30"
        )
    ]

    result = format_table(schedules)
    print(result)
    print()

    # Verify truncation
    lines = result.split('\n')
    for line in lines:
        assert len(line) <= 71, f"Line too long: {len(line)} chars"

    print("[PASS] Long vessel names test PASSED")
    print("  Truncation working correctly")
    print()


def test_edge_cases():
    """Test edge cases"""
    print("=" * 70)
    print("TEST 10: Edge Cases")
    print("=" * 70)

    # Empty list
    result = format_table([])
    print("Empty list result:")
    print(result)
    assert 'VESSEL' in result, "Should still show header"
    print("[PASS] Empty list handled")
    print()

    # Schedule with all TBA
    schedules = [Schedule()]
    result_table = format_table(schedules)
    result_email = format_email(schedules)

    print("All TBA schedule - Table format:")
    print(result_table)
    print()
    print("All TBA schedule - Email format:")
    print(result_email)
    print()

    assert 'TBA' in result_table, "Should contain TBA"
    assert 'TBA' in result_email, "Should contain TBA"

    print("[PASS] Edge cases test PASSED")
    print()


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print(" " * 15 + "SCHEDULE PARSER OUTPUT FORMATTER TESTS")
    print("=" * 70)
    print()

    try:
        # Basic formatting tests
        test_format_table()
        test_format_table_single()
        test_format_table_with_tba()
        test_format_email_multiple()
        test_format_email_single()

        # File I/O tests
        test_save_output_with_carrier()
        test_save_output_without_carrier()

        # Clipboard test
        test_copy_to_clipboard()

        # Edge case tests
        test_long_vessel_names()
        test_edge_cases()

        # Summary
        print("=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - format_table() - Works correctly with single/multiple schedules")
        print("  - format_email() - Formats correctly for single/multiple schedules")
        print("  - save_output() - Creates files with/without carrier subfolders")
        print(f"  - copy_to_clipboard() - {'Available' if HAS_CLIPBOARD else 'Not available (pyperclip not installed)'}")
        print("  - Edge cases - Handled correctly (empty lists, TBA values, long names)")
        print()

        # Cleanup info
        output_dir = os.path.join(os.path.dirname(__file__), "test_output")
        if os.path.exists(output_dir):
            print(f"Test output files saved to: {output_dir}")
            print("(These files can be safely deleted)")

        return True

    except AssertionError as e:
        print()
        print("=" * 70)
        print("TEST FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        return False
    except Exception as e:
        print()
        print("=" * 70)
        print("TEST ERROR!")
        print("=" * 70)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
