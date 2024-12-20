CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_orderdetails`(P_OrderID varchar(10))
BEGIN
  DECLARE V_OrderID INT; --
  DECLARE V_ActiveOnly BIT; --

  --  now we make field tbl_order.SaleType informative only
  --  now we make field view_orderdetails.IsRetail informative only -
  --  user should use BillIns1 .. BillIns4 for the same purpose

  -- P_OrderID
  -- 'ActiveOnly' - all details with State != 'Closed'
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

  UPDATE view_orderdetails_core as details
         INNER JOIN tbl_order as _order ON details.OrderID    = _order.ID
                                       AND details.CustomerID = _order.CustomerID
         LEFT JOIN tbl_pricecode_item as pricing ON pricing.InventoryItemID = details.InventoryItemID
                                                AND pricing.PriceCodeID     = details.PriceCodeID
         LEFT JOIN tbl_inventoryitem as item ON details.InventoryItemID = item.ID
  SET details.`MIR` = CONCAT_WS(','
    , IF(item.ID IS NULL, 'InventoryItemID', null)
    , IF(pricing.ID IS NULL, 'PriceCodeID', null)
    , CASE WHEN details.SaleRentType = 'Medicare Oxygen Rental' AND details.IsOxygen != 1
           THEN 'SaleRentType'
           WHEN details.ActualSaleRentType = '' THEN 'SaleRentType' ELSE null END
    , CASE WHEN details.ActualBillItemOn   = '' THEN 'BillItemOn'   ELSE null END
    , CASE WHEN details.ActualBilledWhen   = '' THEN 'BilledWhen'   ELSE null END
    , CASE WHEN details.ActualOrderedWhen  = '' THEN 'OrderedWhen'  ELSE null END
    , IF((details.IsActive = 1) AND (details.EndDate < _order.BillDate), 'EndDate.Invalid', null)
    , IF((details.State = 'Pickup') AND (details.EndDate IS NULL), 'EndDate.Unconfirmed', null)
    , IF((details.SaleRentType IN ('Capped Rental', 'Parental Capped Rental')) AND (IFNULL(details.Modifier1, '') = ''), 'Modifier1', null)
    , IF((details.SaleRentType IN ('Capped Rental', 'Parental Capped Rental')) AND (_order.DeliveryDate < '2006-01-01') AND (details.BillingMonth BETWEEN 12 AND 13) AND (details.Modifier3 NOT IN ('BP', 'BR', 'BU')), 'Modifier3', null)
    , IF((details.SaleRentType IN ('Capped Rental', 'Parental Capped Rental')) AND (_order.DeliveryDate < '2006-01-01') AND (details.BillingMonth BETWEEN 14 AND 15) AND (details.Modifier3 NOT IN ('BR', 'BU')), 'Modifier3', null)
    , null)
  , details.`MIR.ORDER` = ''
  WHERE IF(V_OrderID IS NOT NULL, _order.ID = V_OrderID, V_ActiveOnly != 1 or details.IsActive = 1); --

  -- common part, no ICD9 or ICD10
  UPDATE view_orderdetails_core as details
         INNER JOIN tbl_order as _order ON details.OrderID    = _order.ID
                                       AND details.CustomerID = _order.CustomerID
         INNER JOIN tbl_customer as customer ON customer.ID = _order.CustomerID
         INNER JOIN tbl_pricecode_item as pricing ON pricing.InventoryItemID = details.InventoryItemID
                                                 AND pricing.PriceCodeID     = details.PriceCodeID
         LEFT JOIN tbl_customer_insurance as policy1 ON _order.CustomerInsurance1_ID = policy1.ID
                                                    AND _order.CustomerID            = policy1.CustomerID
         LEFT JOIN tbl_customer_insurance as policy2 ON _order.CustomerInsurance2_ID = policy2.ID
                                                    AND _order.CustomerID            = policy2.CustomerID
         LEFT JOIN tbl_cmnform as cmnform ON cmnform.ID         = details.CMNFormID
                                         AND cmnform.CustomerID = details.CustomerID
         LEFT JOIN tbl_facility as facility ON _order.FacilityID = facility.ID
         LEFT JOIN tbl_postype as postype ON _order.POSTypeID = postype.ID
  SET details.`MIR` = CONCAT_WS(','
    , details.`MIR`
    , IF(IFNULL(details.OrderedQuantity  ,  0) =  0, 'OrderedQuantity'  , null)
    , IF(IFNULL(details.OrderedUnits     , '') = '', 'OrderedUnits'     , null)
    , IF(IFNULL(details.OrderedConverter ,  0) =  0, 'OrderedConverter' , null)
    , IF(IFNULL(details.BilledQuantity   ,  0) =  0, 'BilledQuantity'   , null)
    , IF(IFNULL(details.BilledUnits      , '') = '', 'BilledUnits'      , null)
    , IF(IFNULL(details.BilledConverter  ,  0) =  0, 'BilledConverter'  , null)
    , IF(IFNULL(details.DeliveryQuantity ,  0) =  0, 'DeliveryQuantity' , null)
    , IF(IFNULL(details.DeliveryUnits    , '') = '', 'DeliveryUnits'    , null)
    , IF(IFNULL(details.DeliveryConverter,  0) =  0, 'DeliveryConverter', null)
    , IF(IFNULL(details.BillingCode      , '') = '', 'BillingCode'      , null)
    , CASE WHEN '2015-10-01' <= details.DOSFrom THEN null
           WHEN IFNULL(details.DXPointer  , '') REGEXP '[1-4](,[1-4])*' THEN null
           ELSE 'DXPointer9' END
    , CASE WHEN details.DOSFrom < '2015-10-01' THEN null
           WHEN IFNULL(details.DXPointer10, '') REGEXP '([1-9]|1[0-2])(,([1-9]|1[0-2]))*' THEN null
           ELSE 'DXPointer10' END
    , IF((IFNULL(pricing.DefaultCMNType, '') != '') AND (cmnform.ID IS NULL), 'CMNForm.Required', null)
    , IF((IFNULL(pricing.DefaultCMNType, '') != '') AND (cmnform.MIR != '' ), 'CMNForm.MIR'     , null)
    , IF((cmnform.CmnType = 'DMERC DRORDER') AND (cmnform.MIR != ''), 'CMNForm.MIR', null)
    , CASE WHEN cmnform.InitialDate           is null THEN null
           WHEN cmnform.EstimatedLengthOfNeed is null THEN null
           WHEN cmnform.EstimatedLengthOfNeed < 0     THEN null
           WHEN 99 <= cmnform.EstimatedLengthOfNeed   THEN null -- 99 = LIFETIME
           WHEN (cmnform.CMNType     IN ('DMERC 484.2', 'DME 484.03'))
            AND (DATE_ADD(cmnform.InitialDate, INTERVAL 12 MONTH) <= details.DOSFrom)
            AND (cmnform.RecertificationDate is null)
           THEN 'CMNForm.RecertificationDate'
           WHEN (cmnform.CMNType     IN ('DMERC 484.2', 'DME 484.03'))
            AND (DATE_ADD(cmnform.InitialDate, INTERVAL 12 MONTH) <= details.DOSFrom)
            AND (DATE_ADD(cmnform.RecertificationDate, INTERVAL 12 MONTH) <= details.DOSFrom)
           THEN 'CMNForm.FormExpired'
           WHEN (cmnform.CMNType NOT IN ('DMERC 484.2', 'DME 484.03'))
            AND (DATE_ADD(cmnform.InitialDate, INTERVAL cmnform.EstimatedLengthOfNeed MONTH) <= details.DOSFrom)
           THEN 'CMNForm.FormExpired'
           ELSE null END
    , CASE WHEN details.AuthorizationNumber is null THEN null
           WHEN details.AuthorizationNumber = ''    THEN null
           WHEN details.AuthorizationExpirationDate < details.DOSFrom THEN 'AuthorizationNumber.Expired'
           WHEN details.AuthorizationExpirationDate <= details.DOSTo  THEN 'AuthorizationNumber.Expires'
           ELSE null END
    , null) -- MIR
  , details.`MIR.ORDER` = CONCAT_WS(','
    , IF((details.BillIns1 = 1) AND (policy1.ID IS NULL), 'Policy1.Required', null)
    , IF((details.BillIns1 = 1) AND (policy1.MIR != '' ), 'Policy1.MIR'     , null)
    , IF((details.BillIns1 = 2) AND (policy2.MIR != '' ), 'Policy2.MIR'     , null)
    , IF(customer.InactiveDate < Now(), 'Customer.Inactive', null)
    , IF(customer.MIR != '', 'Customer.MIR', null)
    , IF(facility.MIR != '', 'Facility.MIR', null)
    , IF(postype.ID IS NULL, 'PosType.Required', null)
    , null)
  WHERE IF(V_OrderID IS NOT NULL, _order.ID = V_OrderID, V_ActiveOnly != 1 or details.IsActive = 1)
    AND (customer.CommercialAccount = 0)
    AND (details.IsZeroAmount = 0)
    AND ((details.BillIns1 = 1) OR (details.BillIns2 = 1) OR (details.BillIns3 = 1) OR (details.BillIns4 = 1)); --

  -- ICD9 is only for orders before 2015-10-01
  UPDATE view_orderdetails_core as details
         INNER JOIN tbl_order as _order ON details.OrderID    = _order.ID
                                       AND details.CustomerID = _order.CustomerID
         INNER JOIN tbl_customer as customer ON customer.ID = _order.CustomerID
         LEFT JOIN tbl_icd9 as icd9_1 ON _order.ICD9_1 = icd9_1.Code
         LEFT JOIN tbl_icd9 as icd9_2 ON _order.ICD9_2 = icd9_2.Code
         LEFT JOIN tbl_icd9 as icd9_3 ON _order.ICD9_3 = icd9_3.Code
         LEFT JOIN tbl_icd9 as icd9_4 ON _order.ICD9_4 = icd9_4.Code
  SET details.`MIR.ORDER` = CONCAT_WS(','
    , details.`MIR.ORDER`
    , CASE WHEN _order.ICD9_1 != ''                THEN null
           WHEN _order.ICD9_2 != ''                THEN null
           WHEN _order.ICD9_3 != ''                THEN null
           WHEN _order.ICD9_4 != ''                THEN null
           ELSE 'ICD9.Required' END
    , CASE WHEN IFNULL(_order.ICD9_1, '') = ''          THEN null
           WHEN icd9_1.Code IS NULL                     THEN 'ICD9.1.Unknown'
           WHEN icd9_1.InactiveDate <= _order.OrderDate THEN 'ICD9.1.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD9_2, '') = ''          THEN null
           WHEN icd9_2.Code IS NULL                     THEN 'ICD9.2.Unknown'
           WHEN icd9_2.InactiveDate <= _order.OrderDate THEN 'ICD9.2.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD9_3, '') = ''          THEN null
           WHEN icd9_3.Code IS NULL                     THEN 'ICD9.3.Unknown'
           WHEN icd9_3.InactiveDate <= _order.OrderDate THEN 'ICD9.3.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD9_4, '') = ''          THEN null
           WHEN icd9_4.Code IS NULL                     THEN 'ICD9.4.Unknown'
           WHEN icd9_4.InactiveDate <= _order.OrderDate THEN 'ICD9.4.Inactive'
           ELSE null END
    , null)
  WHERE IF(V_OrderID IS NOT NULL, _order.ID = V_OrderID, V_ActiveOnly != 1 or details.IsActive = 1)
    AND (customer.CommercialAccount = 0)
    AND (details.IsZeroAmount = 0)
    AND (details.DOSFrom < '2015-10-01')
    AND (details.DXPointer != '')
    AND ((details.BillIns1 = 1) OR (details.BillIns2 = 1) OR (details.BillIns3 = 1) OR (details.BillIns4 = 1)); --

  -- ICD10 is only for orders after 2015-10-01
  UPDATE view_orderdetails_core as details
         INNER JOIN tbl_order as _order ON details.OrderID    = _order.ID
                                       AND details.CustomerID = _order.CustomerID
         INNER JOIN tbl_customer as customer ON customer.ID = _order.CustomerID
         LEFT JOIN tbl_icd10 as icd10_01 ON _order.ICD10_01 = icd10_01.Code
         LEFT JOIN tbl_icd10 as icd10_02 ON _order.ICD10_02 = icd10_02.Code
         LEFT JOIN tbl_icd10 as icd10_03 ON _order.ICD10_03 = icd10_03.Code
         LEFT JOIN tbl_icd10 as icd10_04 ON _order.ICD10_04 = icd10_04.Code
         LEFT JOIN tbl_icd10 as icd10_05 ON _order.ICD10_05 = icd10_05.Code
         LEFT JOIN tbl_icd10 as icd10_06 ON _order.ICD10_06 = icd10_06.Code
         LEFT JOIN tbl_icd10 as icd10_07 ON _order.ICD10_07 = icd10_07.Code
         LEFT JOIN tbl_icd10 as icd10_08 ON _order.ICD10_08 = icd10_08.Code
         LEFT JOIN tbl_icd10 as icd10_09 ON _order.ICD10_09 = icd10_09.Code
         LEFT JOIN tbl_icd10 as icd10_10 ON _order.ICD10_10 = icd10_10.Code
         LEFT JOIN tbl_icd10 as icd10_11 ON _order.ICD10_11 = icd10_11.Code
         LEFT JOIN tbl_icd10 as icd10_12 ON _order.ICD10_12 = icd10_12.Code
  SET details.`MIR.ORDER` = CONCAT_WS(','
    , details.`MIR.ORDER`
    , CASE WHEN _order.ICD10_01 != '' THEN null
           WHEN _order.ICD10_02 != '' THEN null
           WHEN _order.ICD10_03 != '' THEN null
           WHEN _order.ICD10_04 != '' THEN null
           WHEN _order.ICD10_05 != '' THEN null
           WHEN _order.ICD10_06 != '' THEN null
           WHEN _order.ICD10_07 != '' THEN null
           WHEN _order.ICD10_08 != '' THEN null
           WHEN _order.ICD10_09 != '' THEN null
           WHEN _order.ICD10_10 != '' THEN null
           WHEN _order.ICD10_11 != '' THEN null
           WHEN _order.ICD10_12 != '' THEN null
           ELSE 'ICD10.Required' END
    , CASE WHEN IFNULL(_order.ICD10_01, '') = ''          THEN null
           WHEN icd10_01.Code IS NULL                     THEN 'ICD10.01.Unknown'
           WHEN icd10_01.InactiveDate <= _order.OrderDate THEN 'ICD10.01.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_02, '') = ''          THEN null
           WHEN icd10_02.Code IS NULL                     THEN 'ICD10.02.Unknown'
           WHEN icd10_02.InactiveDate <= _order.OrderDate THEN 'ICD10.02.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_03, '') = ''          THEN null
           WHEN icd10_03.Code IS NULL                     THEN 'ICD10.03.Unknown'
           WHEN icd10_03.InactiveDate <= _order.OrderDate THEN 'ICD10.03.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_04, '') = ''          THEN null
           WHEN icd10_04.Code IS NULL                     THEN 'ICD10.04.Unknown'
           WHEN icd10_04.InactiveDate <= _order.OrderDate THEN 'ICD10.04.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_05, '') = ''          THEN null
           WHEN icd10_05.Code IS NULL                     THEN 'ICD10.05.Unknown'
           WHEN icd10_05.InactiveDate <= _order.OrderDate THEN 'ICD10.05.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_06, '') = ''          THEN null
           WHEN icd10_06.Code IS NULL                     THEN 'ICD10.06.Unknown'
           WHEN icd10_06.InactiveDate <= _order.OrderDate THEN 'ICD10.06.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_07, '') = ''          THEN null
           WHEN icd10_07.Code IS NULL                     THEN 'ICD10.07.Unknown'
           WHEN icd10_07.InactiveDate <= _order.OrderDate THEN 'ICD10.07.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_08, '') = ''          THEN null
           WHEN icd10_08.Code IS NULL                     THEN 'ICD10.08.Unknown'
           WHEN icd10_08.InactiveDate <= _order.OrderDate THEN 'ICD10.08.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_09, '') = ''          THEN null
           WHEN icd10_09.Code IS NULL                     THEN 'ICD10.09.Unknown'
           WHEN icd10_09.InactiveDate <= _order.OrderDate THEN 'ICD10.09.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_10, '') = ''          THEN null
           WHEN icd10_10.Code IS NULL                     THEN 'ICD10.10.Unknown'
           WHEN icd10_10.InactiveDate <= _order.OrderDate THEN 'ICD10.10.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_11, '') = ''          THEN null
           WHEN icd10_11.Code IS NULL                     THEN 'ICD10.11.Unknown'
           WHEN icd10_11.InactiveDate <= _order.OrderDate THEN 'ICD10.11.Inactive'
           ELSE null END
    , CASE WHEN IFNULL(_order.ICD10_12, '') = ''          THEN null
           WHEN icd10_12.Code IS NULL                     THEN 'ICD10.12.Unknown'
           WHEN icd10_12.InactiveDate <= _order.OrderDate THEN 'ICD10.12.Inactive'
           ELSE null END
    , null)
  WHERE IF(V_OrderID IS NOT NULL, _order.ID = V_OrderID, V_ActiveOnly != 1 or details.IsActive = 1)
    AND (customer.CommercialAccount = 0)
    AND (details.IsZeroAmount = 0)
    AND ('2015-10-01' <= details.DOSFrom)
    AND (details.DXPointer10 != '')
    AND ((details.BillIns1 = 1) OR (details.BillIns2 = 1) OR (details.BillIns3 = 1) OR (details.BillIns4 = 1)); --
END