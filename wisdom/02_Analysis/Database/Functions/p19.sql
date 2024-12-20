CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_AddAutoSubmit`(
  P_InvoiceDetailsID INT,
  P_InsuranceCompanyID INT,
  P_TransactionDate DATETIME,
  P_LastUpdateUserID smallint,
  OUT P_Result VARCHAR(50))
    MODIFIES SQL DATA
PROC: BEGIN
  DECLARE V_CustomerID, V_InvoiceID, V_InvoiceDetailsID INT; --
  DECLARE V_TransmittedCustomerInsuranceID, V_TransmittedInsuranceCompanyID INT; --
  DECLARE V_Billable DECIMAL(18, 2); --
  DECLARE V_Quantity, V_Count INT; --

  SELECT
   `detail`.CustomerID,
   `detail`.InvoiceID,
   `detail`.ID as InvoiceDetailsID,
   CASE WHEN ins1.InsuranceCompanyID = P_InsuranceCompanyID THEN ins1.ID
        WHEN ins2.InsuranceCompanyID = P_InsuranceCompanyID THEN ins2.ID
        WHEN ins3.InsuranceCompanyID = P_InsuranceCompanyID THEN ins3.ID
        WHEN ins4.InsuranceCompanyID = P_InsuranceCompanyID THEN ins4.ID
        ELSE NULL END AS TransmittedCustomerInsuranceID,
   CASE WHEN ins1.InsuranceCompanyID = P_InsuranceCompanyID THEN ins1.InsuranceCompanyID
        WHEN ins2.InsuranceCompanyID = P_InsuranceCompanyID THEN ins2.InsuranceCompanyID
        WHEN ins3.InsuranceCompanyID = P_InsuranceCompanyID THEN ins3.InsuranceCompanyID
        WHEN ins4.InsuranceCompanyID = P_InsuranceCompanyID THEN ins4.InsuranceCompanyID
        ELSE NULL END AS TransmittedInsuranceCompanyID,
   `detail`.BillableAmount,
   `detail`.Quantity
  INTO
    V_CustomerID,
    V_InvoiceID,
    V_InvoiceDetailsID,
    V_TransmittedCustomerInsuranceID,
    V_TransmittedInsuranceCompanyID,
    V_Billable,
    V_Quantity
  FROM tbl_invoicedetails as `detail`
       INNER JOIN tbl_invoice as `invoice` ON `detail`.InvoiceID  = `invoice`.ID
                                          AND `detail`.CustomerID = `invoice`.CustomerID
       LEFT JOIN `tbl_customer_insurance` as `ins1` ON `ins1`.ID         = `invoice`.CustomerInsurance1_ID
                                                   AND `ins1`.CustomerID = `invoice`.CustomerID
                                                   AND `detail`.BillIns1 = 1
       LEFT JOIN `tbl_customer_insurance` as `ins2` ON `ins2`.ID         = `invoice`.CustomerInsurance2_ID
                                                   AND `ins2`.CustomerID = `invoice`.CustomerID
                                                   AND `detail`.BillIns2 = 1
       LEFT JOIN `tbl_customer_insurance` as `ins3` ON `ins3`.ID         = `invoice`.CustomerInsurance3_ID
                                                   AND `ins3`.CustomerID = `invoice`.CustomerID
                                                   AND `detail`.BillIns3 = 1
       LEFT JOIN `tbl_customer_insurance` as `ins4` ON `ins4`.ID         = `invoice`.CustomerInsurance4_ID
                                                   AND `ins4`.CustomerID = `invoice`.CustomerID
                                                   AND `detail`.BillIns4 = 1
  WHERE (`detail`.ID = P_InvoiceDetailsID); --

  IF (V_CustomerID IS NULL) OR (V_InvoiceID IS NULL) OR (V_InvoiceDetailsID IS NULL) THEN
    SET P_Result = 'InvoiceDetailsID is wrong'; --
    LEAVE PROC; --
  END IF; --

  IF (V_TransmittedCustomerInsuranceID IS NULL) OR (V_TransmittedInsuranceCompanyID IS NULL) THEN
    SET P_Result = 'Autosubmitted Company ID is wrong'; --
    LEAVE PROC; --
  END IF; --

  SELECT COUNT(*)
  INTO V_Count
  FROM tbl_invoice_transaction as it
       INNER JOIN tbl_invoice_transactiontype as tt ON it.TransactionTypeID = tt.ID
  WHERE (tt.Name               = 'Auto Submit'                  )
    AND (it.CustomerID         = V_CustomerID                   )
    AND (it.InvoiceID          = V_InvoiceID                    )
    AND (it.InvoiceDetailsID   = V_InvoiceDetailsID             )
    AND (it.InsuranceCompanyID = V_TransmittedInsuranceCompanyID); --

  IF 0 < V_Count THEN
    SET P_Result = 'Transaction already exists'; --
    LEAVE PROC; --
  END IF; --

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
  , V_TransmittedInsuranceCompanyID
  , V_TransmittedCustomerInsuranceID
  , ID as TransactionTypeID
  , P_TransactionDate
  , V_Billable as Amount
  , V_Quantity as Quantity
  , 0.00       as Taxes
  , ''         as BatchNumber
  , 'EDI'      as Comments
  , null       as Extra
  , 1          as Approved
  , P_LastUpdateUserID
  FROM tbl_invoice_transactiontype
  WHERE (Name = 'Auto Submit'); --

  SET P_Result = 'Success'; --
END PROC