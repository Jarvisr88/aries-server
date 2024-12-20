CREATE DEFINER=`root`@`localhost` PROCEDURE `serials_fix`()
BEGIN
  DECLARE V_Count, V_WarehouseID INT; --
  DECLARE cur_ID, cur_WarehouseID INT; --
  DECLARE done INT DEFAULT 0; --

  DECLARE cur CURSOR FOR
    SELECT
      tbl_serial.ID
    , tbl_warehouse.ID as WarehouseID
    FROM tbl_serial
         LEFT JOIN tbl_warehouse ON tbl_serial.WarehouseID = tbl_warehouse.ID
    WHERE tbl_serial.ID NOT IN (SELECT SerialID FROM tbl_serial_transaction); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  SELECT Count(*), Min(ID)
  INTO V_Count, V_WarehouseID
  FROM tbl_warehouse; --

  IF V_Count = 0 THEN
    INSERT INTO tbl_warehouse SET
      `Address1` = '',
      `Address2` = '',
      `City`     = '',
      `Contact`  = '',
      `Fax`      = '',
      `Name`     = 'Default warehouse',
      `Phone`    = '',
      `Phone2`   = '',
      `State`    = '',
      `Zip`      = '',
      `LastUpdateUserID` = 1; --

    SELECT LAST_INSERT_ID()
    INTO V_WarehouseID; --
  END IF; --

  OPEN cur; --

  REPEAT
    FETCH cur
    INTO cur_ID, cur_WarehouseID; --

    IF NOT done THEN
      SET cur_WarehouseID = IFNULL(cur_WarehouseID, V_WarehouseID); --

      CALL serial_add_transaction(
         'Transferred In' -- P_TranType         VARCHAR(50),
        ,Now()            -- P_TranTime         DATETIME,
        ,cur_ID           -- P_SerialID         INT,
        ,cur_WarehouseID  -- P_WarehouseID      INT,
        ,null             -- P_VendorID         INT,
        ,null             -- P_CustomerID       INT,
        ,null             -- P_OrderID          INT,
        ,null             -- P_OrderDetailsID   INT,
        ,null             -- P_LotNumber        VARCHAR(50),
        ,null             -- P_LastUpdateUserID INT
        ); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END