import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.order import Order, OrderLine
from app.procedures.mir.update_inventory import InventoryMIRUpdater

def test_validate_inventory_required_fields(db: Session):
    """Test validation of required inventory fields"""
    item = InventoryItem(
        is_active=True,
        quantity=10,
        unit_price=100,
        cost_price=50
    )
    db.add(item)
    db.commit()
    
    updater = InventoryMIRUpdater(db)
    issues = updater._validate_inventory(item)
    
    assert "ItemNumber" in issues
    assert "Description" in issues
    assert "Category" in issues
    assert "UnitOfMeasure" in issues
    
def test_validate_inventory_active_checks(db: Session):
    """Test validation of active inventory items"""
    item = InventoryItem(
        item_number="TEST001",
        description="Test Item",
        category="Test",
        unit_of_measure="EA",
        is_active=True,
        quantity=-5,
        reorder_point=10,
        unit_price=0,
        cost_price=-1
    )
    db.add(item)
    db.commit()
    
    updater = InventoryMIRUpdater(db)
    issues = updater._validate_inventory(item)
    
    assert "NegativeQuantity" in issues
    assert "BelowReorderPoint" in issues
    assert "NoRecentTransactions" in issues
    assert "NoRecentOrders" in issues
    assert "InvalidPrice" in issues
    assert "InvalidCost" in issues
    
def test_validate_inventory_serial_numbers(db: Session):
    """Test validation of serialized inventory items"""
    item = InventoryItem(
        item_number="TEST002",
        description="Test Serialized Item",
        category="Test",
        unit_of_measure="EA",
        is_active=True,
        is_serialized=True,
        quantity=1,
        unit_price=100,
        cost_price=50
    )
    db.add(item)
    db.commit()
    
    # Add transaction without serial number
    transaction = InventoryTransaction(
        inventory_item_id=item.id,
        transaction_date=datetime.now(),
        quantity=1
    )
    db.add(transaction)
    db.commit()
    
    updater = InventoryMIRUpdater(db)
    issues = updater._validate_inventory(item)
    
    assert "MissingSerials" in issues
    
def test_validate_inventory_recent_activity(db: Session):
    """Test validation of recent inventory activity"""
    item = InventoryItem(
        item_number="TEST003",
        description="Test Active Item",
        category="Test",
        unit_of_measure="EA",
        is_active=True,
        quantity=20,
        unit_price=100,
        cost_price=50
    )
    db.add(item)
    db.commit()
    
    # Add recent transaction
    transaction = InventoryTransaction(
        inventory_item_id=item.id,
        transaction_date=datetime.now(),
        quantity=1
    )
    db.add(transaction)
    
    # Add recent order
    order = Order(
        order_date=datetime.now()
    )
    db.add(order)
    db.flush()
    
    order_line = OrderLine(
        order_id=order.id,
        inventory_item_id=item.id,
        quantity=1
    )
    db.add(order_line)
    db.commit()
    
    updater = InventoryMIRUpdater(db)
    issues = updater._validate_inventory(item)
    
    assert "NoRecentTransactions" not in issues
    assert "NoRecentOrders" not in issues
    
def test_execute_updates_all_items(db: Session):
    """Test execution of MIR updates for all inventory items"""
    # Create test items
    items = [
        InventoryItem(
            item_number=f"TEST{i}",
            description=f"Test Item {i}",
            category="Test",
            unit_of_measure="EA",
            is_active=True,
            quantity=10,
            unit_price=100,
            cost_price=50
        )
        for i in range(3)
    ]
    db.add_all(items)
    db.commit()
    
    # Update MIR for all items
    InventoryMIRUpdater.execute(db)
    
    # Check that MIR was updated for all items
    updated_items = db.query(InventoryItem).all()
    assert all(item.mir is not None for item in updated_items)
    
def test_execute_updates_single_item(db: Session):
    """Test execution of MIR updates for a single inventory item"""
    # Create test items
    items = [
        InventoryItem(
            item_number=f"TEST{i}",
            description=f"Test Item {i}",
            category="Test",
            unit_of_measure="EA",
            is_active=True,
            quantity=10,
            unit_price=100,
            cost_price=50
        )
        for i in range(3)
    ]
    db.add_all(items)
    db.commit()
    
    # Update MIR for single item
    target_id = items[0].id
    InventoryMIRUpdater.execute(db, target_id)
    
    # Check that only target item was updated
    updated_items = db.query(InventoryItem).all()
    assert updated_items[0].mir is not None
    assert all(item.mir is None for item in updated_items[1:])
