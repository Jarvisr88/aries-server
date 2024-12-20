"""
Amount Multiplier Calculator

Python implementation of the GetAmountMultiplier function for calculating
billing multipliers based on rental types and dates.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from app.procedures.base import BaseProcedure
from app.procedures.billing.date_utils import get_next_dos_from


class SaleRentType(str, Enum):
    """Sale/Rental type enumeration"""
    ONE_TIME_SALE = 'One Time Sale'
    REOCCURRING_SALE = 'Re-occurring Sale'
    RENT_TO_PURCHASE = 'Rent to Purchase'
    CAPPED_RENTAL = 'Capped Rental'
    PARENTAL_CAPPED_RENTAL = 'Parental Capped Rental'
    MEDICARE_OXYGEN_RENTAL = 'Medicare Oxygen Rental'
    MONTHLY_RENTAL = 'Monthly Rental'
    ONE_TIME_RENTAL = 'One Time Rental'


class OrderFrequency(str, Enum):
    """Order frequency enumeration"""
    ONE_TIME = 'One Time'
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    QUARTERLY = 'Quarterly'
    SEMI_ANNUALLY = 'Semi-Annually'
    ANNUALLY = 'Annually'


class AmountMultiplierCalculator(BaseProcedure):
    """
    Calculates amount multipliers for billing based on rental type and dates.
    
    This procedure:
    1. Determines multiplier based on sale/rental type
    2. Handles special cases for different frequencies
    3. Calculates prorated amounts for partial periods
    """

    def _get_multiplier(
        self,
        from_date: datetime,
        to_date: datetime,
        ordered_when: str,
        billed_when: str
    ) -> float:
        """Calculate multiplier based on date range and frequency"""
        days_diff = (to_date - from_date).days

        multipliers = {
            OrderFrequency.WEEKLY: 7.0,
            OrderFrequency.MONTHLY: 30.4,
            OrderFrequency.QUARTERLY: 91.25,
            OrderFrequency.SEMI_ANNUALLY: 182.5,
            OrderFrequency.ANNUALLY: 365.0
        }

        return days_diff / multipliers.get(OrderFrequency(ordered_when), 1.0)

    async def _execute(
        self,
        from_date: datetime,
        to_date: datetime,
        pickup_date: Optional[datetime],
        sale_rent_type: str,
        ordered_when: str,
        billed_when: str
    ) -> float:
        """Execute the amount multiplier calculation"""
        # Handle fixed multiplier cases
        fixed_multiplier_types = {
            SaleRentType.ONE_TIME_SALE,
            SaleRentType.REOCCURRING_SALE,
            SaleRentType.RENT_TO_PURCHASE,
            SaleRentType.CAPPED_RENTAL,
            SaleRentType.PARENTAL_CAPPED_RENTAL,
            SaleRentType.MEDICARE_OXYGEN_RENTAL
        }

        if SaleRentType(sale_rent_type) in fixed_multiplier_types:
            return 1.0

        # Handle Monthly Rental
        if sale_rent_type == SaleRentType.MONTHLY_RENTAL:
            if ordered_when == OrderFrequency.DAILY:
                next_to_date = await get_next_dos_from(from_date, to_date, billed_when)
                
                if pickup_date is None:
                    return (next_to_date - from_date).days
                elif next_to_date <= pickup_date:
                    return (next_to_date - from_date).days
                elif from_date <= pickup_date:
                    return (pickup_date - from_date).days + 1
                else:  # pickup_date < from_date
                    return 0
            else:
                return self._get_multiplier(from_date, to_date, ordered_when, billed_when)

        # Handle One Time Rental
        if sale_rent_type == SaleRentType.ONE_TIME_RENTAL:
            if ordered_when == OrderFrequency.ONE_TIME:
                return 1.0
            
            if not pickup_date:
                return 0.0
                
            days_diff = (pickup_date - from_date).days + 1
            
            if ordered_when == OrderFrequency.DAILY:
                return days_diff
            elif ordered_when == OrderFrequency.WEEKLY:
                return days_diff / 7.0
            elif ordered_when == OrderFrequency.MONTHLY:
                return days_diff / 30.4
            elif ordered_when == OrderFrequency.QUARTERLY:
                return days_diff / 91.25
            elif ordered_when == OrderFrequency.SEMI_ANNUALLY:
                return days_diff / 182.5
            elif ordered_when == OrderFrequency.ANNUALLY:
                return days_diff / 365.0

        return 0.0  # Default case
