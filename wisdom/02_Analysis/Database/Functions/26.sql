CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_AddPayment`( P_InvoiceDetailsID INT
, P_InsuranceCompanyID INT
, P_TransactionDate DATETIME
, P_Extra TEXT
, P_Comments TEXT
, P_Options TEXT
, P_LastUpdateUserID smallint
, OUT P_Result VARCHAR(255))
    MODIFIES SQL DATA
PROC: BEGIN
  DECLARE V_CustomerID, V_InvoiceID, V_InvoiceDetailsID, V_CustomerInsuranceID, V_InsuranceCompanyID INT; --
  DECLARE V_BasisAllowable, V_FirstInsurance BOOL; --
  DECLARE V_AllowableAmount, V_BillableAmount DECIMAL(18, 2); --
  DECLARE V_Quantity, V_Count INT; --
  DECLARE V_ExtraPaid, V_ExtraAllowable, V_ExtraDeductible, V_ExtraCheckNumber, V_ExtraPostingGuid, V_ExtraSequestration, V_ExtraContractualWriteoff VARCHAR(18); --
  DECLARE V_NumericRegexp VARCHAR(50); --
  DECLARE V_PaymentPaidAmount, V_PaymentAllowableAmount, V_PaymentDeductibleAmount, V_PaymentSequestrationAmount, V_PaymentContractualWriteoffAmount DECIMAL(18, 2); --

  SET V_ExtraPaid                = ExtractValue(P_Extra, 'values/v[@n="Paid"]/text()'); --
  SET V_ExtraAllowable           = ExtractValue(P_Extra, 'values/v[@n="Allowable"]/text()'); --
  SET V_ExtraCheckNumber         = ExtractValue(P_Extra, 'values/v[@n="CheckNumber"]/text()'); --
  SET V_ExtraPostingGuid         = ExtractValue(P_Extra, 'values/v[@n="PostingGuid"]/text()'); --
  SET V_ExtraDeductible          = ExtractValue(P_Extra, 'values/v[@n="Deductible"]/text()'); --
  SET V_ExtraSequestration       = ExtractValue(P_Extra, 'values/v[@n="Sequestration"]/text()'); --
  SET V_ExtraContractualWriteoff = ExtractValue(P_Extra, 'values/v[@n="ContractualWriteoff"]/text()'); --

  SET V_NumericRegexp = '^(-|\\+)?([0-9]+\\.[0-9]*|[0-9]*\\.[0-9]+|[0-9]+)$'; --

  SET V_PaymentPaidAmount                = CASE WHEN V_ExtraPaid                REGEXP V_NumericRegexp THEN V_ExtraPaid                ELSE NULL END; --
  SET V_PaymentAllowableAmount           = CASE WHEN V_ExtraAllowable           REGEXP V_NumericRegexp THEN V_ExtraAllowable           ELSE NULL END; --
  SET V_PaymentDeductibleAmount          = CASE WHEN V_ExtraDeductible          REGEXP V_NumericRegexp THEN V_ExtraDeductible          ELSE NULL END; --
  SET V_PaymentSequestrationAmount       = CASE WHEN V_ExtraSequestration       REGEXP V_NumericRegexp THEN V_ExtraSequestration       ELSE NULL END; --
  SET V_PaymentContractualWriteoffAmount = CASE WHEN V_ExtraContractualWriteoff REGEXP V_NumericRegexp THEN V_ExtraContractualWriteoff ELSE NULL END; --

  IF (V_PaymentPaidAmount IS NULL) THEN
    SET P_Result = 'Paid amount is not specified'; --
    LEAVE PROC; --
  END IF; --

  SELECT
   `detail`.CustomerID,
   `detail`.InvoiceID,
   `detail`.ID as InvoiceDetailsID,
   CASE WHEN ins1.InsuranceCompanyID = P_InsuranceCompanyID THEN ins1.ID
        WHEN ins2.InsuranceCompanyID = P_InsuranceCompanyID THEN ins2.ID
        WHEN ins3.InsuranceCompanyID = P_InsuranceCompanyID THEN ins3.ID
        WHEN ins4.InsuranceCompanyID = P_InsuranceCompanyID THEN ins4.ID
        ELSE NULL END AS CustomerInsuranceID,
   CASE WHEN ins1.InsuranceCompanyID = P_InsuranceCompanyID THEN ins1.InsuranceCompanyID
        WHEN ins2.InsuranceCompanyID = P_InsuranceCompanyID THEN ins2.InsuranceCompanyID
        WHEN ins3.InsuranceCompanyID = P_InsuranceCompanyID THEN ins3.InsuranceCompanyID
        WHEN ins4.InsuranceCompanyID = P_InsuranceCompanyID THEN ins4.InsuranceCompanyID
        ELSE NULL END AS InsuranceCompanyID,
   CASE WHEN ins1.ID IS NOT NULL THEN ins1.InsuranceCompanyID = P_InsuranceCompanyID
        WHEN ins2.ID IS NOT NULL THEN ins2.InsuranceCompanyID = P_InsuranceCompanyID
        WHEN ins3.ID IS NOT NULL THEN ins3.InsuranceCompanyID = P_InsuranceCompanyID
        WHEN ins4.ID IS NOT NULL THEN ins4.InsuranceCompanyID = P_InsuranceCompanyID
        ELSE 0 END AS FirstInsurance,
   CASE WHEN ins1.ID IS NOT NULL THEN ins1.Basis = 'Allowed'
        WHEN ins2.ID IS NOT NULL THEN ins2.Basis = 'Allowed'
        WHEN ins3.ID IS NOT NULL THEN ins3.Basis = 'Allowed'
        WHEN ins4.ID IS NOT NULL THEN ins4.Basis = 'Allowed'
        ELSE 0 END AS BasisAllowable,
   `detail`.AllowableAmount,
   `detail`.BillableAmount,
   `detail`.Quantity
  INTO
    V_CustomerID,
    V_InvoiceID,
    V_InvoiceDetailsID,
    V_CustomerInsuranceID,
    V_InsuranceCompanyID,
    V_FirstInsurance,
    V_BasisAllowable,
    V_AllowableAmount,
    V_BillableAmount,
    V_Quantity
  FROM tbl_invoicedetails as `detail`
       INNER JOIN tbl_invoice as `invoice` ON `detail`.InvoiceID  = `invoice`.ID
                                          AND `detail`.CustomerID = `invoice`.CustomerID
       LEFT JOIN `tbl_customer_insurance` as ins1 ON ins1.ID         = `invoice`.CustomerInsurance1_ID
                                                 AND ins1.CustomerID = `invoice`.CustomerID
                                                 AND `detail`.BillIns1 = 1
       LEFT JOIN `tbl_customer_insurance` as ins2 ON ins2.ID         = `invoice`.CustomerInsurance2_ID
                                                 AND ins2.CustomerID = `invoice`.CustomerID
                                                 AND `detail`.BillIns2 = 1
       LEFT JOIN `tbl_customer_insurance` as ins3 ON ins3.ID         = `invoice`.CustomerInsurance3_ID
                                                 AND ins3.CustomerID = `invoice`.CustomerID
                                                 AND `detail`.BillIns3 = 1
       LEFT JOIN `tbl_customer_insurance` as ins4 ON ins4.ID         = `invoice`.CustomerInsurance4_ID
                                                 AND ins4.CustomerID = `invoice`.CustomerID
                                                 AND `detail`.BillIns4 = 1
  WHERE (`detail`.ID = P_InvoiceDetailsID); --

  IF (V_CustomerID IS NULL)
  OR (V_InvoiceID IS NULL)
  OR (V_InvoiceDetailsID IS NULL) THEN
    SET P_Result = 'InvoiceDetailsID is wrong'; --
    LEAVE PROC; --
  END IF; --

  IF ((V_InsuranceCompanyID IS NULL) != (P_InsuranceCompanyID IS NULL)) THEN
    SET P_Result = 'InsuranceCompanyID is wrong'; --
    LEAVE PROC; --
  END IF; --

  IF (V_ExtraCheckNumber != '')
  AND (V_ExtraPostingGuid != '') THEN
    -- if we got both check number and posting guid we have to check that
    -- there are no other payment / denied transactions with same check number but different PostingGuid
    -- that way we allow posting multiple transaction for same checknumber
    -- but prevent autoposting from posting same check (and 835) twice since PostingGuid is used only by auto posting
    SELECT SUM(CASE WHEN ExtractValue(it.Extra, 'values/v[@n="CheckNumber"]/text()') = V_ExtraCheckNumber
                     AND ExtractValue(it.Extra, 'values/v[@n="PostingGuid"]/text()') != V_ExtraPostingGuid
                    THEN 1 ELSE 0 END)
    INTO V_Count
    FROM tbl_invoice_transaction as it
         INNER JOIN tbl_invoice_transactiontype as tt ON it.TransactionTypeID = tt.ID
    WHERE (tt.Name IN ('Denied', 'Payment'))
      AND (it.CustomerID         = V_CustomerID        )
      AND (it.InvoiceID          = V_InvoiceID         )
      AND (it.InvoiceDetailsID   = V_InvoiceDetailsID  )
      AND (it.InsuranceCompanyID = V_InsuranceCompanyID OR (it.InsuranceCompanyID IS NULL AND V_InsuranceCompanyID IS NULL)); --

    IF V_Count != 0 THEN
      SET P_Result = CONCAT('Payment for check# ', V_ExtraCheckNumber, ' does already exist'); --
      LEAVE PROC; --
    END IF; --
  END IF; --

  -- 'Adjust Allowable' - optional
  -- 'Denied' IF Amount = 0 - optional
  -- 'Payment' OTHERWISE
  -- 'Contractual Writeoff'
  -- 'Deductible'
  -- 'Auto Submit'
  -- 'Sequestration Writeoff'
  -- 'Hardship Writeoff'
  -- 'Balance Writeoff' - optional

  IF (0 < FIND_IN_SET('Adjust Allowable', P_Options))
  AND (V_CustomerInsuranceID IS NOT NULL)
  AND (V_InsuranceCompanyID IS NOT NULL)
  AND (V_FirstInsurance = 1)
  AND (0.01 <= ABS(V_PaymentAllowableAmount - V_AllowableAmount)) THEN
    -- we should add transaction only once
    SELECT COUNT(*)
    INTO V_Count
    FROM tbl_invoice_transaction as it
         INNER JOIN tbl_invoice_transactiontype as tt ON it.TransactionTypeID = tt.ID
    WHERE (tt.Name = 'Adjust Allowable')
      AND (it.CustomerID         = V_CustomerID        )
      AND (it.InvoiceID          = V_InvoiceID         )
      AND (it.InvoiceDetailsID   = V_InvoiceDetailsID  )
      AND (it.InsuranceCompanyID = V_InsuranceCompanyID); --

    IF V_Count = 0 THEN
      INSERT INTO tbl_invoice_transaction (
        InvoiceDetailsID
      , InvoiceID
      , CustomerID
      , InsuranceCompanyID
      , CustomerInsuranceID
      , TransactionTypeID
      , TransactionDate
      , Amount
      , Quantity
      , Taxes
      , BatchNumber
      , Comments
      , Extra
      , Approved
      , LastUpdateUserID)
      SELECT
        V_InvoiceDetailsID
      , V_InvoiceID
      , V_CustomerID
      , V_InsuranceCompanyID
      , V_CustomerInsuranceID
      , ID   as TransactionTypeID
      , P_TransactionDate
      , V_PaymentAllowableAmount
      , V_Quantity
      , 0.00       as Taxes
      , ''         as BatchNumber
      , P_Comments as Comments
      , null       as Extra
      , 1          as Approved
      , P_LastUpdateUserID
      FROM tbl_invoice_transactiontype
      WHERE (Name = 'Adjust Allowable'); --

      SET V_AllowableAmount = V_PaymentAllowableAmount; --
    END IF; --
  END IF; --

  IF (0 < FIND_IN_SET('Post Denied', P_Options))
  AND (ABS(V_PaymentPaidAmount) < 0.01) THEN
    -- we allow adding 'denied' transaction many times since they will not affect anything
    INSERT INTO tbl_invoice_transaction (
      InvoiceDetailsID
    , InvoiceID
    , CustomerID
    , InsuranceCompanyID
    , CustomerInsuranceID
    , TransactionTypeID
    , TransactionDate
    , Amount
    , Quantity
    , Taxes
    , BatchNumber
    , Comments
    , Extra
    , Approved
    , LastUpdateUserID)
    SELECT
      V_InvoiceDetailsID
    , V_InvoiceID
    , V_CustomerID
    , V_InsuranceCompanyID
    , V_CustomerInsuranceID
    , ID as TransactionTypeID
    , P_TransactionDate
    , 0.00       as Amount
    , V_Quantity
    , 0.00       as Taxes
    , ''         as BatchNumber
    , P_Comments as Comments
    , P_Extra    as Extra
    , 1          as Approved
    , P_LastUpdateUserID
    FROM tbl_invoice_transactiontype
    WHERE (Name = 'Denied'); --
  ELSE
    INSERT INTO tbl_invoice_transaction (
      InvoiceDetailsID
    , InvoiceID
    , CustomerID
    , InsuranceCompanyID
    , CustomerInsuranceID
    , TransactionTypeID
    , TransactionDate
    , Amount
    , Quantity
    , Taxes
    , BatchNumber
    , Comments
    , Extra
    , Approved
    , LastUpdateUserID)
    SELECT
      V_InvoiceDetailsID
    , V_InvoiceID
    , V_CustomerID
    , V_InsuranceCompanyID
    , V_CustomerInsuranceID
    , ID as TransactionTypeID
    , P_TransactionDate
    , V_PaymentPaidAmount
    , V_Quantity
    , 0.00       as Taxes
    , ''         as BatchNumber
    , P_Comments as Comments
    , P_Extra    as Extra
    , 1          as Approved
    , P_LastUpdateUserID
    FROM tbl_invoice_transactiontype
    WHERE (Name = 'Payment'); --
  END IF; --

  IF (V_CustomerInsuranceID IS NOT NULL)
  AND (V_InsuranceCompanyID IS NOT NULL) THEN
    IF (0.01 <= ABS(V_PaymentSequestrationAmount)) THEN
      INSERT INTO tbl_invoice_transaction (
        InvoiceDetailsID
      , InvoiceID
      , CustomerID
      , InsuranceCompanyID
      , CustomerInsuranceID
      , TransactionTypeID
      , TransactionDate
      , Amount
      , Quantity
      , Taxes
      , BatchNumber
      , Comments
      , Extra
      , Approved
      , LastUpdateUserID)
      SELECT
        V_InvoiceDetailsID
      , V_InvoiceID
      , V_CustomerID
      , V_InsuranceCompanyID
      , V_CustomerInsuranceID
      , ID as TransactionTypeID
      , P_TransactionDate
      , V_PaymentSequestrationAmount
      , V_Quantity
      , 0.00       as Taxes
      , ''         as BatchNumber
      , 'Sequestration Writeoff' as Comments
      , null       as Extra
      , 1          as Approved
      , P_LastUpdateUserID
      FROM tbl_invoice_transactiontype
      WHERE (Name = 'Writeoff'); --
    END IF; --

    IF (V_FirstInsurance = 1)
    AND (0.01 <= ABS(V_PaymentContractualWriteoffAmount)) THEN
      INSERT INTO tbl_invoice_transaction (
        InvoiceDetailsID
      , InvoiceID
      , CustomerID
      , InsuranceCompanyID
      , CustomerInsuranceID
      , TransactionTypeID
      , TransactionDate
      , Amount
      , Quantity
      , Taxes
      , BatchNumber
      , Comments
      , Extra
      , Approved
      , LastUpdateUserID)
      SELECT
        V_InvoiceDetailsID
      , V_InvoiceID
      , V_CustomerID
      , V_InsuranceCompanyID
      , V_CustomerInsuranceID
      , ID as TransactionTypeID
      , P_TransactionDate
      , V_PaymentContractualWriteoffAmount
      , V_Quantity
      , 0.00       as Taxes
      , ''         as BatchNumber
      , P_Comments as Comments
      , null       as Extra
      , 1          as Approved
      , P_LastUpdateUserID
      FROM tbl_invoice_transactiontype
      WHERE (Name = 'Contractual Writeoff'); --
    ELSEIF (V_FirstInsurance = 1)
    AND (V_BasisAllowable = 1)
    AND (0.01 <= V_BillableAmount - V_AllowableAmount) THEN
      SELECT COUNT(*)
      INTO V_Count
      FROM tbl_invoice_transaction as it
           INNER JOIN tbl_invoice_transactiontype as tt ON it.TransactionTypeID = tt.ID
      WHERE (tt.Name               = 'Contractual Writeoff')
        AND (it.CustomerID         = V_CustomerID          )
        AND (it.InvoiceID          = V_InvoiceID           )
        AND (it.InvoiceDetailsID   = V_InvoiceDetailsID    )
        AND (it.InsuranceCompanyID = V_InsuranceCompanyID  ); --

      IF V_Count = 0 THEN
        INSERT INTO tbl_invoice_transaction (
          InvoiceDetailsID
        , InvoiceID
        , CustomerID
        , InsuranceCompanyID
        , CustomerInsuranceID
        , TransactionTypeID
        , TransactionDate
        , Amount
        , Quantity
        , Taxes
        , BatchNumber
        , Comments
        , Extra
        , Approved
        , LastUpdateUserID)
        SELECT
          V_InvoiceDetailsID
        , V_InvoiceID
        , V_CustomerID
        , V_InsuranceCompanyID
        , V_CustomerInsuranceID
        , ID as TransactionTypeID
        , P_TransactionDate
        , V_BillableAmount - V_AllowableAmount
        , V_Quantity
        , 0.00       as Taxes
        , ''         as BatchNumber
        , P_Comments as Comments
        , null       as Extra
        , 1          as Approved
        , P_LastUpdateUserID
        FROM tbl_invoice_transactiontype
        WHERE (Name = 'Contractual Writeoff'); --
      END IF; --
    END IF; --

    IF (V_FirstInsurance = 1)
    AND (0.01 <= V_PaymentDeductibleAmount) THEN
      SELECT COUNT(*)
      INTO V_Count
      FROM tbl_invoice_transaction as it
           INNER JOIN tbl_invoice_transactiontype as tt ON it.TransactionTypeID = tt.ID
      WHERE (tt.Name               = 'Deductible'        )
        AND (it.CustomerID         = V_CustomerID        )
        AND (it.InvoiceID          = V_InvoiceID         )
        AND (it.InvoiceDetailsID   = V_InvoiceDetailsID  )
        AND (it.InsuranceCompanyID = V_InsuranceCompanyID); --

      IF V_Count = 0 THEN
        INSERT INTO tbl_invoice_transaction (
          InvoiceDetailsID
        , InvoiceID
        , CustomerID
        , InsuranceCompanyID
        , CustomerInsuranceID
        , TransactionTypeID
        , TransactionDate
        , Amount
        , Quantity
        , Taxes
        , BatchNumber
        , Comments
        , Extra
        , Approved
        , LastUpdateUserID)
        SELECT
          V_InvoiceDetailsID
        , V_InvoiceID
        , V_CustomerID
        , V_InsuranceCompanyID
        , V_CustomerInsuranceID
        , ID as TransactionTypeID
        , P_TransactionDate
        , V_PaymentDeductibleAmount
        , V_Quantity
        , 0.00       as Taxes
        , ''         as BatchNumber
        , P_Comments as Comments
        , null       as Extra
        , 1          as Approved
        , P_LastUpdateUserID
        FROM tbl_invoice_transactiontype
        WHERE (Name = 'Deductible'); --
      END IF; --
    END IF; --
  END IF; --

  CALL InvoiceDetails_RecalculateInternals_Single(null, P_InvoiceDetailsID); --
  -- for the following operations we need updated balance so we need to recalculate it

  INSERT INTO tbl_invoice_transaction (
    InvoiceDetailsID
  , InvoiceID
  , CustomerID
  , InsuranceCompanyID
  , CustomerInsuranceID
  , TransactionTypeID
  , TransactionDate
  , Amount
  , Quantity
  , Comments
  , Taxes
  , BatchNumber
  , Extra
  , Approved
  , LastUpdateUserID)
  SELECT
    det.ID as InvoiceDetailsID
  , det.InvoiceID
  , det.CustomerID
  , det.CurrentInsuranceCompanyID
  , det.CurrentCustomerInsuranceID
  , itt.ID as TransactionTypeID
  , NOW() as TransactionDate
  , det.Balance
  , det.Quantity
  , CASE WHEN det.Hardship = 1 THEN 'Hardship Writeoff' ELSE CONCAT('Wrote off by ', IFNULL(usr.Login, '?')) END AS Comments
  , 0.00 as Taxes
  , ''   as BatchNumber
  , null as Extra
  , 1    as Approved
  , P_LastUpdateUserID
  FROM tbl_invoicedetails as det
       INNER JOIN tbl_invoice_transactiontype as itt ON itt.Name = 'Writeoff'
       LEFT JOIN tbl_user as usr ON usr.ID = P_LastUpdateUserID
  WHERE (det.ID = P_InvoiceDetailsID)
    AND ((det.Hardship = 1 AND det.CurrentPayer = 'Patient') OR (0 < FIND_IN_SET('Writeoff Balance', P_Options)))
    AND (0.01 <= det.Balance); --

  IF (ROW_COUNT() != 0) THEN
    CALL InvoiceDetails_RecalculateInternals_Single(null, P_InvoiceDetailsID); --
  END IF; --

  SET P_Result = 'Success'; --
END PROC