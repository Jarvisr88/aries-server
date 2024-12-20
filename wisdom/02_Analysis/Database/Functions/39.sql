CREATE DEFINER=`root`@`localhost` PROCEDURE `internal_inventory_transfer`(
  P_InventoryItemID  INT
, P_SrcWarehouseID   INT
, P_DstWarehouseID   INT
, P_Quantity         INT
, P_Description      VARCHAR(30)
, P_LastUpdateUserID INT)
BEGIN
  DECLARE
    V_OnHand INT; --
  DECLARE
    V_CostPerUnit DECIMAL(18, 2); --

  IF (P_InventoryItemID IS NOT NULL)
  AND (P_SrcWarehouseID IS NOT NULL)
  AND (P_DstWarehouseID IS NOT NULL)
  AND (0 < IFNULL(P_Quantity, 0)) THEN
    CALL inventory_refresh(P_SrcWarehouseID, P_InventoryItemID); --

    SELECT
      IFNULL(OnHand     , 0) as OnHand
    , IFNULL(CostPerUnit, 0) as CostPerUnit
    INTO
      V_OnHand
    , V_CostPerUnit
    FROM tbl_inventory
    WHERE (InventoryItemID = P_InventoryItemID)
      AND (WarehouseID     = P_SrcWarehouseID); --

    IF (P_Quantity <= V_OnHand) THEN
      CALL inventory_transaction_add_adjustment(
        P_SrcWarehouseID,
        P_InventoryItemID,
        'Transferred Out',
        P_Description,
        P_Quantity,
        V_CostPerUnit,
        P_LastUpdateUserID); --

      CALL inventory_transaction_add_adjustment(
        P_DstWarehouseID,
        P_InventoryItemID,
        'Transferred In',
        P_Description,
        P_Quantity,
        V_CostPerUnit,
        P_LastUpdateUserID); --

      CALL inventory_refresh(P_SrcWarehouseID, P_InventoryItemID); --
      CALL inventory_refresh(P_DstWarehouseID, P_InventoryItemID); --
    END IF; --
  END IF; --
END