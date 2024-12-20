CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_transaction_order_refresh`(P_OrderID INT)
BEGIN
  -- type:
  -- Committed
  -- Sold
  -- Rented
  -- Rental Returned
  -- since user with necessary permissions have ability to set Approved = False
  -- we need to delete all transactions for not approved order
  -- and check all warehouses for it.

  -- if something was severily changed we need to delete
  DELETE tran
  FROM tbl_inventory_transaction as tran
       LEFT JOIN view_orderdetails as d ON tran.InventoryItemID = d.InventoryItemID
                                       AND tran.WarehouseID     = d.WarehouseID
                                       AND tran.CustomerID      = d.CustomerID
                                       AND tran.OrderID         = d.OrderID
                                       AND tran.OrderDetailsID  = d.ID
       LEFT JOIN tbl_order as o ON d.OrderID    = o.ID
                               AND d.CustomerID = o.CustomerID
  WHERE (tran.OrderID = P_OrderID)
    AND (o.ID IS NULL); --

  -- if transaction type does not correspond to the state of order we need to delete
  DELETE tran
  FROM tbl_inventory_transaction as tran
       INNER JOIN view_orderdetails as d ON tran.InventoryItemID = d.InventoryItemID
                                        AND tran.WarehouseID     = d.WarehouseID
                                        AND tran.CustomerID      = d.CustomerID
                                        AND tran.OrderID         = d.OrderID
                                        AND tran.OrderDetailsID  = d.ID
       INNER JOIN tbl_order as o ON d.OrderID    = o.ID
                                AND d.CustomerID = o.CustomerID
       INNER JOIN tbl_inventory_transaction_type as tt ON tt.ID = tran.TypeID
  WHERE (tran.OrderID = P_OrderID)
    AND NOT CASE tt.Name WHEN 'Committed'       THEN 1
                         WHEN 'Sold'            THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsSold
                         WHEN 'Rented'          THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsRented
                         WHEN 'Rental Returned' THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsRented AND d.IsPickedup
                         ELSE 0 END; --

  -- if transaction were not removed we have to update it to sync with order
  UPDATE tbl_inventory_transaction as tran
         INNER JOIN view_orderdetails as d ON tran.WarehouseID     = d.WarehouseID
                                          AND tran.InventoryItemID = d.InventoryItemID
                                          AND tran.CustomerID      = d.CustomerID
                                          AND tran.OrderID         = d.OrderID
                                          AND tran.OrderDetailsID  = d.ID
         INNER JOIN tbl_order as o ON d.OrderID = o.ID
                                  AND d.CustomerID = o.CustomerID
         INNER JOIN tbl_inventory_transaction_type as tt ON tt.ID = tran.TypeID
  SET tran.Date        = IFNULL(o.OrderDate, CURRENT_DATE()),
      tran.Quantity    = d.DeliveryQuantity,
      tran.Description = CONCAT('Order #', d.OrderID),
      tran.Cost        = 0,
      tran.SerialID    = NULL,
      tran.VendorID    = NULL,
      tran.InvoiceID   = NULL,
      tran.ManufacturerID = NULL,
      tran.LastUpdateUserID = o.LastUpdateUserID
  WHERE (o.ID = P_OrderID)
    AND CASE tt.Name WHEN 'Committed'       THEN 1
                     WHEN 'Sold'            THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsSold
                     WHEN 'Rented'          THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsRented
                     WHEN 'Rental Returned' THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsRented AND d.IsPickedup
                     ELSE 0 END; --

  INSERT INTO tbl_inventory_transaction
    (WarehouseID
    ,InventoryItemID
    ,TypeID
    ,Date
    ,Quantity
    ,Cost
    ,Description
    ,CustomerID
    ,OrderID
    ,OrderDetailsID
    ,LastUpdateUserID
    ,SerialID
    ,VendorID
    ,PurchaseOrderID
    ,PurchaseOrderDetailsID
    ,InvoiceID
    ,ManufacturerID)
  SELECT d.WarehouseID,
         d.InventoryItemID,
         tt.ID as TypeID,
         IFNULL(o.OrderDate, CURRENT_DATE()) as Date,
         d.DeliveryQuantity as Quantity,
         0 as Cost,
         CONCAT('Order #', d.OrderID) as Description,
         d.CustomerID,
         d.OrderID,
         d.ID as OrderDetailsID,
         o.LastUpdateUserID,
         NULL as SerialID,
         NULL as VendorID,
         NULL as PurchaseOrderID,
         NULL as PurchaseOrderDetailsID,
         NULL as InvoiceID,
         NULL as ManufacturerID
  FROM view_orderdetails as d
       INNER JOIN tbl_order as o ON d.OrderID    = o.ID
                                AND d.CustomerID = o.CustomerID
       INNER JOIN tbl_inventory_transaction_type as tt ON tt.Name IN ('Committed', 'Sold', 'Rented', 'Rental Returned')
       LEFT JOIN tbl_inventory_transaction as tran ON tran.WarehouseID     = d.WarehouseID
                                                  AND tran.InventoryItemID = d.InventoryItemID
                                                  AND tran.CustomerID      = d.CustomerID
                                                  AND tran.OrderID         = d.OrderID
                                                  AND tran.OrderDetailsID  = d.ID
                                                  AND tran.TypeID          = tt.ID
  WHERE (o.ID = P_OrderID)
    AND (tran.ID IS NULL)
    AND CASE tt.Name WHEN 'Committed'       THEN 1
                     WHEN 'Sold'            THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsSold
                     WHEN 'Rented'          THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsRented
                     WHEN 'Rental Returned' THEN (o.Approved = 1) AND (o.DeliveryDate IS NOT NULL) AND d.IsRented AND d.IsPickedup
                     ELSE 0 END; --
END