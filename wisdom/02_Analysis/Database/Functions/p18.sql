CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_transaction_po_refresh`(P_PurchaseOrderID INT, P_Type VARCHAR(50))
BEGIN
  -- 'Ordered'
  -- 'Received'
  -- 'BackOrdered'
  UPDATE tbl_inventory_transaction as tran
         INNER JOIN tbl_purchaseorderdetails as podetails ON tran.WarehouseID = podetails.WarehouseID
                                                         AND tran.InventoryItemID = podetails.InventoryItemID
                                                         AND tran.PurchaseOrderID = podetails.PurchaseOrderID
                                                         AND tran.PurchaseOrderDetailsID = podetails.ID
         INNER JOIN tbl_purchaseorder as po ON podetails.PurchaseOrderID = po.ID
         INNER JOIN tbl_inventory_transaction_type ON tbl_inventory_transaction_type.ID   = tran.TypeID
                                                  AND tbl_inventory_transaction_type.Name = P_Type
  SET tran.Date = CASE P_Type WHEN 'Ordered'     THEN IFNULL(po.OrderDate   , CURRENT_DATE())
                              WHEN 'Received'    THEN IFNULL(podetails.DateReceived, CURRENT_DATE())
                              WHEN 'BackOrdered' THEN IFNULL(podetails.DateReceived, CURRENT_DATE())
                              ELSE 0 END,
      tran.Quantity = CASE P_Type WHEN 'Ordered'     THEN podetails.Ordered
                                  WHEN 'Received'    THEN podetails.Received
                                  WHEN 'BackOrdered' THEN podetails.Ordered - podetails.Received
                                  ELSE 0 END,
      tran.Cost = CASE P_Type WHEN 'Ordered'     THEN 0
                              WHEN 'Received'    THEN IFNULL(podetails.Received, 0) * IFNULL(podetails.Price, 0)
                              WHEN 'BackOrdered' THEN 0
                              ELSE 0 END,
      tran.Description = CONCAT('PO #', podetails.PurchaseOrderID),
      tran.SerialID = NULL,
      tran.VendorID = po.VendorID,
      tran.CustomerID = NULL,
      tran.InvoiceID  = NULL,
      tran.ManufacturerID = NULL,
      tran.OrderDetailsID = NULL,
      tran.LastUpdateUserID = po.LastUpdateUserID
  WHERE (po.ID = P_PurchaseOrderID)
    AND (po.Approved = 1)
    AND CASE P_Type WHEN 'Ordered'     THEN (0 < podetails.Ordered)
                    WHEN 'Received'    THEN (0 < podetails.Ordered) AND (0 < podetails.Received)
                    WHEN 'BackOrdered' THEN (0 < podetails.Ordered) AND (0 < podetails.Received) -- AND (podetails.Received < podetails.Ordered)
                    ELSE 0 END; --

  INSERT INTO tbl_inventory_transaction
  (WarehouseID,
   InventoryItemID,
   TypeID,
   Date,
   Quantity,
   Cost,
   Description,
   SerialID,
   VendorID,
   CustomerID,
   LastUpdateUserID,
   PurchaseOrderID,
   PurchaseOrderDetailsID,
   InvoiceID,
   ManufacturerID,
   OrderDetailsID)
  SELECT podetails.WarehouseID,
         podetails.InventoryItemID,
         tran_type.ID as TypeID,
         CASE P_Type WHEN 'Ordered'     THEN IFNULL(po.OrderDate   , CURRENT_DATE())
                     WHEN 'Received'    THEN IFNULL(podetails.DateReceived, CURRENT_DATE())
                     WHEN 'BackOrdered' THEN IFNULL(podetails.DateReceived, CURRENT_DATE())
                     ELSE 0 END as Date,
         CASE P_Type WHEN 'Ordered'     THEN podetails.Ordered
                     WHEN 'Received'    THEN podetails.Received
                     WHEN 'BackOrdered' THEN podetails.Ordered - podetails.Received
                     ELSE 0 END as Quantity,
         CASE P_Type WHEN 'Ordered'     THEN 0
                     WHEN 'Received'    THEN IFNULL(podetails.Received, 0) * IFNULL(podetails.Price, 0)
                     WHEN 'BackOrdered' THEN 0
                     ELSE 0 END as Cost,
         CONCAT('PO #', podetails.PurchaseOrderID) as Description,
         NULL as SerialID,
         po.VendorID,
         NULL as CustomerID,
         po.LastUpdateUserID,
         podetails.PurchaseOrderID,
         podetails.ID as PurchaseOrderDetailsID,
         NULL as InvoiceID,
         NULL as ManufacturerID,
         NULL as OrderDetailsID
  FROM tbl_purchaseorderdetails as podetails
       INNER JOIN tbl_purchaseorder as po ON podetails.PurchaseOrderID = po.ID
       INNER JOIN tbl_inventory_transaction_type as tran_type ON tran_type.Name = P_Type
       LEFT JOIN tbl_inventory_transaction as tran ON tran.WarehouseID = podetails.WarehouseID
                                                  AND tran.InventoryItemID = podetails.InventoryItemID
                                                  AND tran.PurchaseOrderID = podetails.PurchaseOrderID
                                                  AND tran.PurchaseOrderDetailsID = podetails.ID
                                                  AND tran.TypeID = tran_type.ID
  WHERE (po.ID = P_PurchaseOrderID)
    AND (po.Approved = 1)
    AND (tran.ID IS NULL)
    AND CASE P_Type WHEN 'Ordered'     THEN (0 < podetails.Ordered)
                    WHEN 'Received'    THEN (0 < podetails.Ordered) AND (0 < podetails.Received)
                    WHEN 'BackOrdered' THEN (0 < podetails.Ordered) AND (0 < podetails.Received) -- AND (podetails.Received < podetails.Ordered)
                    ELSE 0 END; --
END