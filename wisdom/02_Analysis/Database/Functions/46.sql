CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_adjust_2`(
  P_WarehouseID INT
, P_InventoryItemID INT
, P_OnHand INT
, P_Rented INT
, P_Sold INT
, P_Unavailable INT
, P_Committed INT
, P_OnOrder INT
, P_BackOrdered INT
, P_ReOrderPoint INT
, P_CostPerUnit DECIMAL(18, 2)
, P_LastUpdateUserID INT)
BEGIN
  DECLARE
    V_DeltaOnHand
  , V_DeltaRented
  , V_DeltaSold
  , V_DeltaUnavailable
  , V_DeltaCommitted
  , V_DeltaOnOrder
  , V_DeltaBackOrdered INT; --
  DECLARE
    V_CostPerUnit DECIMAL(18, 2); --

  IF (P_WarehouseID IS NOT NULL) AND (P_InventoryItemID IS NOT NULL) THEN
    CALL inventory_refresh(P_WarehouseID, P_InventoryItemID); --

    /* in case when this entry does not have any transactions */
    SET V_DeltaOnHand        = IF(0 <= IFNULL(P_OnHand     , -1), P_OnHand      - 0, NULL); --
    SET V_DeltaRented        = IF(0 <= IFNULL(P_Rented     , -1), P_Rented      - 0, NULL); --
    SET V_DeltaSold          = IF(0 <= IFNULL(P_Sold       , -1), P_Sold        - 0, NULL); --
    SET V_DeltaUnavailable   = IF(0 <= IFNULL(P_Unavailable, -1), P_Unavailable - 0, NULL); --
    SET V_DeltaCommitted     = IF(0 <= IFNULL(P_Committed  , -1), P_Committed   - 0, NULL); --
    SET V_DeltaOnOrder       = IF(0 <= IFNULL(P_OnOrder    , -1), P_OnOrder     - 0, NULL); --
    SET V_DeltaBackOrdered   = IF(0 <= IFNULL(P_BackOrdered, -1), P_BackOrdered - 0, NULL); --
    SET V_CostPerUnit        = P_CostPerUnit; --

    SELECT
      IF(0 <= IFNULL(P_OnHand     , -1), P_OnHand      - IFNULL(OnHand     , 0), NULL) as DeltaOnHand
    , IF(0 <= IFNULL(P_Rented     , -1), P_Rented      - IFNULL(Rented     , 0), NULL) as DeltaRented
    , IF(0 <= IFNULL(P_Sold       , -1), P_Sold        - IFNULL(Sold       , 0), NULL) as DeltaSold
    , IF(0 <= IFNULL(P_Unavailable, -1), P_Unavailable - IFNULL(Unavailable, 0), NULL) as DeltaUnavailable
    , IF(0 <= IFNULL(P_Committed  , -1), P_Committed   - IFNULL(Committed  , 0), NULL) as DeltaCommitted
    , IF(0 <= IFNULL(P_OnOrder    , -1), P_OnOrder     - IFNULL(OnOrder    , 0), NULL) as DeltaOnOrder
    , IF(0 <= IFNULL(P_BackOrdered, -1), P_BackOrdered - IFNULL(BackOrdered, 0), NULL) as DeltaBackOrdered
    , CostPerUnit
    INTO
      V_DeltaOnHand
    , V_DeltaRented
    , V_DeltaSold
    , V_DeltaUnavailable
    , V_DeltaCommitted
    , V_DeltaOnOrder
    , V_DeltaBackOrdered
    , V_CostPerUnit
    FROM tbl_inventory
    WHERE (WarehouseID     = P_WarehouseID)
      AND (InventoryItemID = P_InventoryItemID); --

    SET V_CostPerUnit = IFNULL(P_CostPerUnit, IFNULL(V_CostPerUnit, 0)); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'OnHand Adjustment',
      'Manual Adjustment',
      IFNULL(V_DeltaOnHand, 0) + IFNULL(V_DeltaCommitted, 0) + IF(V_DeltaOnOrder < 0, V_DeltaOnOrder, 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Rented Adjustment',
      'Manual Adjustment',
      V_DeltaRented,
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Sold Adjustment',
      'Manual Adjustment',
      V_DeltaSold,
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Unavailable Adj',
      'Manual Adjustment',
      0 - V_DeltaUnavailable,
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Committed',
      'Manual Adjustment',
      IF(0 < V_DeltaCommitted, ABS(V_DeltaCommitted), 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Commit Cancelled',
      'Manual Adjustment',
      IF(V_DeltaCommitted < 0, ABS(V_DeltaCommitted), 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Ordered',
      'Manual Adjustment',
      IF(0 < V_DeltaOnOrder, ABS(V_DeltaOnOrder), 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Received',
      'Manual Adjustment',
      IF(V_DeltaOnOrder < 0, ABS(V_DeltaOnOrder), 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'BackOrdered',
      'Manual Adjustment',
      IF(0 < V_DeltaBackOrdered, ABS(V_DeltaBackOrdered), 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    CALL inventory_transaction_add_adjustment(
      P_WarehouseID,
      P_InventoryItemID,
      'Fill Back Order',
      'Manual Adjustment',
      IF(V_DeltaBackOrdered < 0, ABS(V_DeltaBackOrdered), 0),
      V_CostPerUnit,
      P_LastUpdateUserID); --

    IF (0 < IFNULL(P_CostPerUnit, -1)) THEN
      CALL inventory_transaction_add_adjustment(
        P_WarehouseID,
        P_InventoryItemID,
        'CostPerUnit Adj',
        'Manual Adjustment',
        1, -- to satisfy quantity check
        P_CostPerUnit,
        P_LastUpdateUserID); --
    END IF; --

    IF (0 <= IFNULL(P_ReOrderPoint, -1)) THEN
      UPDATE tbl_inventory
      SET ReOrderPoint = P_ReOrderPoint
      WHERE (WarehouseID     = P_WarehouseID)
        AND (InventoryItemID = P_InventoryItemID); --
    END IF; --

    CALL inventory_refresh(P_WarehouseID, P_InventoryItemID); --
  END IF; --
END