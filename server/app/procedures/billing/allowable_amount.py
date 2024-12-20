from decimal import Decimal
from typing import Optional
from enum import Enum, auto

class SaleRentType(Enum):
    """Types of sales and rentals"""
    ONE_TIME_SALE = "One Time Sale"
    RE_OCCURRING_SALE = "Re-occurring Sale"
    ONE_TIME_RENTAL = "One Time Rental"
    MEDICARE_OXYGEN_RENTAL = "Medicare Oxygen Rental"
    MONTHLY_RENTAL = "Monthly Rental"
    RENT_TO_PURCHASE = "Rent to Purchase"
    CAPPED_RENTAL = "Capped Rental"
    PARENTAL_CAPPED_RENTAL = "Parental Capped Rental"

class AllowableAmountCalculator:
    """Calculates allowable amounts for different sale/rental types"""
    
    @staticmethod
    def calculate(
        sale_rent_type: str,
        billing_month: int,
        price: Decimal,
        quantity: int,
        sale_price: Optional[Decimal] = None,
        flat_rate: bool = False
    ) -> Decimal:
        """
        Calculate the allowable amount based on sale/rental type and billing parameters
        
        Args:
            sale_rent_type: Type of sale or rental (from SaleRentType enum)
            billing_month: Current billing month
            price: Base price for calculation
            quantity: Quantity being billed
            sale_price: Sale price (required for rent to purchase)
            flat_rate: If True, quantity is forced to 1
            
        Returns:
            Calculated allowable amount
            
        Note:
            For rent to purchase, sale_price must be provided and should be greater
            than (9 * price) to make business sense.
        """
        # Validate and adjust billing month
        billing_month = max(1, billing_month)
        
        # Handle flat rate
        if flat_rate:
            quantity = 1
            
        # Handle different sale/rental types
        if sale_rent_type in [
            SaleRentType.ONE_TIME_SALE.value,
            SaleRentType.RE_OCCURRING_SALE.value,
            SaleRentType.ONE_TIME_RENTAL.value
        ]:
            if billing_month == 1:
                return price * Decimal(quantity)
                
        elif sale_rent_type in [
            SaleRentType.MEDICARE_OXYGEN_RENTAL.value,
            SaleRentType.MONTHLY_RENTAL.value
        ]:
            return price * Decimal(quantity)
            
        elif sale_rent_type == SaleRentType.RENT_TO_PURCHASE.value:
            if billing_month <= 9:
                return price * Decimal(quantity)
            elif billing_month == 10:
                if sale_price is None:
                    raise ValueError("Sale price is required for rent to purchase calculation")
                return (sale_price - (9 * price)) * Decimal(quantity)
                
        elif sale_rent_type == SaleRentType.CAPPED_RENTAL.value:
            if billing_month <= 3:
                return price * Decimal(quantity)
            elif billing_month <= 15:
                return Decimal('0.75') * price * Decimal(quantity)
            elif billing_month >= 22 and (billing_month - 22) % 6 == 0:
                return price * Decimal(quantity)
                
        elif sale_rent_type == SaleRentType.PARENTAL_CAPPED_RENTAL.value:
            if billing_month <= 15:
                return price * Decimal(quantity)
            elif billing_month >= 22 and (billing_month - 22) % 6 == 0:
                return price * Decimal(quantity)
                
        # Default case - no allowable amount
        return Decimal('0.00')
        
    @classmethod
    def get_allowable_amount(cls,
                           sale_rent_type: str,
                           billing_month: int,
                           price: Decimal,
                           quantity: int,
                           sale_price: Optional[Decimal] = None,
                           flat_rate: bool = False) -> Decimal:
        """
        Public interface for calculating allowable amount
        
        Args:
            sale_rent_type: Type of sale or rental
            billing_month: Current billing month
            price: Base price for calculation
            quantity: Quantity being billed
            sale_price: Sale price (required for rent to purchase)
            flat_rate: If True, quantity is forced to 1
            
        Returns:
            Calculated allowable amount
        """
        return cls.calculate(
            sale_rent_type,
            billing_month,
            price,
            quantity,
            sale_price,
            flat_rate
        )
