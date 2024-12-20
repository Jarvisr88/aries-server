"""Test cases for the InventoryAdjustment class."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.procedures.inventory.adjustment import InventoryAdjustment
from app.models.inventory import (
    InventoryItem,
    InventoryHistory,
    InventoryAdjustmentType
)
from app.core.exceptions import ProcedureError

@pytest.fixture
def db():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def inventory_item():
    """Sample inventory item for testing"""
    return InventoryItem(
        id=1,
        quantity=Decimal('10.00'),
        last_physical_count=None
    )

def test_validate_adjustment_zero_quantity(inventory_item):
    """Test validation with zero quantity"""
    procedure = InventoryAdjustment(Mock())
    
    with pytest.raises(ProcedureError, match="cannot be zero"):
        procedure._validate_adjustment(
            inventory_item,
            Decimal('0.00'),
            InventoryAdjustmentType.PHYSICAL_COUNT
        )

def test_validate_adjustment_insufficient_quantity(inventory_item):
    """Test validation with insufficient quantity"""
    procedure = InventoryAdjustment(Mock())
    
    with pytest.raises(ProcedureError, match="Insufficient quantity"):
        procedure._validate_adjustment(
            inventory_item,
            Decimal('-20.00'),
            InventoryAdjustmentType.DAMAGE
        )

def test_validate_adjustment_negative_physical_count(inventory_item):
    """Test validation with negative physical count"""
    procedure = InventoryAdjustment(Mock())
    
    with pytest.raises(ProcedureError, match="cannot be negative"):
        procedure._validate_adjustment(
            inventory_item,
            Decimal('-5.00'),
            InventoryAdjustmentType.PHYSICAL_COUNT
        )

def test_validate_adjustment_positive_damage(inventory_item):
    """Test validation with positive damage adjustment"""
    procedure = InventoryAdjustment(Mock())
    
    with pytest.raises(ProcedureError, match="must be negative"):
        procedure._validate_adjustment(
            inventory_item,
            Decimal('5.00'),
            InventoryAdjustmentType.DAMAGE
        )

def test_create_history(inventory_item):
    """Test creating history record"""
    db = Mock()
    procedure = InventoryAdjustment(db)
    
    quantity = Decimal('5.00')
    history = procedure._create_history(
        inventory_item,
        quantity,
        InventoryAdjustmentType.PHYSICAL_COUNT,
        reference_id=None,
        notes="Test adjustment"
    )
    
    assert isinstance(history, InventoryHistory)
    assert history.inventory_item_id == inventory_item.id
    assert history.adjustment_type == InventoryAdjustmentType.PHYSICAL_COUNT
    assert history.quantity_before == inventory_item.quantity
    assert history.adjustment_quantity == quantity
    assert history.quantity_after == inventory_item.quantity + quantity
    assert history.notes == "Test adjustment"
    assert db.add.called_once_with(history)

def test_execute_item_not_found(db):
    """Test adjustment with non-existent item"""
    db.query.return_value.get.return_value = None
    
    procedure = InventoryAdjustment(db)
    with pytest.raises(ProcedureError, match="not found"):
        procedure._execute(
            999,
            Decimal('5.00'),
            InventoryAdjustmentType.PHYSICAL_COUNT
        )

def test_execute_physical_count(db, inventory_item):
    """Test physical count adjustment"""
    db.query.return_value.get.return_value = inventory_item
    
    procedure = InventoryAdjustment(db)
    procedure._execute(
        inventory_item.id,
        Decimal('15.00'),
        InventoryAdjustmentType.PHYSICAL_COUNT,
        notes="Physical count adjustment"
    )
    
    assert inventory_item.quantity == Decimal('25.00')
    assert inventory_item.last_physical_count is not None
    assert db.commit.called_once()

def test_execute_damage(db, inventory_item):
    """Test damage adjustment"""
    db.query.return_value.get.return_value = inventory_item
    initial_quantity = inventory_item.quantity
    
    procedure = InventoryAdjustment(db)
    procedure._execute(
        inventory_item.id,
        Decimal('-2.00'),
        InventoryAdjustmentType.DAMAGE,
        notes="Damage adjustment"
    )
    
    assert inventory_item.quantity == initial_quantity - Decimal('2.00')
    assert db.commit.called_once()

def test_execute_with_reference(db, inventory_item):
    """Test adjustment with reference ID"""
    db.query.return_value.get.return_value = inventory_item
    
    procedure = InventoryAdjustment(db)
    procedure._execute(
        inventory_item.id,
        Decimal('5.00'),
        InventoryAdjustmentType.PHYSICAL_COUNT,
        reference_id=123,
        notes="Referenced adjustment"
    )
    
    # Verify history created with reference
    assert db.add.call_count == 1
    history = db.add.call_args[0][0]
    assert history.reference_id == 123
