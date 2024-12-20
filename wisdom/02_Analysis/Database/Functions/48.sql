CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_InternalAddSubmitted`(
  P_InvoiceDetailsID INT,
  P_Amount DECIMAL(18,2),
  P_SubmittedTo VARCHAR(50),
  P_SubmittedBy VARCHAR(50),
  P_SubmittedBatch VARCHAR(50),
  P_LastUpdateUserID smallint)
BEGIN
  DECLARE V_TransactionTypeID INT DEFAULT (0); --

  SELECT ID
  INTO V_TransactionTypeID
  FROM tbl_invoice_transactiontype
  WHERE Name = 'Submit'; --

  IF P_SubmittedTo = 'Patient' THEN
    INSERT INTO `tbl_invoice_transaction` (
      `InvoiceDetailsID`,
      `InvoiceID`,
      `CustomerID`,
      `InsuranceCompanyID`,
      `CustomerInsuranceID`,
      `TransactionTypeID`,
      `Amount`,
      `Quantity`,
      `TransactionDate`,
      `BatchNumber`,
      `Comments`,
      `LastUpdateUserID`)
    SELECT tbl_invoicedetails.ID as `InvoiceDetailsID`,
           tbl_invoicedetails.InvoiceID,
           tbl_invoicedetails.CustomerID,
           NULL                  as `InsuranceCompanyID`,
           NULL                  as `CustomerInsuranceID`,
           V_TransactionTypeID,
           P_Amount,
           tbl_invoicedetails.Quantity,
           CURRENT_DATE() as `TransactionDate`,
           P_SubmittedBatch,
           Concat('Submitted by ', P_SubmittedBy) as `Comments`,
           P_LastUpdateUserID
    FROM tbl_invoicedetails
    WHERE (tbl_invoicedetails.ID = P_InvoiceDetailsID); --

  ELSEIF P_SubmittedTo = 'Ins4' THEN
    INSERT INTO `tbl_invoice_transaction` (
      `InvoiceDetailsID`,
      `InvoiceID`,
      `CustomerID`,
      `InsuranceCompanyID`,
      `CustomerInsuranceID`,
      `TransactionTypeID`,
      `Amount`,
      `Quantity`,
      `TransactionDate`,
      `BatchNumber`,
      `Comments`,
      `LastUpdateUserID`)
    SELECT tbl_invoicedetails.ID as `InvoiceDetailsID`,
           tbl_invoicedetails.InvoiceID,
           tbl_invoicedetails.CustomerID,
           tbl_customer_insurance.InsuranceCompanyID,
           tbl_customer_insurance.ID as `CustomerInsuranceID`,
           V_TransactionTypeID,
           P_Amount,
           tbl_invoicedetails.Quantity,
           CURRENT_DATE() as `TransactionDate`,
           P_SubmittedBatch,
           Concat('Submitted by ', P_SubmittedBy) as `Comments`,
           P_LastUpdateUserID
    FROM ((tbl_invoicedetails
           INNER JOIN tbl_invoice ON tbl_invoicedetails.CustomerID = tbl_invoice.CustomerID
                                 AND tbl_invoicedetails.InvoiceID = tbl_invoice.ID)
          INNER JOIN tbl_customer_insurance ON tbl_invoice.CustomerID = tbl_customer_insurance.CustomerID
                                           AND tbl_invoice.CustomerInsurance4_ID = tbl_customer_insurance.ID)
    WHERE (tbl_invoicedetails.ID = P_InvoiceDetailsID); --

  ELSEIF P_SubmittedTo = 'Ins3' THEN
    INSERT INTO `tbl_invoice_transaction` (
      `InvoiceDetailsID`,
      `InvoiceID`,
      `CustomerID`,
      `InsuranceCompanyID`,
      `CustomerInsuranceID`,
      `TransactionTypeID`,
      `Amount`,
      `Quantity`,
      `TransactionDate`,
      `BatchNumber`,
      `Comments`,
      `LastUpdateUserID`)
    SELECT tbl_invoicedetails.ID as `InvoiceDetailsID`,
           tbl_invoicedetails.InvoiceID,
           tbl_invoicedetails.CustomerID,
           tbl_customer_insurance.InsuranceCompanyID,
           tbl_customer_insurance.ID as `CustomerInsuranceID`,
           V_TransactionTypeID,
           P_Amount,
           tbl_invoicedetails.Quantity,
           CURRENT_DATE() as `TransactionDate`,
           P_SubmittedBatch,
           Concat('Submitted by ', P_SubmittedBy) as `Comments`,
           P_LastUpdateUserID
    FROM ((tbl_invoicedetails
           INNER JOIN tbl_invoice ON tbl_invoicedetails.CustomerID = tbl_invoice.CustomerID
                                 AND tbl_invoicedetails.InvoiceID = tbl_invoice.ID)
          INNER JOIN tbl_customer_insurance ON tbl_invoice.CustomerID = tbl_customer_insurance.CustomerID
                                           AND tbl_invoice.CustomerInsurance3_ID = tbl_customer_insurance.ID)
    WHERE (tbl_invoicedetails.ID = P_InvoiceDetailsID); --

  ELSEIF P_SubmittedTo = 'Ins2' THEN
    INSERT INTO `tbl_invoice_transaction` (
      `InvoiceDetailsID`,
      `InvoiceID`,
      `CustomerID`,
      `InsuranceCompanyID`,
      `CustomerInsuranceID`,
      `TransactionTypeID`,
      `Amount`,
      `Quantity`,
      `TransactionDate`,
      `BatchNumber`,
      `Comments`,
      `LastUpdateUserID`)
    SELECT tbl_invoicedetails.ID as `InvoiceDetailsID`,
           tbl_invoicedetails.InvoiceID,
           tbl_invoicedetails.CustomerID,
           tbl_customer_insurance.InsuranceCompanyID,
           tbl_customer_insurance.ID as `CustomerInsuranceID`,
           V_TransactionTypeID,
           P_Amount,
           tbl_invoicedetails.Quantity,
           CURRENT_DATE() as `TransactionDate`,
           P_SubmittedBatch,
           Concat('Submitted by ', P_SubmittedBy) as `Comments`,
           P_LastUpdateUserID
    FROM ((tbl_invoicedetails
           INNER JOIN tbl_invoice ON tbl_invoicedetails.CustomerID = tbl_invoice.CustomerID
                                 AND tbl_invoicedetails.InvoiceID = tbl_invoice.ID)
          INNER JOIN tbl_customer_insurance ON tbl_invoice.CustomerID = tbl_customer_insurance.CustomerID
                                           AND tbl_invoice.CustomerInsurance2_ID = tbl_customer_insurance.ID)
    WHERE (tbl_invoicedetails.ID = P_InvoiceDetailsID); --

  ELSEIF P_SubmittedTo = 'Ins1' THEN
    INSERT INTO `tbl_invoice_transaction` (
      `InvoiceDetailsID`,
      `InvoiceID`,
      `CustomerID`,
      `InsuranceCompanyID`,
      `CustomerInsuranceID`,
      `TransactionTypeID`,
      `Amount`,
      `Quantity`,
      `TransactionDate`,
      `BatchNumber`,
      `Comments`,
      `LastUpdateUserID`)
    SELECT tbl_invoicedetails.ID as `InvoiceDetailsID`,
           tbl_invoicedetails.InvoiceID,
           tbl_invoicedetails.CustomerID,
           tbl_customer_insurance.InsuranceCompanyID,
           tbl_customer_insurance.ID as `CustomerInsuranceID`,
           V_TransactionTypeID,
           P_Amount,
           tbl_invoicedetails.Quantity,
           CURRENT_DATE() as `TransactionDate`,
           P_SubmittedBatch,
           Concat('Submitted by ', P_SubmittedBy) as `Comments`,
           P_LastUpdateUserID
    FROM ((tbl_invoicedetails
           INNER JOIN tbl_invoice ON tbl_invoicedetails.CustomerID = tbl_invoice.CustomerID
                                 AND tbl_invoicedetails.InvoiceID = tbl_invoice.ID)
          INNER JOIN tbl_customer_insurance ON tbl_invoice.CustomerID = tbl_customer_insurance.CustomerID
                                           AND tbl_invoice.CustomerInsurance1_ID = tbl_customer_insurance.ID)
    WHERE (tbl_invoicedetails.ID = P_InvoiceDetailsID); --

  END IF; --
END