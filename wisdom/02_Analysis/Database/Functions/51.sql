CREATE DEFINER=`root`@`localhost` PROCEDURE `serial_order_refresh`(P_OrderID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --

  -- cursor variables
  DECLARE cur_Priority         int(11); --
  DECLARE cur_CustomerID       int(11); --
  DECLARE cur_OrderID          int(11); --
  DECLARE cur_OrderDetailsID   int(11); --
  DECLARE cur_SerialID         int(11); --
  DECLARE cur_WarehouseID      int(11); --
  DECLARE cur_TranType         varchar(50); --
  DECLARE cur_TranTime         datetime; --

  DECLARE cur CURSOR FOR
    (
     SELECT
      1 as Priority
     ,view_orderdetails.CustomerID
     ,view_orderdetails.OrderID
     ,view_orderdetails.ID as OrderDetailsID
     ,view_orderdetails.SerialID
     ,null as WarehouseID
     ,'Reserved' as TranType
     ,IFNULL(tbl_order.OrderDate, Now()) as TranTime
     FROM tbl_order
          INNER JOIN view_orderdetails ON view_orderdetails.CustomerID = tbl_order.CustomerID
                                      AND view_orderdetails.OrderID    = tbl_order.ID
          INNER JOIN tbl_serial ON view_orderdetails.SerialID        = tbl_serial.ID -- serial exists
                               AND view_orderdetails.InventoryItemID = tbl_serial.InventoryItemID
          INNER JOIN tbl_serial_transaction_type as stt ON stt.Name = 'Reserved'
          LEFT JOIN tbl_serial_transaction as LastTran ON LastTran.CustomerID     = view_orderdetails.CustomerID
                                                      AND LastTran.OrderID        = view_orderdetails.OrderID
                                                      AND LastTran.OrderDetailsID = view_orderdetails.ID
                                                      AND LastTran.TypeID         = stt.ID
          LEFT JOIN (SELECT SerialID, Max(ID) as MaxID
                     FROM tbl_serial_transaction
                     GROUP BY SerialID) as TranHistory ON LastTran.SerialID = TranHistory.SerialID
                                                      AND LastTran.ID       = TranHistory.MaxID
     WHERE (tbl_order.Approved = 0) -- we reserve only for not approved orders
       AND ((LastTran.ID IS NULL) OR (TranHistory.SerialID IS NULL))
       AND ((tbl_order.ID = P_OrderID) OR (P_OrderID IS NULL))
    ) UNION ALL (
     SELECT
      2 as Priority
     ,LastTran.CustomerID
     ,LastTran.OrderID
     ,LastTran.OrderDetailsID
     ,LastTran.SerialID
     ,null as WarehouseID
     ,'Reserve Cancelled' as TranType
     ,Now() as TranTime
     FROM (SELECT SerialID, Max(ID) as MaxID
           FROM tbl_serial_transaction
           GROUP BY SerialID) as TranHistory
          INNER JOIN tbl_serial_transaction as LastTran ON LastTran.SerialID = TranHistory.SerialID
                                                       AND LastTran.ID       = TranHistory.MaxID
          INNER JOIN tbl_serial_transaction_type ON tbl_serial_transaction_type.ID   = LastTran.TypeID
                                                AND tbl_serial_transaction_type.Name = 'Reserved'
          INNER JOIN tbl_serial ON TranHistory.SerialID = tbl_serial.ID
          LEFT JOIN view_orderdetails ON LastTran.CustomerID     =  view_orderdetails.CustomerID
                                     AND LastTran.OrderID        =  view_orderdetails.OrderID
                                     AND LastTran.OrderDetailsID =  view_orderdetails.ID
          LEFT JOIN tbl_order ON view_orderdetails.CustomerID = tbl_order.CustomerID
                             AND view_orderdetails.OrderID    = tbl_order.ID
     WHERE ((view_orderdetails.SerialID IS NULL) OR (view_orderdetails.SerialID != LastTran.SerialID))
       AND ((LastTran.OrderID = P_OrderID) OR (P_OrderID IS NULL))
    ) UNION ALL (
     SELECT DISTINCT
      3 as Priority
     ,view_orderdetails.CustomerID
     ,view_orderdetails.OrderID
     ,view_orderdetails.ID as OrderDetailsID
     ,view_orderdetails.SerialID
     ,null as WarehouseID
     ,'Rented' as TranType
     ,IFNULL(tbl_order.DeliveryDate, IFNULL(tbl_order.OrderDate, Now())) as TranTime
     FROM tbl_order
          INNER JOIN view_orderdetails ON view_orderdetails.CustomerID = tbl_order.CustomerID
                                      AND view_orderdetails.OrderID    = tbl_order.ID
          INNER JOIN tbl_serial ON view_orderdetails.SerialID        = tbl_serial.ID -- serial exists
                               AND view_orderdetails.InventoryItemID = tbl_serial.InventoryItemID
          INNER JOIN tbl_serial_transaction_type as stt ON stt.Name = 'Rented'
          LEFT JOIN tbl_serial_transaction as st ON st.CustomerID     = view_orderdetails.CustomerID
                                                AND st.OrderID        = view_orderdetails.OrderID
                                                AND st.OrderDetailsID = view_orderdetails.ID
                                                AND st.SerialID       = view_orderdetails.SerialID
                                                AND st.TypeID         = stt.ID
     WHERE (tbl_order.Approved = 1)
       AND (view_orderdetails.IsRented = 1)
       AND (st.ID IS NULL)
       AND ((tbl_order.ID = P_OrderID) OR (P_OrderID IS NULL))
    ) UNION ALL (
     SELECT DISTINCT
      3 as Priority
     ,view_orderdetails.CustomerID
     ,view_orderdetails.OrderID
     ,view_orderdetails.ID as OrderDetailsID
     ,view_orderdetails.SerialID
     ,null as WarehouseID
     ,'Sold' as TranType
     ,IFNULL(tbl_order.DeliveryDate, IFNULL(tbl_order.OrderDate, Now())) as TranTime
     FROM tbl_order
          INNER JOIN view_orderdetails ON view_orderdetails.CustomerID = tbl_order.CustomerID
                                      AND view_orderdetails.OrderID    = tbl_order.ID
          INNER JOIN tbl_serial ON view_orderdetails.SerialID        = tbl_serial.ID -- serial exists
                               AND view_orderdetails.InventoryItemID = tbl_serial.InventoryItemID
          INNER JOIN tbl_serial_transaction_type as stt ON stt.Name = 'Sold'
          LEFT JOIN tbl_serial_transaction as st ON st.CustomerID     = view_orderdetails.CustomerID
                                                AND st.OrderID        = view_orderdetails.OrderID
                                                AND st.OrderDetailsID = view_orderdetails.ID
                                                AND st.SerialID       = view_orderdetails.SerialID
                                                AND st.TypeID         = stt.ID
     WHERE (tbl_order.Approved = 1)
       AND (view_orderdetails.IsSold = 1)
       AND (st.ID IS NULL)
       AND ((tbl_order.ID = P_OrderID) OR (P_OrderID IS NULL))
    ) UNION ALL (
     SELECT DISTINCT
      4 as Priority
     ,view_orderdetails.CustomerID
     ,view_orderdetails.OrderID
     ,view_orderdetails.ID as OrderDetailsID
     ,view_orderdetails.SerialID
     ,view_orderdetails.WarehouseID
     ,'Returned' as TranType
     ,IFNULL(view_orderdetails.EndDate, Now()) as TranTime
     FROM tbl_order
          INNER JOIN view_orderdetails ON view_orderdetails.CustomerID = tbl_order.CustomerID
                                      AND view_orderdetails.OrderID    = tbl_order.ID
          INNER JOIN tbl_serial ON view_orderdetails.SerialID        = tbl_serial.ID -- serial exists
                               AND view_orderdetails.InventoryItemID = tbl_serial.InventoryItemID
          INNER JOIN tbl_serial_transaction_type as stt ON stt.Name = 'Returned'
          LEFT JOIN tbl_serial_transaction as st ON st.CustomerID     = view_orderdetails.CustomerID
                                                AND st.OrderID        = view_orderdetails.OrderID
                                                AND st.OrderDetailsID = view_orderdetails.ID
                                                AND st.SerialID       = view_orderdetails.SerialID
                                                AND st.TypeID         = stt.ID
     WHERE (tbl_order.Approved = 1)
       AND (view_orderdetails.IsCanceled = 0)
       AND (view_orderdetails.IsPickedup = 1)
       AND (view_orderdetails.IsRented = 1)
       AND (st.ID IS NULL)
       AND ((tbl_order.ID = P_OrderID) OR (P_OrderID IS NULL))
    ) UNION ALL (
     SELECT DISTINCT
      5 as Priority
     ,view_orderdetails.CustomerID
     ,view_orderdetails.OrderID
     ,view_orderdetails.ID as OrderDetailsID
     ,view_orderdetails.SerialID
     ,null as WarehouseID
     ,'Sold' as TranType
     ,IFNULL(view_orderdetails.EndDate, Now()) as TranTime
     FROM tbl_order
          INNER JOIN view_orderdetails ON view_orderdetails.CustomerID = tbl_order.CustomerID
                                      AND view_orderdetails.OrderID    = tbl_order.ID
          INNER JOIN tbl_serial ON view_orderdetails.SerialID        = tbl_serial.ID -- serial exists
                               AND view_orderdetails.InventoryItemID = tbl_serial.InventoryItemID
          INNER JOIN tbl_serial_transaction_type as stt ON stt.Name = 'Sold'
          LEFT JOIN tbl_serial_transaction as st ON st.CustomerID     = view_orderdetails.CustomerID
                                                AND st.OrderID        = view_orderdetails.OrderID
                                                AND st.OrderDetailsID = view_orderdetails.ID
                                                AND st.SerialID       = view_orderdetails.SerialID
                                                AND st.TypeID         = stt.ID
     WHERE (tbl_order.Approved = 1)
       AND (view_orderdetails.IsActive = 0)
       AND (view_orderdetails.IsCanceled = 0)
       AND (view_orderdetails.IsPickedup = 0)
       AND (view_orderdetails.IsRented = 1)
       AND (st.ID IS NULL)
       AND ((tbl_order.ID = P_OrderID) OR (P_OrderID IS NULL))
    ) ORDER BY SerialID, Priority, TranTime; --

  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO
     cur_Priority
    ,cur_CustomerID
    ,cur_OrderID
    ,cur_OrderDetailsID
    ,cur_SerialID
    ,cur_WarehouseID
    ,cur_TranType
    ,cur_TranTime; --

    IF (done = 0) THEN
      CALL serial_add_transaction(
          cur_TranType       -- P_TranType         VARCHAR(50)
        , cur_TranTime       -- P_TranTime         DATETIME
        , cur_SerialID       -- P_SerialID         INT,
        , cur_WarehouseID    -- P_WarehouseID      INT,
        , null               -- P_VendorID         INT,
        , cur_CustomerID     -- P_CustomerID       INT,
        , cur_OrderID        -- P_OrderID          INT,
        , cur_OrderDetailsID -- P_OrderDetailsID   INT,
        , null               -- P_LotNumber        VARCHAR(50),
        , 1                  -- P_LastUpdateUserID INT
      ); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END