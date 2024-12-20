"""
Payments By Date Module

Contains functions for retrieving and analyzing payments by date.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.payment import Payment


def get_payments_by_date(
    session: Session,
    start_date: datetime,
    end_date: datetime,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    group_by: str = 'day'
) -> List[Dict[str, Any]]:
    """
    Get payments within a date range with optional filtering and grouping
    
    Args:
        session: Database session
        start_date: Start date for payment range
        end_date: End date for payment range
        payment_method: Optional payment method filter
        status: Optional payment status filter
        group_by: Grouping interval ('day', 'week', 'month', 'year')
        
    Returns:
        List of dictionaries containing payment information grouped by date
    """
    # Validate dates
    if start_date > end_date:
        raise ValueError("Start date must be before end date")
        
    # Build base query
    query = select(Payment).where(
        and_(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
    )
    
    # Add filters if provided
    if payment_method:
        query = query.where(Payment.payment_method == payment_method)
    if status:
        query = query.where(Payment.status == status)
        
    # Get all payments
    payments = session.execute(query).scalars().all()
    
    # Group payments by date
    grouped_payments = {}
    
    for payment in payments:
        # Get group key based on group_by parameter
        if group_by == 'day':
            group_key = payment.payment_date.date()
        elif group_by == 'week':
            group_key = payment.payment_date.date() - timedelta(days=payment.payment_date.weekday())
        elif group_by == 'month':
            group_key = payment.payment_date.replace(day=1).date()
        elif group_by == 'year':
            group_key = payment.payment_date.replace(month=1, day=1).date()
        else:
            raise ValueError("Invalid group_by parameter. Must be 'day', 'week', 'month', or 'year'")
            
        if group_key not in grouped_payments:
            grouped_payments[group_key] = {
                "date": group_key,
                "total_amount": Decimal('0.00'),
                "count": 0,
                "payment_methods": {},
                "statuses": {}
            }
            
        group = grouped_payments[group_key]
        group["total_amount"] += payment.amount
        group["count"] += 1
        
        # Count by payment method
        method = payment.payment_method
        if method in group["payment_methods"]:
            group["payment_methods"][method]["count"] += 1
            group["payment_methods"][method]["amount"] += payment.amount
        else:
            group["payment_methods"][method] = {
                "count": 1,
                "amount": payment.amount
            }
            
        # Count by status
        status = payment.status
        if status in group["statuses"]:
            group["statuses"][status]["count"] += 1
            group["statuses"][status]["amount"] += payment.amount
        else:
            group["statuses"][status] = {
                "count": 1,
                "amount": payment.amount
            }
            
    # Convert to sorted list
    result = list(grouped_payments.values())
    result.sort(key=lambda x: x["date"])
    
    return result


def get_payment_trends(
    session: Session,
    start_date: datetime,
    end_date: datetime,
    interval: str = 'month'
) -> Dict[str, Any]:
    """
    Get payment trends analysis over a date range
    
    Args:
        session: Database session
        start_date: Start date for analysis
        end_date: End date for analysis
        interval: Analysis interval ('day', 'week', 'month', 'year')
        
    Returns:
        Dictionary containing trend analysis
    """
    payments = get_payments_by_date(
        session,
        start_date,
        end_date,
        group_by=interval
    )
    
    if not payments:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "total_payments": 0,
            "total_amount": Decimal('0.00'),
            "average_per_period": Decimal('0.00'),
            "trend": "No data available"
        }
        
    # Calculate trends
    amounts = [p["total_amount"] for p in payments]
    counts = [p["count"] for p in payments]
    
    avg_amount = sum(amounts) / len(amounts)
    avg_count = sum(counts) / len(counts)
    
    # Simple trend analysis
    if len(amounts) >= 2:
        first_half = amounts[:len(amounts)//2]
        second_half = amounts[len(amounts)//2:]
        first_half_avg = sum(first_half) / len(first_half)
        second_half_avg = sum(second_half) / len(second_half)
        
        if second_half_avg > first_half_avg * Decimal('1.1'):
            trend = "Increasing"
        elif second_half_avg < first_half_avg * Decimal('0.9'):
            trend = "Decreasing"
        else:
            trend = "Stable"
    else:
        trend = "Insufficient data for trend analysis"
        
    return {
        "start_date": start_date,
        "end_date": end_date,
        "interval": interval,
        "total_payments": sum(counts),
        "total_amount": sum(amounts),
        "average_per_period": avg_amount,
        "average_count_per_period": avg_count,
        "trend": trend,
        "periods": len(payments),
        "period_data": payments
    }
