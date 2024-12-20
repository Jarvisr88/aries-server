CREATE DEFINER=`root`@`localhost` PROCEDURE `fix_serial_transactions`(P_SerialID INT)
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
  SELECT
    Priority
  , CustomerID
  , OrderID
  , OrderDetailsID
  , SerialID
  , WarehouseID
  , TranType
  , TranTime
  FROM `{E9A96545-F98D-4318-836E-A10EA2CD78B7}`
  ORDER BY DateReserved, OrderDetailsID, SerialId, Priority; --

  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  DROP TABLE IF EXISTS `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}`; --

  CREATE TEMPORARY TABLE `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` AS
  SELECT DISTINCT
    od.SerialID
  , od.CustomerID
  , od.OrderID
  , od.ID as OrderDetailsID
  , od.WarehouseID
  , o.DeliveryDate as DateReserved
  , trf.Time as DateTransferred
  , CASE WHEN (o.Approved = 1) AND (od.IsRented = 1)
         THEN o.DeliveryDate
         ELSE NULL END as DateRented
  , CASE WHEN (o.Approved = 1) AND (od.IsRented = 1) AND (od.IsActive = 0) AND (od.IsCanceled = 0) AND (od.IsPickedup = 0)
         THEN od.EndDate
         ELSE NULL END as DateRentSold
  , CASE WHEN (o.Approved = 1) AND (od.IsRented = 1) AND (od.IsActive = 0) AND (od.IsCanceled = 0) AND (od.IsPickedup = 1)
         THEN od.EndDate
         ELSE NULL END as DatePickedup
  , CASE WHEN (o.Approved = 1) AND (od.IsSold = 1)
         THEN o.DeliveryDate
         ELSE NULL END as DateSold
  FROM tbl_order AS o
       INNER JOIN view_orderdetails AS od ON od.CustomerID = o.CustomerID
                                         AND od.OrderID    = o.ID
       INNER JOIN tbl_serial AS s ON od.SerialID        = s.ID -- serial exists
                                 AND od.InventoryItemID = s.InventoryItemID
       LEFT JOIN (SELECT st.SerialID, st.WarehouseID, MIN(TransactionDatetime) as Time
                  FROM tbl_serial_transaction as st
                       INNER JOIN tbl_serial_transaction_type as stt ON stt.ID = st.TypeID
                  WHERE stt.Name = 'Transferred In'
                  GROUP BY st.SerialID, st.WarehouseID) as trf ON trf.SerialID    = od.SerialID
                                                              AND trf.WarehouseID = od.WarehouseID
  WHERE (o.DeliveryDate IS NOT NULL)
    AND (P_SerialID IS NULL OR s.ID = P_SerialID)
  ORDER BY od.SerialID, o.DeliveryDate, od.ID; --

  ALTER TABLE `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` ADD COLUMN Number INT NOT NULL AUTO_INCREMENT PRIMARY KEY; --
  ALTER TABLE `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` ADD COLUMN IsFirst BOOL NOT NULL DEFAULT 0; --

  DROP TABLE IF EXISTS `{F591E13A-9C30-445B-A812-BDE8F9A4566F}`; --

  CREATE TEMPORARY TABLE `{F591E13A-9C30-445B-A812-BDE8F9A4566F}` AS
  SELECT SerialID, Min(Number) as Number
  FROM `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}`
  GROUP BY SerialID; --

  UPDATE `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` AS a
         INNER JOIN `{F591E13A-9C30-445B-A812-BDE8F9A4566F}` AS b ON a.SerialID = b.SerialID
  SET a.IsFirst = CASE WHEN a.Number = b.Number THEN 1 ELSE 0 END; --

  DROP TABLE IF EXISTS `{F591E13A-9C30-445B-A812-BDE8F9A4566F}`; --

  -- delete bad entries

  DROP TABLE IF EXISTS `{B3F09F5E-8C0F-41BD-B652-25386EAAEAC4}`; --

  CREATE TEMPORARY TABLE `{B3F09F5E-8C0F-41BD-B652-25386EAAEAC4}` AS
  SELECT SerialID
  FROM `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}`
  GROUP BY SerialID
  HAVING 2 <= SUM(CASE WHEN DateRentSold IS NULL AND DatePickedup IS NULL THEN 1 ELSE 0 END); --

  -- OUTPUT bad entries for investigations

  SELECT SerialID
  FROM `{B3F09F5E-8C0F-41BD-B652-25386EAAEAC4}`; --

  DELETE FROM `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}`
  WHERE SerialID IN (SELECT SerialID FROM `{B3F09F5E-8C0F-41BD-B652-25386EAAEAC4}`); --

  DROP TABLE IF EXISTS `{B3F09F5E-8C0F-41BD-B652-25386EAAEAC4}`; --

  -- OUTPUT bad entries for investigations
  SELECT DISTINCT tmp.SerialID, stt.Name
  FROM `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` as tmp
       INNER JOIN tbl_serial_transaction as st ON st.SerialID = tmp.SerialID
       INNER JOIN tbl_serial_transaction_type as stt ON stt.ID = st.TypeID
  WHERE stt.Name NOT IN ('Reserved', 'Reserve Cancelled', 'Rented', 'Sold', 'Returned', 'In from Maintenance', 'Transferred In')
  ORDER BY tmp.SerialID, stt.Name; --

  DELETE tmp
  FROM `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` as tmp
       INNER JOIN tbl_serial_transaction as st ON st.SerialID = tmp.SerialID
       INNER JOIN tbl_serial_transaction_type as stt ON stt.ID = st.TypeID
  WHERE stt.Name NOT IN ('Reserved', 'Reserve Cancelled', 'Rented', 'Sold', 'Returned', 'In from Maintenance', 'Transferred In'); --

  DROP TABLE IF EXISTS `{E9A96545-F98D-4318-836E-A10EA2CD78B7}`; --

  CREATE TEMPORARY TABLE `{E9A96545-F98D-4318-836E-A10EA2CD78B7}` AS
  SELECT
    CASE WHEN s.IsFirst = 1              AND t.Name = 'Transferred In'      THEN 0
         WHEN s.IsFirst = 0              AND t.Name = 'In from Maintenance' THEN 0
         WHEN s.DateReserved IS NOT NULL AND t.Name = 'Reserved'            THEN 1
         WHEN s.DateSold     IS NOT NULL AND t.Name = 'Sold'                THEN 2
         WHEN s.DateRented   IS NOT NULL AND t.Name = 'Rented'              THEN 2
         WHEN s.DateRentSold IS NOT NULL AND t.Name = 'Sold'                THEN 3
         WHEN s.DatePickedup IS NOT NULL AND t.Name = 'Returned'            THEN 3
         END as Priority
  , s.DateReserved
  , s.CustomerID
  , s.OrderID
  , s.OrderDetailsID
  , s.SerialID
  , s.WarehouseID
  , t.Name as TranType
  , CASE WHEN s.IsFirst = 1              AND t.Name = 'Transferred In'      THEN IFNULL(s.DateTransferred, s.DateReserved)
         WHEN s.IsFirst = 0              AND t.Name = 'In from Maintenance' THEN s.DateReserved
         WHEN s.DateReserved IS NOT NULL AND t.Name = 'Reserved'            THEN s.DateReserved
         WHEN s.DateSold     IS NOT NULL AND t.Name = 'Sold'                THEN s.DateSold
         WHEN s.DateRented   IS NOT NULL AND t.Name = 'Rented'              THEN s.DateRented
         WHEN s.DateRentSold IS NOT NULL AND t.Name = 'Sold'                THEN s.DateRentSold
         WHEN s.DatePickedup IS NOT NULL AND t.Name = 'Returned'            THEN s.DatePickedup
         END as TranTime
  FROM ( SELECT Name
         FROM tbl_serial_transaction_type
         WHERE Name IN ('Reserved', 'Reserve Cancelled', 'Rented', 'Sold', 'Returned', 'In from Maintenance', 'Transferred In')
       ) as t
       INNER JOIN `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}` as s
               ON (s.IsFirst = 1              AND t.Name = 'Transferred In')
               OR (s.IsFirst = 0              AND t.Name = 'In from Maintenance')
               OR (s.DateReserved IS NOT NULL AND t.Name = 'Reserved')
               OR (s.DateSold     IS NOT NULL AND t.Name = 'Sold')
               OR (s.DateRented   IS NOT NULL AND t.Name = 'Rented')
               OR (s.DateRentSold IS NOT NULL AND t.Name = 'Sold')
               OR (s.DatePickedup IS NOT NULL AND t.Name = 'Returned')
  ORDER BY SerialId, DateReserved, OrderDetailsID, Priority; --

  DROP TABLE IF EXISTS `{B19B3C36-B432-4F3C-86F9-F4AF004EE8AF}`; --

  DELETE
  FROM tbl_serial_transaction
  WHERE SerialID IN (SELECT SerialID FROM `{E9A96545-F98D-4318-836E-A10EA2CD78B7}`); --

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

  DROP TABLE IF EXISTS `{E9A96545-F98D-4318-836E-A10EA2CD78B7}`; --
END