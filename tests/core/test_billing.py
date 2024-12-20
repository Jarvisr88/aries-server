"""Tests for billing calculation functions"""
from datetime import date
from decimal import Decimal
import pytest
from app.core.billing import (
    get_amount_multiplier,
    get_allowable_amount,
    get_billable_amount,
    get_quantity_multiplier
)

def test_get_quantity_multiplier_one_time():
    """Test quantity multiplier for one-time orders"""
    # One-time sale
    assert get_quantity_multiplier(
        'Sale',
        'One Time',
        'One Time'
    ) == Decimal('1.00')
    
    # One-time rental
    assert get_quantity_multiplier(
        'Rental',
        'One Time',
        'One Time'
    ) == Decimal('1.00')
    
def test_get_quantity_multiplier_recurring_daily():
    """Test quantity multiplier for daily recurring orders"""
    # Daily billing, weekly frequency (7 units per week)
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Daily',
        'Weekly',
        7
    ) == Decimal('1.00')  # 7 units / 7 days = 1 per day
    
    # Daily billing, monthly frequency (30 units per month)
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Daily',
        'Monthly',
        30
    ) == Decimal('1.00')  # 30 units / 30 days = 1 per day
    
def test_get_quantity_multiplier_recurring_weekly():
    """Test quantity multiplier for weekly recurring orders"""
    # Weekly billing, monthly frequency (20 units per month)
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Weekly',
        'Monthly',
        20
    ) == Decimal('4.67')  # (20 units / 30 days) * 7 days = 4.67 per week
    
def test_get_quantity_multiplier_recurring_monthly():
    """Test quantity multiplier for monthly recurring orders"""
    # Monthly billing, quarterly frequency (90 units per quarter)
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Monthly',
        'Quarterly',
        90
    ) == Decimal('30.00')  # (90 units / 90 days) * 30 days = 30 per month
    
def test_get_quantity_multiplier_recurring_quarterly():
    """Test quantity multiplier for quarterly recurring orders"""
    # Quarterly billing, annual frequency (365 units per year)
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Quarterly',
        'Annually',
        365
    ) == Decimal('90.00')  # (365 units / 365 days) * 90 days = 90 per quarter
    
def test_get_quantity_multiplier_recurring_annually():
    """Test quantity multiplier for annual recurring orders"""
    # Annual billing, monthly frequency (30 units per month)
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Annually',
        'Monthly',
        30
    ) == Decimal('365.00')  # (30 units / 30 days) * 365 days = 365 per year
    
def test_get_quantity_multiplier_missing_frequency():
    """Test quantity multiplier with missing frequency parameters"""
    # Missing frequency
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Monthly',
        units_per_freq=30
    ) == Decimal('1.00')
    
    # Missing units per frequency
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'Monthly',
        'Weekly'
    ) == Decimal('1.00')
    
def test_get_quantity_multiplier_invalid_combination():
    """Test quantity multiplier with invalid parameter combinations"""
    # One-time order with recurring billing
    assert get_quantity_multiplier(
        'Sale',
        'One Time',
        'Monthly',
        'Monthly',
        30
    ) == Decimal('1.00')
    
    # Recurring order with one-time billing
    assert get_quantity_multiplier(
        'Rental',
        'Recurring',
        'One Time',
        'Monthly',
        30
    ) == Decimal('1.00')
