CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_transaction_add_adjustment`(
  P_WarehouseID INT,
  P_InventoryItemID INT,
  P_Type VARCHAR(50),
  P_Description VARCHAR(30),
  P_Quantity INT,
  P_CostPerUnit DECIMAL(18, 2),
  P_LastUpdateUserID INT)
BEGIN
  DECLARE V_TranTypeID INT; --

  IF (P_WarehouseID IS NOT NULL) AND (P_InventoryItemID IS NOT NULL) AND (IFNULL(P_Quantity, 0) != 0) THEN
    SELECT ID
    INTO V_TranTypeID
    FROM tbl_inventory_transaction_type
    WHERE (Name = P_Type); --

    IF (V_TranTypeID IS NOT NULL) THEN
      INSERT INTO tbl_inventory_transaction SET
       WarehouseID            = P_WarehouseID
      ,InventoryItemID        = P_InventoryItemID
      ,TypeID                 = V_TranTypeID
      ,Date                   = Now()
      ,Quantity               = P_Quantity
      ,Cost                   = P_Quantity * P_CostPerUnit
      ,Description            = IFNULL(P_Description, 'No Description')
      ,SerialID               = NULL
      ,VendorID               = NULL
      ,CustomerID             = NULL
      ,LastUpdateUserID       = P_LastUpdateUserID
      ,LastUpdateDatetime     = Now()
      ,PurchaseOrderID        = NULL
      ,PurchaseOrderDetailsID = NULL
      ,InvoiceID              = NULL
      ,ManufacturerID         = NULL
      ,OrderID                = NULL
      ,OrderDetailsID         = NULL; --
    END IF; --
  END IF; --
END