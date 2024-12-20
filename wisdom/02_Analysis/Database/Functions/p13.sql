CREATE DEFINER=`root`@`localhost` PROCEDURE `move_serial_on_hand`(P_SerialID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --

  -- cursor variables
  DECLARE cur_SerialID    INT(11); --
  DECLARE cur_WarehouseID INT(11); --
  DECLARE cur_TranType    VARCHAR(50); --

  DECLARE cur CURSOR FOR
  SELECT
    st2.SerialID
  , st2.WarehouseId
  , stt2.Name as TranType
  FROM (SELECT *
        FROM tbl_serial_transaction
        WHERE ID IN (SELECT Max(ID) FROM tbl_serial_transaction GROUP BY SerialID)) AS st
  INNER JOIN tbl_serial_transaction_type as stt ON stt.ID   = st.TypeID
                                               AND stt.Name = 'Returned'
  INNER JOIN (SELECT *
              FROM tbl_serial_transaction
              WHERE ID IN (SELECT Max(ID) FROM tbl_serial_transaction WHERE WarehouseId IS NOT NULL GROUP BY SerialID)) AS st2
          ON st2.SerialID = st.SerialID
  INNER JOIN tbl_serial_transaction_type AS stt2 ON stt2.Name = 'In from Maintenance'
  WHERE (P_SerialID IS NULL OR st2.SerialID = P_SerialID); --

  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO
      cur_SerialID
    , cur_WarehouseID
    , cur_TranType; --

    IF (done = 0) THEN
      CALL serial_add_transaction(
        cur_TranType       -- P_TranType         VARCHAR(50)
      , NOW()              -- P_TranTime         DATETIME
      , cur_SerialID       -- P_SerialID         INT,
      , cur_WarehouseID    -- P_WarehouseID      INT,
      , null               -- P_VendorID         INT,
      , null               -- P_CustomerID       INT,
      , null               -- P_OrderID          INT,
      , null               -- P_OrderDetailsID   INT,
      , null               -- P_LotNumber        VARCHAR(50),
      , 1                  -- P_LastUpdateUserID INT
      ); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END