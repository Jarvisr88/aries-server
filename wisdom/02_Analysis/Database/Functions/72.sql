CREATE DEFINER=`root`@`localhost` PROCEDURE `serial_update_transaction`( P_TransactionID    INT
, P_TranTime         DATETIME
, P_WarehouseID      INT
, P_VendorID         INT
, P_CustomerID       INT
, P_LotNumber        VARCHAR(50)
, P_LastUpdateUserID INT
)
BEGIN
  DECLARE V_SerialID INT; --

  SELECT SerialID
  INTO V_SerialID
  FROM tbl_serial_transaction
  WHERE ID = P_TransactionID; --

  IF V_SerialID IS NOT NULL THEN
    UPDATE tbl_serial_transaction SET
      TransactionDatetime = IFNULL(P_TranTime, Now())
    , VendorID            = P_VendorID
    , WarehouseID         = P_WarehouseID
    , CustomerID          = IF(OrderID IS NOT NULL OR OrderDetailsID IS NOT NULL, CustomerID, P_CustomerID)
    , LotNumber           = IFNULL(P_LotNumber, '')
    , LastUpdateDatetime  = Now()
    , LastUpdateUserID    = IFNULL(P_LastUpdateUserID, 1) -- root
    WHERE ID = P_TransactionID; --

    CALL serial_refresh(V_SerialID); --
  END IF; --
END