CREATE DEFINER=`root`@`localhost` PROCEDURE `serial_transfer`(
  P_SerialID INT
, P_SrcWarehouseID   INT
, P_DstWarehouseID   INT
, P_LastUpdateUserID INT
)
BEGIN
  DECLARE V_SerialID, V_InventoryItemID, V_CountBefore, V_CountAfter INT; --

  SELECT tbl_serial.ID, tbl_serial.InventoryItemID
  INTO V_SerialID, V_InventoryItemID
  FROM tbl_serial
  WHERE ID = P_SerialID; --

  IF (V_SerialID IS NOT NULL) THEN
    SELECT Count(*)
    INTO V_CountBefore
    FROM tbl_serial_transaction
    WHERE SerialID = V_SerialID; --

    CALL serial_add_transaction(
       'Transferred Out'  -- P_TranType         VARCHAR(50),
      ,Now()              -- P_TranTime         DATETIME,
      ,V_SerialID         -- P_SerialID         INT,
      ,P_SrcWarehouseID   -- P_WarehouseID      INT,
      ,null               -- P_VendorID         INT,
      ,null               -- P_CustomerID       INT,
      ,null               -- P_OrderID          INT,
      ,null               -- P_OrderDetailsID   INT,
      ,null               -- P_LotNumber        VARCHAR(50),
      ,P_LastUpdateUserID -- P_LastUpdateUserID INT
      ); --

    CALL serial_add_transaction(
       'Transferred In'   -- P_TranType         VARCHAR(50),
      ,Now()              -- P_TranTime         DATETIME,
      ,V_SerialID         -- P_SerialID         INT,
      ,P_DstWarehouseID   -- P_WarehouseID      INT,
      ,null               -- P_VendorID         INT,
      ,null               -- P_CustomerID       INT,
      ,null               -- P_OrderID          INT,
      ,null               -- P_OrderDetailsID   INT,
      ,null               -- P_LotNumber        VARCHAR(50),
      ,P_LastUpdateUserID -- P_LastUpdateUserID INT
      ); --

    SELECT Count(*)
    INTO V_CountAfter
    FROM tbl_serial_transaction
    WHERE SerialID = V_SerialID; --

    IF V_CountAfter - V_CountBefore = 2 THEN
      CALL internal_inventory_transfer(
        V_InventoryItemID
      , P_SrcWarehouseID
      , P_DstWarehouseID
      , 1
      , CONCAT('Serial #', V_SerialID, ' Transfer')
      , P_LastUpdateUserID); --
    END IF; --
  END IF; --
END