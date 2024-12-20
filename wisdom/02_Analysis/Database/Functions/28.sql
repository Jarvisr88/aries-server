CREATE DEFINER=`root`@`localhost` PROCEDURE `Order_InternalProcess`(P_OrderID INT, P_BillingMonth INT, P_BillingFlags INT, P_InvoiceDate DATE, OUT P_InvoiceID INT)
BEGIN
  DECLARE V_DetailsCount, V_ICD10Count INT; --

  SET P_InvoiceID = NULL; --

  SELECT COUNT(*), SUM(CASE WHEN '2015-10-01' <= details.DosFrom THEN 1 ELSE 0 END)
  INTO V_DetailsCount, V_ICD10Count
  FROM tbl_order
       INNER JOIN view_orderdetails_core as details ON tbl_order.ID = details.OrderID
                                                   AND tbl_order.CustomerID = details.CustomerID
       INNER JOIN tbl_pricecode_item as pricecode ON details.PriceCodeID = pricecode.PriceCodeID
                                                 AND details.InventoryItemID = pricecode.InventoryItemID
  WHERE (details.OrderID = P_OrderID)
    AND (details.IsActive = 1)
    -- we should generate invoices before end date and should not generate invoices after end date
    AND ((details.EndDate IS NULL) OR (details.DosFrom <= details.EndDate))
    AND (IF(details.BillingMonth <= 0, 1, details.BillingMonth) = P_BillingMonth)
    AND ((IF((tbl_order.CustomerInsurance1_ID IS NOT NULL) AND (details.BillIns1 = 1), 1, 0) +
          IF((tbl_order.CustomerInsurance2_ID IS NOT NULL) AND (details.BillIns2 = 1), 2, 0) +
          IF((tbl_order.CustomerInsurance3_ID IS NOT NULL) AND (details.BillIns3 = 1), 4, 0) +
          IF((tbl_order.CustomerInsurance4_ID IS NOT NULL) AND (details.BillIns4 = 1), 8, 0) +
          IF((details.EndDate IS NOT NULL), 32, 0) +
          IF((details.AcceptAssignment = 1), 16, 0)) = P_BillingFlags)
    AND (IFNULL(details.MIR, '') = '')
    AND (OrderMustBeSkipped  (tbl_order.DeliveryDate, details.DosFrom, details.ActualSaleRentType, details.BillingMonth, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4) = 0)
    AND (InvoiceMustBeSkipped(tbl_order.DeliveryDate, details.DosFrom, details.ActualSaleRentType, details.BillingMonth, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4) = 0)
    -- check for zero amount was moved out of function InvoiceMustBeSkipped
    AND (details.IsZeroAmount = 0); --

  IF 0 < V_DetailsCount THEN
    -- create invoice
    INSERT INTO tbl_invoice
    ( CustomerID
    , OrderID
    , Approved
    , AcceptAssignment
    , ClaimNote
    , InvoiceDate
    , DoctorID
    , POSTypeID
    , FacilityID
    , ReferralID
    , SalesrepID
    , CustomerInsurance1_ID
    , CustomerInsurance2_ID
    , CustomerInsurance3_ID
    , CustomerInsurance4_ID
    , ICD9_1
    , ICD9_2
    , ICD9_3
    , ICD9_4
    , ICD10_01
    , ICD10_02
    , ICD10_03
    , ICD10_04
    , ICD10_05
    , ICD10_06
    , ICD10_07
    , ICD10_08
    , ICD10_09
    , ICD10_10
    , ICD10_11
    , ICD10_12
    , TaxRateID
    , TaxRatePercent
    , Discount
    , LastUpdateUserID)
    SELECT
      tbl_order.CustomerID
    , tbl_order.ID
    , tbl_order.Approved
    , IF(P_BillingFlags & 16 = 16, 1, 0) as AcceptAssignment
    , ClaimNote
    , P_InvoiceDate as InvoiceDate
    , tbl_order.DoctorID
    , tbl_order.POSTypeID
    , tbl_order.FacilityID
    , tbl_order.ReferralID
    , tbl_order.SalesrepID
    , tbl_order.CustomerInsurance1_ID
    , tbl_order.CustomerInsurance2_ID
    , tbl_order.CustomerInsurance3_ID
    , tbl_order.CustomerInsurance4_ID
    , IF(V_ICD10Count = V_DetailsCount, '', tbl_order.ICD9_1) as ICD9_1
    , IF(V_ICD10Count = V_DetailsCount, '', tbl_order.ICD9_2) as ICD9_2
    , IF(V_ICD10Count = V_DetailsCount, '', tbl_order.ICD9_3) as ICD9_3
    , IF(V_ICD10Count = V_DetailsCount, '', tbl_order.ICD9_4) as ICD9_4
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_01) as ICD10_01
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_02) as ICD10_02
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_03) as ICD10_03
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_04) as ICD10_04
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_05) as ICD10_05
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_06) as ICD10_06
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_07) as ICD10_07
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_08) as ICD10_08
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_09) as ICD10_09
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_10) as ICD10_10
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_11) as ICD10_11
    , IF(V_ICD10Count = 0, '', tbl_order.ICD10_12) as ICD10_12
    , view_taxrate.ID
    , view_taxrate.TotalTax
    , tbl_order.Discount
    , IFNULL(@UserId, 1) as LastUpdateUserID
    FROM tbl_order
         LEFT JOIN tbl_customer ON tbl_order.CustomerID = tbl_customer.ID
         LEFT JOIN tbl_company ON tbl_company.ID = 1
         LEFT JOIN view_taxrate ON IFNULL(tbl_customer.TaxRateID, tbl_company.TaxRateID) = view_taxrate.ID
    WHERE (tbl_order.ID = P_OrderID); --

    SELECT LAST_INSERT_ID() INTO P_InvoiceID; --

    -- add line items to invoice
    INSERT INTO tbl_invoicedetails
    ( CustomerID
    , InvoiceID
    , InventoryItemID
    , PriceCodeID
    , OrderID
    , OrderDetailsID
    , Balance
    , BillableAmount
    , AllowableAmount
    , Taxes
    , Quantity
    , Hardship
    , AcceptAssignment
    , InvoiceDate
    , DOSFrom
    , DOSTo
    , ShowSpanDates
    , BillingCode
    , Modifier1
    , Modifier2
    , Modifier3
    , Modifier4
    , DXPointer
    , DXPointer10
    , DrugNoteField
    , DrugControlNumber
    , BillingMonth
    , SendCMN_RX_w_invoice
    , SpecialCode
    , ReviewCode
    , MedicallyUnnecessary
    , BillIns1
    , BillIns2
    , BillIns3
    , BillIns4
    , NopayIns1
    , CMNFormID
    , AuthorizationTypeID
    , AuthorizationNumber
    , HaoDescription)
    SELECT
      details.CustomerID
    , P_InvoiceID
    , details.InventoryItemID
    , details.PriceCodeID
    , details.OrderID
    , details.ID
    , (1 - IFNULL(tbl_order.Discount, 0) / 100) *
      GetAmountMultiplier(details.DOSFrom, details.DOSTo, details.EndDate, details.ActualSaleRentType, details.ActualOrderedWhen, details.ActualBilledWhen) *
      IF((details.Taxable = 1) AND (view_taxrate.ID IS NOT NULL)
        ,GetAllowableAmount(details.ActualSaleRentType, details.BillingMonth, details.AllowablePrice, details.BilledQuantity, pricecode.Sale_AllowablePrice, details.FlatRate) * (1 + IFNULL(view_taxrate.TotalTax, 0) / 100)
        ,GetBillableAmount (details.ActualSaleRentType, details.BillingMonth, details.BillablePrice , details.BilledQuantity, pricecode.Sale_BillablePrice, details.FlatRate))
      as Balance
    , (1 - IFNULL(tbl_order.Discount, 0) / 100) *
      GetAmountMultiplier(details.DOSFrom, details.DOSTo, details.EndDate, details.ActualSaleRentType, details.ActualOrderedWhen, details.ActualBilledWhen) *
      IF((details.Taxable = 1) AND (view_taxrate.ID IS NOT NULL)
        ,GetAllowableAmount(details.ActualSaleRentType, details.BillingMonth, details.AllowablePrice, details.BilledQuantity, pricecode.Sale_AllowablePrice, details.FlatRate) * (1 + IFNULL(view_taxrate.TotalTax, 0) / 100)
        ,GetBillableAmount (details.ActualSaleRentType, details.BillingMonth, details.BillablePrice , details.BilledQuantity, pricecode.Sale_BillablePrice, details.FlatRate))
      as BillableAmount
    , (1 - IFNULL(tbl_order.Discount, 0) / 100) *
      GetAmountMultiplier(details.DOSFrom, details.DOSTo, details.EndDate, details.ActualSaleRentType, details.ActualOrderedWhen, details.ActualBilledWhen) *
      GetAllowableAmount(details.ActualSaleRentType, details.BillingMonth, details.AllowablePrice, details.BilledQuantity, pricecode.Sale_AllowablePrice, details.FlatRate)
      as AllowableAmount
    , (1 - IFNULL(tbl_order.Discount, 0) / 100) *
      GetAmountMultiplier(details.DOSFrom, details.DOSTo, details.EndDate, details.ActualSaleRentType, details.ActualOrderedWhen, details.ActualBilledWhen) *
      IF((details.Taxable = 1) AND (view_taxrate.ID IS NOT NULL)
        ,GetAllowableAmount(details.ActualSaleRentType, details.BillingMonth, details.AllowablePrice, details.BilledQuantity, pricecode.Sale_AllowablePrice, details.FlatRate) * (0 + IFNULL(view_taxrate.TotalTax, 0) / 100)
        ,0.00) as Taxes
    , details.BilledQuantity *
      GetQuantityMultiplier(details.DOSFrom, details.DOSTo, details.EndDate, details.ActualSaleRentType, details.ActualOrderedWhen, details.ActualBilledWhen)
      as Quantity
    , IFNULL(tbl_customer.Hardship, 0)
    , IFNULL(details.AcceptAssignment, 0) as AcceptAssignment
    , P_InvoiceDate
    , details.DOSFrom
    , details.ActualDosTo as DOSTo
    , details.ShowSpanDates
    , details.BillingCode
    , GetInvoiceModifier(tbl_order.DeliveryDate, details.ActualSaleRentType, details.BillingMonth, 1, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4)
    , GetInvoiceModifier(tbl_order.DeliveryDate, details.ActualSaleRentType, details.BillingMonth, 2, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4)
    , GetInvoiceModifier(tbl_order.DeliveryDate, details.ActualSaleRentType, details.BillingMonth, 3, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4)
    , GetInvoiceModifier(tbl_order.DeliveryDate, details.ActualSaleRentType, details.BillingMonth, 4, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4)
    , details.DXPointer
    , details.DXPointer10
    , details.DrugNoteField
    , details.DrugControlNumber
    , IF(details.BillingMonth <= 0, 1, details.BillingMonth)
    , IF(details.BillingMonth <= 1, details.SendCMN_RX_w_invoice, 0)
    , details.SpecialCode
    , details.ReviewCode
    , details.MedicallyUnnecessary
    , details.BillIns1
    , details.BillIns2
    , details.BillIns3
    , details.BillIns4
    , details.NopayIns1
    , details.CMNFormID
    , details.AuthorizationTypeID
    , details.AuthorizationNumber
    , details.HaoDescription
    FROM tbl_order
         INNER JOIN view_orderdetails_core as details ON tbl_order.ID = details.OrderID
                                                     AND tbl_order.CustomerID = details.CustomerID
         INNER JOIN tbl_pricecode_item as pricecode ON details.PriceCodeID = pricecode.PriceCodeID
                                                   AND details.InventoryItemID = pricecode.InventoryItemID
         LEFT JOIN tbl_customer ON tbl_order.CustomerID = tbl_customer.ID
         LEFT JOIN tbl_company ON tbl_company.ID = 1
         LEFT JOIN view_taxrate ON IFNULL(tbl_customer.TaxRateID, tbl_company.TaxRateID) = view_taxrate.ID
    WHERE (details.OrderID = P_OrderID)
      AND (details.IsActive = 1)
      -- we should generate invoices before end date and should not generate invoices after end date
      AND ((details.EndDate IS NULL) OR (details.DosFrom <= details.EndDate))
      AND (IF(details.BillingMonth <= 0, 1, details.BillingMonth) = P_BillingMonth)
      AND ((IF((tbl_order.CustomerInsurance1_ID IS NOT NULL) AND (details.BillIns1 = 1), 1, 0) +
            IF((tbl_order.CustomerInsurance2_ID IS NOT NULL) AND (details.BillIns2 = 1), 2, 0) +
            IF((tbl_order.CustomerInsurance3_ID IS NOT NULL) AND (details.BillIns3 = 1), 4, 0) +
            IF((tbl_order.CustomerInsurance4_ID IS NOT NULL) AND (details.BillIns4 = 1), 8, 0) +
            IF((details.EndDate IS NOT NULL), 32, 0) +
            IF((details.AcceptAssignment = 1), 16, 0)) = P_BillingFlags)
      AND (IFNULL(details.MIR, '') = '')
      AND (OrderMustBeSkipped  (tbl_order.DeliveryDate, details.DosFrom, details.ActualSaleRentType, details.BillingMonth, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4) = 0)
      AND (InvoiceMustBeSkipped(tbl_order.DeliveryDate, details.DosFrom, details.ActualSaleRentType, details.BillingMonth, details.Modifier1, details.Modifier2, details.Modifier3, details.Modifier4) = 0)
      -- check for zero amount was moved out of function InvoiceMustBeSkipped
      AND (details.IsZeroAmount = 0); --
  END IF; --

  -- update order line items
  UPDATE tbl_order AS o
         INNER JOIN view_orderdetails_core AS od ON o.ID = od.OrderID
                                                AND o.CustomerID = od.CustomerID
  SET
    o.BillDate = od.DOSFrom
  , od.DOSTo     = GetNextDosTo  (od.DOSFrom, od.DOSTo, od.ActualBilledWhen)
  , od.DOSFrom   = GetNextDosFrom(od.DOSFrom, od.DOSTo, od.ActualBilledWhen)
  , od.Modifier1 = GetInvoiceModifier(o.DeliveryDate, od.ActualSaleRentType, od.BillingMonth, 1, od.Modifier1, od.Modifier2, od.Modifier3, od.Modifier4)
  , od.Modifier2 = GetInvoiceModifier(o.DeliveryDate, od.ActualSaleRentType, od.BillingMonth, 2, od.Modifier1, od.Modifier2, od.Modifier3, od.Modifier4)
  , od.State     = CASE WHEN (od.EndDate IS NOT NULL) AND (od.EndDate < od.InvoiceDate)
                        THEN 'Closed'
                        WHEN OrderMustBeClosed(o.DeliveryDate, od.DOSFrom, od.ActualSaleRentType, od.BillingMonth, od.Modifier1, od.Modifier2, od.Modifier3, od.Modifier4) = 1
                        THEN 'Closed'
                        ELSE od.State END
  , od.EndDate   = CASE WHEN od.EndDate IS NOT NULL
                        THEN od.EndDate
                        WHEN OrderMustBeClosed(o.DeliveryDate, od.DOSFrom, od.ActualSaleRentType, od.BillingMonth, od.Modifier1, od.Modifier2, od.Modifier3, od.Modifier4) = 1
                        THEN P_InvoiceDate
                        ELSE od.EndDate END
  , od.BillingMonth = IF(od.BillingMonth <= 0, 1, od.BillingMonth) + 1
  WHERE (od.OrderID = P_OrderID)
    AND (od.IsActive = 1)
    AND (IF(od.BillingMonth <= 0, 1, od.BillingMonth) = P_BillingMonth)
    AND ((IF((o.CustomerInsurance1_ID IS NOT NULL) AND (od.BillIns1 = 1), 1, 0) +
          IF((o.CustomerInsurance2_ID IS NOT NULL) AND (od.BillIns2 = 1), 2, 0) +
          IF((o.CustomerInsurance3_ID IS NOT NULL) AND (od.BillIns3 = 1), 4, 0) +
          IF((o.CustomerInsurance4_ID IS NOT NULL) AND (od.BillIns4 = 1), 8, 0) +
          IF((od.EndDate IS NOT NULL), 32, 0) +
          IF((od.AcceptAssignment = 1), 16, 0)) = P_BillingFlags)
    AND (IFNULL(od.MIR, '') = '')
    AND (OrderMustBeSkipped(o.DeliveryDate, od.DosFrom, od.ActualSaleRentType, od.BillingMonth, od.Modifier1, od.Modifier2, od.Modifier3, od.Modifier4) = 0); --

  IF P_BillingMonth = 1 THEN
    CALL Order_ConvertDepositsIntoPayments(P_OrderID); --
  END IF; --
END