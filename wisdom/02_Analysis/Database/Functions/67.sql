CREATE DEFINER=`root`@`localhost` PROCEDURE `inventory_refresh`(P_WarehouseID INT, P_InventoryItemID INT)
BEGIN
  DECLARE
    V_WarehouseID,
    V_InventoryItemID INT; --
  DECLARE
    V_OnHand,
    V_Committed,
    V_OnOrder,
    V_UnAvailable,
    V_Rented,
    V_Sold,
    V_BackOrdered INT; --
  DECLARE
    V_UnitPrice DECIMAL(18, 2); --

  DECLARE done INT DEFAULT 0; --
  DECLARE cur CURSOR FOR
      SELECT
        summary.WarehouseID
      , summary.InventoryItemID
      , IF(item.Service = 0, IFNULL(summary.OnHand      , 0), 0) as OnHand
      , IF(item.Service = 0, IFNULL(summary.Committed   , 0), 0) as Committed
      , IF(item.Service = 0, IFNULL(summary.OnOrder     , 0), 0) as OnOrder
      , IF(item.Service = 0, IFNULL(summary.UnAvailable , 0), 0) as UnAvailable
      , IF(item.Service = 0, IFNULL(summary.Rented      , 0), 0) as Rented
      , IF(item.Service = 0, IFNULL(summary.Sold        , 0), 0) as Sold
      , IF(item.Service = 0, IFNULL(summary.BackOrdered , 0), 0) as BackOrdered
      , IF(item.Service = 0, IFNULL(tran.Cost / tran.Quantity, IFNULL(summary.TotalCost / summary.TotalQuantity, 0)), 0) as UnitPrice
      FROM (SELECT
              tran.WarehouseID
            , tran.InventoryItemID
            , SUM(CASE WHEN tran_type.OnHand       > 0 THEN tran.Quantity WHEN tran_type.OnHand       < 0 THEN -tran.Quantity ELSE null END) as OnHand
            , SUM(CASE WHEN tran_type.Committed    > 0 THEN tran.Quantity WHEN tran_type.Committed    < 0 THEN -tran.Quantity ELSE null END) as Committed
            , SUM(CASE WHEN tran_type.OnOrder      > 0 THEN tran.Quantity WHEN tran_type.OnOrder      < 0 THEN -tran.Quantity ELSE null END) as OnOrder
            , SUM(CASE WHEN tran_type.UnAvailable  > 0 THEN tran.Quantity WHEN tran_type.UnAvailable  < 0 THEN -tran.Quantity ELSE null END) as UnAvailable
            , SUM(CASE WHEN tran_type.Rented       > 0 THEN tran.Quantity WHEN tran_type.Rented       < 0 THEN -tran.Quantity ELSE null END) as Rented
            , SUM(CASE WHEN tran_type.Sold         > 0 THEN tran.Quantity WHEN tran_type.Sold         < 0 THEN -tran.Quantity ELSE null END) as Sold
            , SUM(CASE WHEN tran_type.BackOrdered  > 0 THEN tran.Quantity WHEN tran_type.BackOrdered  < 0 THEN -tran.Quantity ELSE null END) as BackOrdered
            , SUM(IF(tran_type.AdjTotalCost = 1, tran.Cost    , null)) as TotalCost
            , SUM(IF(tran_type.AdjTotalCost = 1, tran.Quantity, null)) as TotalQuantity
            , MAX(IF(tran_type.Name = 'CostPerUnit Adj', tran.ID, null)) as LastAdjustID
            FROM tbl_inventory_transaction as tran
                 INNER JOIN tbl_inventory_transaction_type as tran_type ON tran.TypeID = tran_type.ID
            WHERE ((P_WarehouseID     IS NULL) OR (tran.WarehouseID     = P_WarehouseID    ))
              AND ((P_InventoryItemID IS NULL) OR (tran.InventoryItemID = P_InventoryItemID))
            GROUP BY tran.WarehouseID, tran.InventoryItemID) as summary
      LEFT JOIN tbl_inventory_transaction as tran ON tran.ID              = summary.LastAdjustID
                                                 AND tran.WarehouseID     = summary.WarehouseID
                                                 AND tran.InventoryItemID = summary.InventoryItemID
      INNER JOIN tbl_inventoryitem as item ON item.ID = summary.InventoryItemID
      WHERE (1 = 1); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO
      V_WarehouseID
    , V_InventoryItemID
    , V_OnHand
    , V_Committed
    , V_OnOrder
    , V_UnAvailable
    , V_Rented
    , V_Sold
    , V_BackOrdered
    , V_UnitPrice; --

    IF NOT done THEN
      UPDATE tbl_inventory SET
       OnHand           = V_OnHand
      ,Committed        = V_Committed
      ,OnOrder          = V_OnOrder
      ,UnAvailable      = V_UnAvailable
      ,Rented           = V_Rented
      ,Sold             = V_Sold
      ,BackOrdered      = V_BackOrdered
      ,CostPerUnit      = V_UnitPrice
      ,TotalCost        = V_UnitPrice * (V_OnHand + V_Rented + V_UnAvailable)
      ,LastUpdateUserID = 1
      WHERE (WarehouseID     = V_WarehouseID)
        AND (InventoryItemID = V_InventoryItemID); --

      IF (ROW_COUNT() = 0) THEN
        INSERT IGNORE INTO tbl_inventory SET
         OnHand           = V_OnHand
        ,Committed        = V_Committed
        ,OnOrder          = V_OnOrder
        ,UnAvailable      = V_UnAvailable
        ,Rented           = V_Rented
        ,Sold             = V_Sold
        ,BackOrdered      = V_BackOrdered
        ,CostPerUnit      = V_UnitPrice
        ,TotalCost        = V_UnitPrice * (V_OnHand + V_Rented + V_UnAvailable)
        ,LastUpdateUserID = 1
        ,ReOrderPoint     = 0
        ,WarehouseID      = V_WarehouseID
        ,InventoryItemID  = V_InventoryItemID; --
      END IF; --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END