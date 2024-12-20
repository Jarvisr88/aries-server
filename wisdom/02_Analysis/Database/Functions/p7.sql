CREATE DEFINER=`root`@`localhost` PROCEDURE `serials_po_refresh`(P_PurchaseOrderID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE V_SerialID, V_VendorID, V_InventoryItemID, V_WarehouseID INT; --
  DECLARE V_ReceivedDate DATETIME; --
  DECLARE V_ReceivedQuantity, V_SerialCount INT; --
  DECLARE V_PurchasePrice decimal(18, 2); --
  DECLARE cur CURSOR FOR
      SELECT
        tbl_purchaseorder.VendorID,
        tbl_purchaseorderdetails.InventoryItemID,
        tbl_purchaseorderdetails.WarehouseID,
        MAX(tbl_purchaseorderdetails.DateReceived) as ReceivedDate,
        SUM(tbl_purchaseorderdetails.Received) as ReceivedQuantity,
        tbl_purchaseorderdetails.Price as PurchasePrice
      FROM tbl_purchaseorder
           INNER JOIN tbl_purchaseorderdetails ON tbl_purchaseorder.ID = tbl_purchaseorderdetails.PurchaseOrderID
           INNER JOIN tbl_inventoryitem ON tbl_purchaseorderdetails.InventoryItemID = tbl_inventoryitem.ID
      WHERE (tbl_purchaseorder.ID = P_PurchaseOrderID)
        AND (tbl_inventoryitem.Serialized = 1)
      GROUP BY tbl_purchaseorder.VendorID, tbl_purchaseorderdetails.InventoryItemID, tbl_purchaseorderdetails.WarehouseID; --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  DROP TABLE IF EXISTS `{A890A925-A355-44AA-AA99-D28A52F7DF0D}`; --

  CREATE TEMPORARY TABLE `{A890A925-A355-44AA-AA99-D28A52F7DF0D}` (SerialID INT); --

  IF EXISTS (SELECT * FROM tbl_purchaseorder WHERE Approved = 1 AND ID = P_PurchaseOrderID) THEN
    OPEN cur; --

    REPEAT
      FETCH cur INTO
        V_VendorID,
        V_InventoryItemID,
        V_WarehouseID,
        V_ReceivedDate,
        V_ReceivedQuantity,
        V_PurchasePrice; --

      IF NOT done THEN
        SET V_SerialCount = V_ReceivedQuantity; --

        SELECT Count(*)
        INTO V_SerialCount
        FROM tbl_serial
        WHERE (WarehouseID = V_WarehouseID)
          AND (InventoryItemID = V_InventoryItemID)
          AND (VendorID = V_VendorID)
          AND (PurchaseOrderID = P_PurchaseOrderID); --

        WHILE (V_SerialCount < V_ReceivedQuantity) DO
          INSERT INTO tbl_serial (WarehouseID, InventoryItemID, VendorID, PurchaseOrderID, PurchaseDate, PurchaseAmount, Status)
          VALUES (V_WarehouseID, V_InventoryItemID, V_VendorID, P_PurchaseOrderID, V_ReceivedDate, V_PurchasePrice, 'On Hand'); --

          SELECT LAST_INSERT_ID() INTO V_SerialID; --

          INSERT INTO `{A890A925-A355-44AA-AA99-D28A52F7DF0D}` (SerialID) VALUES (V_SerialID); --

          SET V_SerialCount = V_SerialCount + 1; --
        END WHILE; --
      END IF; --
    UNTIL done END REPEAT; --

    CLOSE cur; --
  END IF; --

  SELECT SerialID FROM `{A890A925-A355-44AA-AA99-D28A52F7DF0D}`; --

  DROP TABLE `{A890A925-A355-44AA-AA99-D28A52F7DF0D}`; --
END