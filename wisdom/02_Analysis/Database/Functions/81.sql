CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_order`(P_OrderID varchar(10))
BEGIN
  DECLARE V_OrderID INT; --
  DECLARE V_ActiveOnly BIT; --

  -- P_OrderID
  -- 'ActiveOnly' - all orders that have details with State != 'Closed'
  -- number - just one
  -- all details regardless of state

  IF (P_OrderID = 'ActiveOnly') THEN
    SET V_OrderID = null; --
    SET V_ActiveOnly = 1; --
  ELSEIF (P_OrderID REGEXP '^(\\-|\\+){0,1}([0-9]+)$') THEN
    SET V_OrderID = CAST(P_OrderID as signed); --
    SET V_ActiveOnly = 0; --
  ELSE
    SET V_OrderID = null; --
    SET V_ActiveOnly = 0; --
  END IF; --

  IF (V_OrderID IS NOT NULL) THEN
    UPDATE tbl_order
    SET `MIR` =
      CONCAT_WS(','
      ,IF(CustomerID   IS NULL, 'CustomerID'  , null)
      ,IF(DeliveryDate IS NULL, 'DeliveryDate', null)
      ,IF(BillDate     IS NULL, 'BillDate'    , null)
      )
    WHERE (ID = V_OrderID); --
  ELSEIF (V_ActiveOnly != 1) THEN
    UPDATE tbl_order
    SET `MIR` =
      CONCAT_WS(','
      ,IF(CustomerID   IS NULL, 'CustomerID'  , null)
      ,IF(DeliveryDate IS NULL, 'DeliveryDate', null)
      ,IF(BillDate     IS NULL, 'BillDate'    , null)
      ); --
  ELSE
    UPDATE tbl_order as o
    INNER JOIN
           (SELECT DISTINCT CustomerID, OrderID
            FROM view_orderdetails
            WHERE (IsActive = 1)
           ) as d on d.CustomerID = o.CustomerID and d.OrderID = o.ID
    SET o.`MIR` =
      CONCAT_WS(','
      ,IF(o.CustomerID   IS NULL, 'CustomerID'  , null)
      ,IF(o.DeliveryDate IS NULL, 'DeliveryDate', null)
      ,IF(o.BillDate     IS NULL, 'BillDate'    , null)
      ); --
  END IF; --

  UPDATE tbl_order as o
  INNER JOIN
         (SELECT CustomerID, OrderID
          , SUM(0 < FIND_IN_SET('Customer.Inactive', `MIR.ORDER`)) AS `Customer.Inactive`
          , SUM(0 < FIND_IN_SET('Customer.MIR'     , `MIR.ORDER`)) AS `Customer.MIR`
          , SUM(0 < FIND_IN_SET('Policy1.Required' , `MIR.ORDER`)) AS `Policy1.Required`
          , SUM(0 < FIND_IN_SET('Policy1.MIR'      , `MIR.ORDER`)) AS `Policy1.MIR`
          , SUM(0 < FIND_IN_SET('Policy2.Required' , `MIR.ORDER`)) AS `Policy2.Required`
          , SUM(0 < FIND_IN_SET('Policy2.MIR'      , `MIR.ORDER`)) AS `Policy2.MIR`
          , SUM(0 < FIND_IN_SET('Facility.MIR'     , `MIR.ORDER`)) AS `Facility.MIR`
          , SUM(0 < FIND_IN_SET('PosType.Required' , `MIR.ORDER`)) AS `PosType.Required`
          , SUM(0 < FIND_IN_SET('ICD9.Required'    , `MIR.ORDER`)) AS `ICD9.Required`
          , SUM(0 < FIND_IN_SET('ICD9.1.Unknown'   , `MIR.ORDER`)) AS `ICD9.1.Unknown`
          , SUM(0 < FIND_IN_SET('ICD9.1.Inactive'  , `MIR.ORDER`)) AS `ICD9.1.Inactive`
          , SUM(0 < FIND_IN_SET('ICD9.2.Unknown'   , `MIR.ORDER`)) AS `ICD9.2.Unknown`
          , SUM(0 < FIND_IN_SET('ICD9.2.Inactive'  , `MIR.ORDER`)) AS `ICD9.2.Inactive`
          , SUM(0 < FIND_IN_SET('ICD9.3.Unknown'   , `MIR.ORDER`)) AS `ICD9.3.Unknown`
          , SUM(0 < FIND_IN_SET('ICD9.3.Inactive'  , `MIR.ORDER`)) AS `ICD9.3.Inactive`
          , SUM(0 < FIND_IN_SET('ICD9.4.Unknown'   , `MIR.ORDER`)) AS `ICD9.4.Unknown`
          , SUM(0 < FIND_IN_SET('ICD9.4.Inactive'  , `MIR.ORDER`)) AS `ICD9.4.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.Required'   , `MIR.ORDER`)) AS `ICD10.Required`
          , SUM(0 < FIND_IN_SET('ICD10.01.Unknown' , `MIR.ORDER`)) AS `ICD10.01.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.01.Inactive', `MIR.ORDER`)) AS `ICD10.01.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.02.Unknown' , `MIR.ORDER`)) AS `ICD10.02.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.02.Inactive', `MIR.ORDER`)) AS `ICD10.02.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.03.Unknown' , `MIR.ORDER`)) AS `ICD10.03.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.03.Inactive', `MIR.ORDER`)) AS `ICD10.03.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.04.Unknown' , `MIR.ORDER`)) AS `ICD10.04.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.04.Inactive', `MIR.ORDER`)) AS `ICD10.04.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.05.Unknown' , `MIR.ORDER`)) AS `ICD10.05.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.05.Inactive', `MIR.ORDER`)) AS `ICD10.05.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.06.Unknown' , `MIR.ORDER`)) AS `ICD10.06.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.06.Inactive', `MIR.ORDER`)) AS `ICD10.06.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.07.Unknown' , `MIR.ORDER`)) AS `ICD10.07.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.07.Inactive', `MIR.ORDER`)) AS `ICD10.07.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.08.Unknown' , `MIR.ORDER`)) AS `ICD10.08.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.08.Inactive', `MIR.ORDER`)) AS `ICD10.08.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.09.Unknown' , `MIR.ORDER`)) AS `ICD10.09.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.09.Inactive', `MIR.ORDER`)) AS `ICD10.09.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.10.Unknown' , `MIR.ORDER`)) AS `ICD10.10.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.10.Inactive', `MIR.ORDER`)) AS `ICD10.10.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.11.Unknown' , `MIR.ORDER`)) AS `ICD10.11.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.11.Inactive', `MIR.ORDER`)) AS `ICD10.11.Inactive`
          , SUM(0 < FIND_IN_SET('ICD10.12.Unknown' , `MIR.ORDER`)) AS `ICD10.12.Unknown`
          , SUM(0 < FIND_IN_SET('ICD10.12.Inactive', `MIR.ORDER`)) AS `ICD10.12.Inactive`
          FROM view_orderdetails
          WHERE IF(V_OrderID IS NOT NULL, OrderID = V_OrderID, V_ActiveOnly != 1 or IsActive = 1)
            AND (0 < FIND_IN_SET('Customer.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('Customer.MIR'     , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('Policy1.Required' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('Policy1.MIR'      , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('Policy2.Required' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('Policy2.MIR'      , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('Facility.MIR'     , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('PosType.Required' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.Required'    , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.1.Unknown'   , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.1.Inactive'  , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.2.Unknown'   , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.2.Inactive'  , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.3.Unknown'   , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.3.Inactive'  , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.4.Unknown'   , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD9.4.Inactive'  , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.Required'   , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.01.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.01.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.02.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.02.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.03.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.03.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.04.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.04.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.05.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.05.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.06.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.06.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.07.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.07.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.08.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.08.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.09.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.09.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.10.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.10.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.11.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.11.Inactive', `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.12.Unknown' , `MIR.ORDER`)
              OR 0 < FIND_IN_SET('ICD10.12.Inactive', `MIR.ORDER`))
          GROUP BY CustomerID, OrderID
         ) as d on d.CustomerID = o.CustomerID and d.OrderID = o.ID
  SET o.`MIR` = CONCAT_WS(','
    ,o.MIR
    ,IF(0 < d.`Customer.Inactive`, 'Customer.Inactive', NULL)
    ,IF(0 < d.`Customer.MIR`     , 'Customer.MIR'     , NULL)
    ,IF(0 < d.`Policy1.Required` , 'Policy1.Required' , NULL)
    ,IF(0 < d.`Policy1.MIR`      , 'Policy1.MIR'      , NULL)
    ,IF(0 < d.`Policy2.Required` , 'Policy2.Required' , NULL)
    ,IF(0 < d.`Policy2.MIR`      , 'Policy2.MIR'      , NULL)
    ,IF(0 < d.`Facility.MIR`     , 'Facility.MIR'     , NULL)
    ,IF(0 < d.`PosType.Required` , 'PosType.Required' , NULL)
    ,IF(0 < d.`ICD9.Required`    , 'ICD9.Required'    , NULL)
    ,IF(0 < d.`ICD9.1.Unknown`   , 'ICD9.1.Unknown'   , NULL)
    ,IF(0 < d.`ICD9.1.Inactive`  , 'ICD9.1.Inactive'  , NULL)
    ,IF(0 < d.`ICD9.2.Unknown`   , 'ICD9.2.Unknown'   , NULL)
    ,IF(0 < d.`ICD9.2.Inactive`  , 'ICD9.2.Inactive'  , NULL)
    ,IF(0 < d.`ICD9.3.Unknown`   , 'ICD9.3.Unknown'   , NULL)
    ,IF(0 < d.`ICD9.3.Inactive`  , 'ICD9.3.Inactive'  , NULL)
    ,IF(0 < d.`ICD9.4.Unknown`   , 'ICD9.4.Unknown'   , NULL)
    ,IF(0 < d.`ICD9.4.Inactive`  , 'ICD9.4.Inactive'  , NULL)
    ,IF(0 < d.`ICD10.Required`   , 'ICD10.Required'   , NULL)
    ,IF(0 < d.`ICD10.01.Unknown` , 'ICD10.01.Unknown' , NULL)
    ,IF(0 < d.`ICD10.01.Inactive`, 'ICD10.01.Inactive', NULL)
    ,IF(0 < d.`ICD10.02.Unknown` , 'ICD10.02.Unknown' , NULL)
    ,IF(0 < d.`ICD10.02.Inactive`, 'ICD10.02.Inactive', NULL)
    ,IF(0 < d.`ICD10.03.Unknown` , 'ICD10.03.Unknown' , NULL)
    ,IF(0 < d.`ICD10.03.Inactive`, 'ICD10.03.Inactive', NULL)
    ,IF(0 < d.`ICD10.04.Unknown` , 'ICD10.04.Unknown' , NULL)
    ,IF(0 < d.`ICD10.04.Inactive`, 'ICD10.04.Inactive', NULL)
    ,IF(0 < d.`ICD10.05.Unknown` , 'ICD10.05.Unknown' , NULL)
    ,IF(0 < d.`ICD10.05.Inactive`, 'ICD10.05.Inactive', NULL)
    ,IF(0 < d.`ICD10.06.Unknown` , 'ICD10.06.Unknown' , NULL)
    ,IF(0 < d.`ICD10.06.Inactive`, 'ICD10.06.Inactive', NULL)
    ,IF(0 < d.`ICD10.07.Unknown` , 'ICD10.07.Unknown' , NULL)
    ,IF(0 < d.`ICD10.07.Inactive`, 'ICD10.07.Inactive', NULL)
    ,IF(0 < d.`ICD10.08.Unknown` , 'ICD10.08.Unknown' , NULL)
    ,IF(0 < d.`ICD10.08.Inactive`, 'ICD10.08.Inactive', NULL)
    ,IF(0 < d.`ICD10.09.Unknown` , 'ICD10.09.Unknown' , NULL)
    ,IF(0 < d.`ICD10.09.Inactive`, 'ICD10.09.Inactive', NULL)
    ,IF(0 < d.`ICD10.10.Unknown` , 'ICD10.10.Unknown' , NULL)
    ,IF(0 < d.`ICD10.10.Inactive`, 'ICD10.10.Inactive', NULL)
    ,IF(0 < d.`ICD10.11.Unknown` , 'ICD10.11.Unknown' , NULL)
    ,IF(0 < d.`ICD10.11.Inactive`, 'ICD10.11.Inactive', NULL)
    ,IF(0 < d.`ICD10.12.Unknown` , 'ICD10.12.Unknown' , NULL)
    ,IF(0 < d.`ICD10.12.Inactive`, 'ICD10.12.Inactive', NULL)
    ); --
END