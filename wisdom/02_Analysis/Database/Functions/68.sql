CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_InternalUpdatePendingSubmissions`(P_InvoiceID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE
    V_CustomerID,
    V_InvoiceID,
    V_InvoiceDetailsID,
    V_Insurance1_ID,
    V_Insurance2_ID,
    V_Insurance3_ID,
    V_Insurance4_ID,
    V_Company1_ID,
    V_Company2_ID,
    V_Company3_ID,
    V_Company4_ID,
    V_Insurances,
    V_PendingSubmissions,
    V_Payments INT; --
  DECLARE
    V_CurrentPayer VARCHAR(10); --
  DECLARE
    V_PendingSubmissionID,
    V_WriteoffID INT; --
  DECLARE
    V_PaymentAmount,
    V_WriteoffAmount,
    V_BillableAmount DECIMAL(18, 2); --
  DECLARE
    V_Quantity DOUBLE; --
  DECLARE
    V_Hardship TINYINT(1); --
  DECLARE cur CURSOR FOR
    SELECT
      CustomerID,
      InvoiceID,
      InvoiceDetailsID,
      PaymentAmount,
      WriteoffAmount,
      BillableAmount,
      IFNULL(Quantity, 0.0) as Quantity,
      Insurance1_ID,
      Insurance2_ID,
      Insurance3_ID,
      Insurance4_ID,
      InsuranceCompany1_ID,
      InsuranceCompany2_ID,
      InsuranceCompany3_ID,
      InsuranceCompany4_ID,
      Insurances,
      PendingSubmissions,
      Payments,
      CurrentPayer
  FROM view_invoicetransaction_statistics
  WHERE (InvoiceID = P_InvoiceID) OR (P_InvoiceID IS NULL); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  SET V_PendingSubmissionID = NULL; --

  SELECT ID
  INTO V_PendingSubmissionID
  FROM tbl_invoice_transactiontype
  WHERE (Name = 'Pending Submission'); --

  SET V_WriteoffID = NULL; --

  SELECT ID
  INTO V_WriteoffID
  FROM tbl_invoice_transactiontype
  WHERE (Name = 'Writeoff'); --

  OPEN cur; --

  REPEAT
    FETCH cur INTO
      V_CustomerID,
      V_InvoiceID,
      V_InvoiceDetailsID,
      V_PaymentAmount,
      V_WriteoffAmount,
      V_BillableAmount,
      V_Quantity,
      V_Insurance1_ID,
      V_Insurance2_ID,
      V_Insurance3_ID,
      V_Insurance4_ID,
      V_Company1_ID,
      V_Company2_ID,
      V_Company3_ID,
      V_Company4_ID,
      V_Insurances,
      V_PendingSubmissions,
      V_Payments,
      V_CurrentPayer; --

    IF NOT done THEN
      IF (V_CurrentPayer = 'Ins1') AND (V_Insurance1_ID IS NOT NULL) AND (V_PendingSubmissions & 01 = 00) THEN -- first insurance requires billing but do not have 'pending submission'
        INSERT INTO `tbl_invoice_transaction`
          (`InvoiceDetailsID`, `InvoiceID`, `CustomerID`, `InsuranceCompanyID`, `CustomerInsuranceID`, `TransactionTypeID`, `TransactionDate`, `Comments`, `Amount`, `Quantity`)
        VALUES
          (V_InvoiceDetailsID, V_InvoiceID, V_CustomerID,        V_Company1_ID,       V_Insurance1_ID, V_PendingSubmissionID,    CURRENT_DATE(), 'Ins1',
           V_BillableAmount, V_Quantity); --

      ELSEIF (V_CurrentPayer = 'Ins2') AND (V_Insurance2_ID IS NOT NULL) AND (V_PendingSubmissions & 02 = 00) THEN -- second insurance requires billing but do not have 'pending submission'
        INSERT INTO `tbl_invoice_transaction`
          (`InvoiceDetailsID`, `InvoiceID`, `CustomerID`, `InsuranceCompanyID`, `CustomerInsuranceID`, `TransactionTypeID`, `TransactionDate`, `Comments`, `Amount`, `Quantity`)
        VALUES
          (V_InvoiceDetailsID, V_InvoiceID, V_CustomerID,        V_Company2_ID,       V_Insurance2_ID, V_PendingSubmissionID,    CURRENT_DATE(), 'Ins2',
           V_BillableAmount - V_PaymentAmount - V_WriteoffAmount, V_Quantity); --

      ELSEIF (V_CurrentPayer = 'Ins3') AND (V_Insurance3_ID IS NOT NULL) AND (V_PendingSubmissions & 04 = 00) THEN -- third insurance requires billing but do not have 'pending submission'
        INSERT INTO `tbl_invoice_transaction`
          (`InvoiceDetailsID`, `InvoiceID`, `CustomerID`, `InsuranceCompanyID`, `CustomerInsuranceID`, `TransactionTypeID`, `TransactionDate`, `Comments`, `Amount`, `Quantity`)
        VALUES
          (V_InvoiceDetailsID, V_InvoiceID, V_CustomerID,        V_Company3_ID,       V_Insurance3_ID, V_PendingSubmissionID,    CURRENT_DATE(), 'Ins3',
           V_BillableAmount - V_PaymentAmount - V_WriteoffAmount, V_Quantity); --

      ELSEIF (V_CurrentPayer = 'Ins4') AND (V_Insurance4_ID IS NOT NULL) AND (V_PendingSubmissions & 08 = 00) THEN -- fourth insurance requires billing but do not have 'pending submission'
        INSERT INTO `tbl_invoice_transaction`
          (`InvoiceDetailsID`, `InvoiceID`, `CustomerID`, `InsuranceCompanyID`, `CustomerInsuranceID`, `TransactionTypeID`, `TransactionDate`, `Comments`, `Amount`, `Quantity`)
        VALUES
          (V_InvoiceDetailsID, V_InvoiceID, V_CustomerID,        V_Company4_ID,       V_Insurance4_ID, V_PendingSubmissionID,    CURRENT_DATE(), 'Ins4',
           V_BillableAmount - V_PaymentAmount - V_WriteoffAmount, V_Quantity); --

      ELSEIF (V_CurrentPayer = 'Patient') AND (V_PendingSubmissions & 16 = 00) THEN -- patient requires billing but do not have 'pending submission'
        INSERT INTO `tbl_invoice_transaction`
          (`InvoiceDetailsID`, `InvoiceID`, `CustomerID`, `InsuranceCompanyID`, `CustomerInsuranceID`, `TransactionTypeID`, `TransactionDate`, `Comments`, `Amount`, `Quantity`)
        VALUES
          (V_InvoiceDetailsID, V_InvoiceID, V_CustomerID,                 null,                  null, V_PendingSubmissionID,    CURRENT_DATE(), 'Patient',
           V_BillableAmount - V_PaymentAmount - V_WriteoffAmount, V_Quantity); --

      END IF; --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END