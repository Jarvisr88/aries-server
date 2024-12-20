CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_transfer`(
  P_InventoryItemID   INT
, P_SrcWarehouseID   INT
, P_DstWarehouseID   INT
, P_Quantity         INT
, P_LastUpdateUserID INT)
BEGIN
  CALL internal_inventory_transfer(
    P_InventoryItemID
  , P_SrcWarehouseID
  , P_DstWarehouseID
  , P_Quantity
  , 'Inventory Transfer'
  , P_LastUpdateUserID); --
END