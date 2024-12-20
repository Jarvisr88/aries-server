"""
Tests for the next_dos module.
"""

import pytest
from datetime import datetime
from app.procedures.scheduling.next_dos import get_next_dos_from, validate_frequency


@pytest.mark.parametrize("from_date,frequency,expected_delta", [
    # Test one-time frequency (no change)
    (datetime(2024, 1, 1), 'One time', {'days': 0}),
    
    # Test daily frequency
    (datetime(2024, 1, 1), 'Daily', {'days': 1}),
    
    # Test weekly frequency
    (datetime(2024, 1, 1), 'Weekly', {'days': 7}),
    
    # Test monthly frequency
    (datetime(2024, 1, 1), 'Monthly', {'months': 1}),
    
    # Test quarterly frequency
    (datetime(2024, 1, 1), 'Quarterly', {'months': 3}),
    
    # Test semi-annual frequency
    (datetime(2024, 1, 1), 'Semi-Annually', {'months': 6}),
    
    # Test annual frequency
    (datetime(2024, 1, 1), 'Annually', {'months': 12}),
])
def test_get_next_dos_from_basic(from_date, frequency, expected_delta):
    """Test basic frequency calculations."""
    result = get_next_dos_from(from_date, None, frequency)
    
    # Calculate expected date based on delta
    expected = from_date
    if 'days' in expected_delta:
        expected = from_date.replace(day=from_date.day + expected_delta['days'])
    if 'months' in expected_delta:
        new_month = from_date.month + expected_delta['months']
        year_add = (new_month - 1) // 12
        month = ((new_month - 1) % 12) + 1
        expected = from_date.replace(year=from_date.year + year_add, month=month)
    
    assert result == expected


def test_get_next_dos_from_calendar_monthly():
    """Test calendar monthly frequency specifically."""
    # Test with start date in middle of month
    result = get_next_dos_from(datetime(2024, 1, 15), None, 'Calendar Monthly')
    assert result == datetime(2024, 2, 1)

    # Test with start date at end of month
    result = get_next_dos_from(datetime(2024, 1, 31), None, 'Calendar Monthly')
    assert result == datetime(2024, 2, 1)

    # Test over year boundary
    result = get_next_dos_from(datetime(2024, 12, 15), None, 'Calendar Monthly')
    assert result == datetime(2025, 1, 1)


def test_get_next_dos_from_invalid_frequency():
    """Test handling of invalid frequency."""
    with pytest.raises(ValueError) as exc_info:
        get_next_dos_from(datetime(2024, 1, 1), None, 'Invalid')
    assert 'Invalid frequency pattern' in str(exc_info.value)


@pytest.mark.parametrize("frequency,expected", [
    ('One time', True),
    ('Daily', True),
    ('Weekly', True),
    ('Monthly', True),
    ('Calendar Monthly', True),
    ('Quarterly', True),
    ('Semi-Annually', True),
    ('Annually', True),
    ('Invalid', False),
    ('', False),
    ('  Daily  ', True),  # Test with whitespace
])
def test_validate_frequency(frequency, expected):
    """Test frequency validation."""
    assert validate_frequency(frequency) == expected
