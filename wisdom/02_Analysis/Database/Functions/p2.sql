CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_transaction_order_cleanup`()
BEGIN
  -- delete transactions if corresponding orders or line items do not exist
  DELETE tran
  FROM tbl_inventory_transaction as tran
       LEFT JOIN view_orderdetails as d ON tran.InventoryItemID = d.InventoryItemID
                                       AND tran.WarehouseID     = d.WarehouseID
                                       AND tran.CustomerID      = d.CustomerID
                                       AND tran.OrderID         = d.OrderID
                                       AND tran.OrderDetailsID  = d.ID
       LEFT JOIN tbl_order as o ON d.OrderID    = o.ID
                               AND d.CustomerID = o.CustomerID
  WHERE (tran.OrderID IS NOT NULL)
    AND (o.ID IS NULL); --
END