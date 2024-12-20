from datetime import datetime
from typing import Optional
from enum import Enum

class SaleRentType(str, Enum):
    ONE_TIME_SALE = 'One Time Sale'
    REOCCURING_SALE = 'Re-occurring Sale'
    ONE_TIME_RENTAL = 'One Time Rental'
    MEDICARE_OXYGEN_RENTAL = 'Medicare Oxygen Rental'
    MONTHLY_RENTAL = 'Monthly Rental'
    RENT_TO_PURCHASE = 'Rent to Purchase'
    CAPPED_RENTAL = 'Capped Rental'
    PARENTAL_CAPPED_RENTAL = 'Parental Capped Rental'

class InvoiceSkipRules:
    """Rules engine for determining if an invoice should be skipped based on billing rules"""
    
    CUTOFF_DATE_2006 = datetime(2006, 1, 1)
    CUTOFF_DATE_2009 = datetime(2009, 1, 1)
    
    @staticmethod
    def must_skip(
        delivery_date: datetime,
        dos_from: datetime,
        sale_rent_type: str,
        billing_month: int,
        modifier1: Optional[str] = None,
        modifier2: Optional[str] = None,
        modifier3: Optional[str] = None,
        modifier4: Optional[str] = None
    ) -> bool:
        """
        Determine if an invoice should be skipped based on billing rules
        
        Args:
            delivery_date: Date of delivery
            dos_from: Date of service start
            sale_rent_type: Type of sale/rental
            billing_month: Current billing month
            modifier1: First modifier code (optional)
            modifier2: Second modifier code (optional) 
            modifier3: Third modifier code (optional)
            modifier4: Fourth modifier code (optional)
            
        Returns:
            True if invoice should be skipped, False otherwise
        """
        # Ensure billing month is at least 1
        if billing_month <= 0:
            billing_month = 1

        # Handle one-time transactions
        if sale_rent_type in [
            SaleRentType.ONE_TIME_SALE,
            SaleRentType.REOCCURING_SALE,
            SaleRentType.ONE_TIME_RENTAL
        ]:
            return billing_month > 1

        # Handle Medicare oxygen rental
        if sale_rent_type == SaleRentType.MEDICARE_OXYGEN_RENTAL:
            if delivery_date < InvoiceSkipRules.CUTOFF_DATE_2006:
                return (dos_from >= InvoiceSkipRules.CUTOFF_DATE_2009 and 
                       billing_month > 36)
            return billing_month > 36

        # Handle monthly rental
        if sale_rent_type == SaleRentType.MONTHLY_RENTAL:
            return False

        # Handle rent to purchase
        if sale_rent_type == SaleRentType.RENT_TO_PURCHASE:
            return billing_month > 10

        # Handle capped rentals
        if sale_rent_type in [
            SaleRentType.CAPPED_RENTAL,
            SaleRentType.PARENTAL_CAPPED_RENTAL
        ]:
            if delivery_date < InvoiceSkipRules.CUTOFF_DATE_2006:
                if billing_month <= 15:
                    return False
                elif billing_month < 22:
                    return True
                else:
                    return (billing_month - 22) % 6 != 0
            return billing_month > 13

        return False

    @classmethod
    def check_invoice(cls, 
                     delivery_date: datetime,
                     dos_from: datetime,
                     sale_rent_type: str,
                     billing_month: int,
                     modifier1: Optional[str] = None,
                     modifier2: Optional[str] = None,
                     modifier3: Optional[str] = None,
                     modifier4: Optional[str] = None) -> bool:
        """
        Convenience method to check if an invoice should be skipped
        
        Args:
            delivery_date: Date of delivery
            dos_from: Date of service start
            sale_rent_type: Type of sale/rental
            billing_month: Current billing month
            modifier1: First modifier code (optional)
            modifier2: Second modifier code (optional)
            modifier3: Third modifier code (optional)
            modifier4: Fourth modifier code (optional)
            
        Returns:
            True if invoice should be skipped, False if it should be processed
        """
        return cls.must_skip(
            delivery_date=delivery_date,
            dos_from=dos_from,
            sale_rent_type=sale_rent_type,
            billing_month=billing_month,
            modifier1=modifier1,
            modifier2=modifier2,
            modifier3=modifier3,
            modifier4=modifier4
        )
