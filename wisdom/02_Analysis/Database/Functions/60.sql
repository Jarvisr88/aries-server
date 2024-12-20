CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_po_refresh`(P_PurchaseOrderID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE V_WarehouseID, V_InventoryItemID INT; --
  DECLARE cur CURSOR FOR SELECT WarehouseID, InventoryItemID FROM tbl_purchaseorderdetails WHERE (PurchaseOrderID = P_PurchaseOrderID); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO V_WarehouseID, V_InventoryItemID; --

    IF NOT done THEN
      CALL inventory_refresh(V_WarehouseID, V_InventoryItemID); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END