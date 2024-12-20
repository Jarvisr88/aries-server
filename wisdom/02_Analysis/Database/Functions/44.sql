CREATE DEFINER=`root`@`localhost` PROCEDURE `serial_add_transaction`( P_TranType         VARCHAR(50)
, P_TranTime         DATETIME
, P_SerialID         INT
, P_WarehouseID      INT
, P_VendorID         INT
, P_CustomerID       INT
, P_OrderID          INT
, P_OrderDetailsID   INT
, P_LotNumber        VARCHAR(50)
, P_LastUpdateUserID INT
)
BEGIN
  DECLARE done INT DEFAULT 0; --

  -- cursor variables
  DECLARE cur_TranID             int(11); --
  DECLARE cur_TranExists         int(11); --
  DECLARE cur_TranTypeID         int(11); --
  DECLARE cur_TranType           varchar(50); --
  DECLARE cur_TranTime           datetime; --
  DECLARE cur_VendorID           int(11); --
  DECLARE cur_WarehouseID        int(11); --
  DECLARE cur_CustomerID         int(11); --
  DECLARE cur_OrderID            int(11); --
  DECLARE cur_OrderDetailsID     int(11); --
  DECLARE cur_LotNumber          varchar(50); --
  DECLARE cur_LastUpdateUserID   smallint(6); --
  DECLARE cur_LastUpdateDatetime timestamp; --

  -- variables for update
  DECLARE V_Status            varchar(20); --
  DECLARE V_VendorID          int(11); --
  DECLARE V_WarehouseID       int(11); --
  DECLARE V_LotNumber         varchar(50); --
  DECLARE V_SoldDate          date; --
  DECLARE V_CurrentCustomerID int(11); --
  DECLARE V_LastCustomerID    int(11); --
  DECLARE V_LastUpdateUserID  smallint(6); --
  DECLARE V_AcceptableTran    bool; --

  DECLARE cur CURSOR FOR
   (SELECT
     st.ID    as TranID
    ,1        as TranExists
    ,stt.ID   as TranTypeID
    ,stt.Name as TranType
    ,st.TransactionDatetime
    ,st.VendorID
    ,st.WarehouseID
    ,st.CustomerID
    ,st.OrderID
    ,st.OrderDetailsID
    ,st.LotNumber
    ,st.LastUpdateUserID
    ,st.LastUpdateDatetime
    FROM tbl_serial_transaction AS st
         INNER JOIN tbl_serial_transaction_type as stt ON st.TypeID = stt.ID
    WHERE st.SerialID = P_SerialID)
   UNION ALL
   (SELECT
     NULL                      as TranID
    ,0                         as TranExists
    ,ID                        as TranTypeID
    ,Name                      as TranType
    ,IFNULL(P_TranTime, Now()) as TransactionDatetime
    ,P_VendorID         as VendorID
    ,P_WarehouseID      as WarehouseID
    ,P_CustomerID       as CustomerID
    ,P_OrderID          as OrderID
    ,P_OrderDetailsID   as OrderDetailsID
    ,P_LotNumber        as LotNumber
    ,P_LastUpdateUserID as LastUpdateUserID
    ,Now()              as LastUpdateDatetime
    FROM tbl_serial_transaction_type
    WHERE Name = P_TranType)
   ORDER BY TranExists desc, TransactionDatetime asc, TranID asc; --

  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  IF (P_SerialID IS NOT NULL) THEN
    -- init / reinit
    SET V_Status            = 'Unknown'; --
    SET V_VendorID          = null; --
    SET V_WarehouseID       = null; --
    SET V_LotNumber         = null; --
    SET V_SoldDate          = null; --
    SET V_LastCustomerID    = null; --
    SET V_CurrentCustomerID = null; --
    SET V_LastUpdateUserID  = null; --

    OPEN cur; --

    REPEAT
      FETCH cur INTO
       cur_TranID
      ,cur_TranExists
      ,cur_TranTypeID
      ,cur_TranType
      ,cur_TranTime
      ,cur_VendorID
      ,cur_WarehouseID
      ,cur_CustomerID
      ,cur_OrderID
      ,cur_OrderDetailsID
      ,cur_LotNumber
      ,cur_LastUpdateUserID
      ,cur_LastUpdateDatetime; --

      IF (done = 0)
      AND (cur_TranTypeID IS NOT NULL)
      THEN
        SET V_AcceptableTran = 1; --

        IF (V_Status IN ('Unknown', 'On Hand')) AND (cur_TranType = 'Reserved') THEN
          -- ( 1, 'Reserved'                ), -- means that we added serial to not approved order
          SET cur_VendorID        = null; --
          SET cur_WarehouseID     = null; --
          -- SET cur_CustomerID      = null; -- we need to know for whom did we reserved that serial
          -- SET cur_OrderID         = null; --
          -- SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Reserved'; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'Reserved')) AND (cur_TranType = 'Reserve Cancelled') THEN
          -- ( 2, 'Reserve Cancelled'       ), -- means that we removed serial from not approved order
          SET cur_VendorID        = null; --
          SET cur_WarehouseID     = null; --
          SET cur_CustomerID      = null; --
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'On Hand'; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'On Hand', 'Reserved') AND cur_TranType IN ('Rented', 'Sold'))
            OR (V_Status IN ('Rented') AND cur_TranType IN ('Sold')) THEN
          -- ( 3, 'Rented'                  ), -- means that RENT order was approved
          -- ( 4, 'Sold'                    ), -- means that SALE order or RENT-TO-PURCHASE order was approved
          SET cur_VendorID        = null; --
          SET cur_WarehouseID     = null; --
          -- SET cur_CustomerID      = null; -- we need to know who rented or bought that serial
          -- SET cur_OrderID         = null; --
          -- SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = CASE WHEN cur_TranType = 'Sold' THEN cur_TranTime ELSE null END; --
          SET V_Status            = CASE cur_TranType WHEN 'Rented' THEN 'Rented' WHEN 'Sold' THEN 'Sold' ELSE null END; --
          SET V_WarehouseID       = null; --
          SET V_LastCustomerID    = V_CurrentCustomerID; --
          SET V_CurrentCustomerID = cur_CustomerID; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status != 'Maintenance') AND (cur_TranType IN ('Returned')) THEN
          -- ( 5, 'Returned'                ), -- means that user return RENTED serial
          --                                   -- but serial must be cleaned out prior to re-using
          SET cur_VendorID        = null; --
          -- SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          -- SET cur_CustomerID      = null; -- we need to know whom we returned that serial from
          -- SET cur_OrderID         = null; --
          -- SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Maintenance'; --
          SET V_WarehouseID       = cur_WarehouseID; --
          SET V_LastCustomerID    = V_CurrentCustomerID; --
          SET V_CurrentCustomerID = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (cur_TranType IN ('Lost', 'Junked')) THEN
          -- ( 6, 'Lost'                    ), -- can be added only manually to mark serial as 'Lost'
          -- ( 7, 'Junked'                  ), -- can be added only manually to mark serial as 'Junked'
          SET cur_VendorID        = null; --
          SET cur_WarehouseID     = null; --
          SET cur_CustomerID      = null; --
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = CASE cur_TranType WHEN 'Lost' THEN 'Lost' WHEN 'Junked' THEN 'Junked' ELSE null END; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'Empty')) AND (cur_TranType = 'O2 Tank out for filling') THEN
          -- ( 8, 'O2 Tank out for filling' ), -- Send    : "Empty"   -> "Sent"
          -- SET cur_VendorID        = null; -- we need to know whom we sent that serial
          SET cur_WarehouseID     = null; --
          SET cur_CustomerID      = null; --
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Sent'; --
          SET V_VendorID          = cur_VendorID; --
          SET V_WarehouseID       = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'Sent')) AND (cur_TranType = 'O2 Tank in from filling') THEN
          -- ( 9, 'O2 Tank in from filling' ), -- Receive : "Sent"    -> "On Hand"
          SET cur_VendorID        = null; --
          -- SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          SET cur_CustomerID      = null; --
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          -- SET cur_LotNumber       = null; --we need to know lot number assigned

          SET V_SoldDate          = null; --
          SET V_Status            = 'On Hand'; --
          SET V_WarehouseID       = cur_WarehouseID; --
          SET V_LotNumber         = cur_LotNumber; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'On Hand')) AND (cur_TranType = 'O2 Tank out to customer') THEN
          -- (10, 'O2 Tank out to customer' ), -- Rent    : "On Hand" -> "Rented"
          SET cur_VendorID        = null; --
          SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          -- SET cur_CustomerID      = null; -- we need to know whom we sent that serial
          -- SET cur_OrderID         = null; --
          -- SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Rented'; --
          SET V_WarehouseID       = null; --
          SET V_CurrentCustomerID = cur_CustomerID; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'Rented')) AND (cur_TranType = 'O2 Tank in from customer') THEN
          -- (11, 'O2 Tank in from customer'), -- Pickup  : "Rented"  -> "Empty"
          SET cur_VendorID        = null; --
          -- SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          SET cur_CustomerID      = null; --
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Empty'; --
          SET V_WarehouseID       = cur_WarehouseID; --
          SET V_LastCustomerID    = V_CurrentCustomerID; --
          SET V_CurrentCustomerID = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'On Hand')) AND (cur_TranType = 'Transferred Out') THEN
          -- (14, 'Transferred Out' ), -- Transferred Out  : "On Hand" -> "Transferred Out"
          SET cur_VendorID        = null; --
          SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          SET cur_CustomerID      = null; -- we need to know whom we sent that serial
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Transferred Out'; --
          SET V_WarehouseID       = null; --
          SET V_CurrentCustomerID = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'Transferred Out')) AND (cur_TranType = 'Transferred In') THEN
          -- (15, 'Transferred In' ) -- Transferred In  : "Transferred Out" -> "On Hand"
          --                                            :       <NULL>      -> "On Hand"
          -- only way to assign warehouse to serial
          SET cur_VendorID        = null; --
          -- SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          SET cur_CustomerID      = null; -- we need to know whom we sent that serial
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'On Hand'; --
          SET V_WarehouseID       = cur_WarehouseID; --
          SET V_CurrentCustomerID = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'On Hand')) AND (cur_TranType = 'Out for Maintenance') THEN
          -- (12, 'Out for Maintenance' ), -- Out for Maintenance  : "On Hand" -> "Maintenance"
          SET cur_VendorID        = null; --
          -- SET cur_WarehouseID     = null; -- we need to know where we sent that serial
          SET cur_CustomerID      = null; -- we do not need to know whom we sent that serial
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'Maintenance'; --
          SET V_WarehouseID       = cur_WarehouseID; --
          SET V_CurrentCustomerID = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSEIF (V_Status IN ('Unknown', 'Maintenance')) AND (cur_TranType = 'In from Maintenance') THEN
          -- (13, 'In from Maintenance' ) -- In from Maintenance  : "Maintenance" -> "On Hand"
          --                                                      :     <NULL>    -> "On Hand"
          -- another way to assign warehouse to serial
          SET cur_VendorID        = null; --
          -- SET cur_WarehouseID     = null; -- we need to know where we returned that serial
          SET cur_CustomerID      = null; -- we do not need to know whom we sent that serial
          SET cur_OrderID         = null; --
          SET cur_OrderDetailsID  = null; --
          SET cur_LotNumber       = null; --

          SET V_SoldDate          = null; --
          SET V_Status            = 'On Hand'; --
          SET V_WarehouseID       = cur_WarehouseID; --
          SET V_CurrentCustomerID = null; --
          SET V_LastUpdateUserID  = cur_LastUpdateUserID; --

        ELSE
          SET V_AcceptableTran = 0; --

        END IF; --

        IF (V_AcceptableTran = 1) AND (cur_TranExists = 0) THEN
          INSERT INTO tbl_serial_transaction SET
           TypeID              = cur_TranTypeID
          ,SerialID            = P_SerialID
          ,TransactionDatetime = cur_TranTime
          ,VendorID            = cur_VendorID
          ,WarehouseID         = cur_WarehouseID
          ,CustomerID          = cur_CustomerID
          ,OrderID             = cur_OrderID
          ,OrderDetailsID      = cur_OrderDetailsID
          ,LotNumber           = IFNULL(cur_LotNumber, '')
          ,LastUpdateDatetime  = IFNULL(cur_LastUpdateDatetime, Now())
          ,LastUpdateUserID    = IFNULL(cur_LastUpdateUserID, 1); -- root
        END IF; --

      END IF; --
    UNTIL done END REPEAT; --

    CLOSE cur; --

    -- save into db
    UPDATE tbl_serial SET
      Status            = CASE WHEN V_Status = 'Unknown' THEN 'On Hand' ELSE V_Status END
    , VendorID          = V_VendorID
    , WarehouseID       = V_WarehouseID
    , LotNumber         = IFNULL(V_LotNumber, '')
    , SoldDate          = V_SoldDate
    , CurrentCustomerID = V_CurrentCustomerID
    , LastCustomerID    = V_LastCustomerID
    , LastUpdateUserID  = IFNULL(V_LastUpdateUserID, 1) -- root
    WHERE (ID = P_SerialID); --
  END IF; --
END