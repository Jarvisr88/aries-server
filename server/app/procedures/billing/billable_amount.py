"""
Billable Amount Calculator

Python implementation of the GetBillableAmount function for calculating
billable amounts based on rental types and billing months.
"""
from decimal import Decimal
from enum import Enum
from typing import Dict, Any

from app.procedures.base import BaseProcedure


class SaleRentType(str, Enum):
    """Sale/Rental type enumeration"""
    ONE_TIME_SALE = 'One Time Sale'
    REOCCURRING_SALE = 'Re-occurring Sale'
    ONE_TIME_RENTAL = 'One Time Rental'
    MEDICARE_OXYGEN_RENTAL = 'Medicare Oxygen Rental'
    MONTHLY_RENTAL = 'Monthly Rental'
    RENT_TO_PURCHASE = 'Rent to Purchase'
    CAPPED_RENTAL = 'Capped Rental'
    PARENTAL_CAPPED_RENTAL = 'Parental Capped Rental'


class BillableAmountCalculator(BaseProcedure):
    """
    Calculates billable amounts based on rental type and billing month.
    
    This procedure:
    1. Handles different rental types
    2. Calculates based on billing month
    3. Supports flat rate pricing
    4. Manages special rental programs
    """

    async def _execute(
        self,
        sale_rent_type: str,
        billing_month: int,
        price: Decimal,
        quantity: int,
        sale_price: Decimal,
        flat_rate: bool
    ) -> Dict[str, Any]:
        """Execute the billable amount calculation"""
        try:
            amount = self._calculate_amount(
                sale_rent_type=sale_rent_type,
                billing_month=billing_month,
                price=price,
                quantity=quantity,
                sale_price=sale_price,
                flat_rate=flat_rate
            )
            return {
                'success': True,
                'amount': amount
            }
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_amount(
        self,
        sale_rent_type: str,
        billing_month: int,
        price: Decimal,
        quantity: int,
        sale_price: Decimal,
        flat_rate: bool
    ) -> Decimal:
        """Calculate the billable amount"""
        # Validate and normalize inputs
        if billing_month <= 0:
            billing_month = 1

        if flat_rate:
            quantity = 1

        try:
            rent_type = SaleRentType(sale_rent_type)
        except ValueError:
            return Decimal('0.00')

        # One-time charges
        if rent_type in {
            SaleRentType.ONE_TIME_SALE,
            SaleRentType.REOCCURRING_SALE,
            SaleRentType.ONE_TIME_RENTAL
        }:
            if billing_month == 1:
                return price * Decimal(quantity)
            return Decimal('0.00')

        # Monthly rentals
        if rent_type in {
            SaleRentType.MEDICARE_OXYGEN_RENTAL,
            SaleRentType.MONTHLY_RENTAL
        }:
            return price * Decimal(quantity)

        # Rent to purchase
        if rent_type == SaleRentType.RENT_TO_PURCHASE:
            if billing_month <= 9:
                return price * Decimal(quantity)
            elif billing_month == 10:
                return (sale_price - (9 * price)) * Decimal(quantity)
            return Decimal('0.00')

        # Capped rentals
        if rent_type in {
            SaleRentType.CAPPED_RENTAL,
            SaleRentType.PARENTAL_CAPPED_RENTAL
        }:
            if billing_month <= 15:
                return price * Decimal(quantity)
            elif billing_month >= 22 and (billing_month - 22) % 6 == 0:
                return price * Decimal(quantity)
            return Decimal('0.00')

        return Decimal('0.00')
