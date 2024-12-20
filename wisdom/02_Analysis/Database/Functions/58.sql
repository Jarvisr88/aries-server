CREATE DEFINER=`root`@`localhost` PROCEDURE `serial_refresh`(P_SerialID INT)
BEGIN
  CALL serial_add_transaction
  ( null       -- P_TranType         VARCHAR(50)
  , null       -- P_TranTime         DATETIME
  , P_SerialID -- P_SerialID         INT
  , null       -- P_WarehouseID      INT
  , null       -- P_VendorID         INT
  , null       -- P_CustomerID       INT
  , null       -- P_OrderID          INT
  , null       -- P_OrderDetailsID   INT
  , null       -- P_LotNumber        VARCHAR(50)
  , null       -- P_LastUpdateUserID INT
  ); --
END