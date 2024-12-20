CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_InternalReflag`(P_InvoiceID INT, P_Extra TEXT, P_LastUpdateUserID SMALLINT)
BEGIN
  DECLARE F_Insco_1 tinyint DEFAULT 01; --
  DECLARE F_Insco_2 tinyint DEFAULT 02; --
  DECLARE F_Insco_3 tinyint DEFAULT 04; --
  DECLARE F_Insco_4 tinyint DEFAULT 08; --
  DECLARE F_Patient tinyint DEFAULT 16; --

  DECLARE V_TransactionTypeID int DEFAULT 0; --
  DECLARE V_Username VARCHAR(50); --

  SET V_TransactionTypeID = NULL; --
  SELECT ID
  INTO V_TransactionTypeID
  FROM tbl_invoice_transactiontype
  WHERE (Name = 'Voided Submission'); --

  SET V_Username = ''; --
  SELECT Login
  INTO V_Username
  FROM tbl_user
  WHERE (ID = P_LastUpdateUserID); --

  IF P_Extra NOT LIKE '<values>%</values>'
  AND P_Extra NOT LIKE '<values%/>'
  THEN
    SET P_Extra = NULL; --
  END IF; --

  INSERT INTO tbl_invoice_transaction
  ( InvoiceDetailsID
  , InvoiceID
  , CustomerID
  , InsuranceCompanyID
  , CustomerInsuranceID
  , TransactionTypeID
  , Amount
  , Quantity
  , TransactionDate
  , BatchNumber
  , Comments
  , Extra
  , LastUpdateUserID)
  SELECT
    InvoiceDetailsID
  , InvoiceID
  , CustomerID
  , CASE CurrentPayer WHEN 'Patient' THEN null
                      WHEN 'Ins4'    THEN InsuranceCompany4_ID
                      WHEN 'Ins3'    THEN InsuranceCompany3_ID
                      WHEN 'Ins2'    THEN InsuranceCompany2_ID
                      WHEN 'Ins1'    THEN InsuranceCompany1_ID
                      ELSE null END as InsuranceCompanyID
  , CASE CurrentPayer WHEN 'Patient' THEN null
                      WHEN 'Ins4'    THEN Insurance4_ID
                      WHEN 'Ins3'    THEN Insurance3_ID
                      WHEN 'Ins2'    THEN Insurance2_ID
                      WHEN 'Ins1'    THEN Insurance1_ID
                      ELSE null END as CustomerInsuranceID
  , V_TransactionTypeID as TransactionTypeID
  , BillableAmount
  , Quantity
  , CURRENT_DATE()
  , null as BatchNumber
  , Concat('Reflagged by ', V_Username) as Comments
  , P_Extra
  , P_LastUpdateUserID as LastUpdateUserID
  FROM view_invoicetransaction_statistics
  WHERE (InvoiceID = P_InvoiceID)
    AND ((CurrentPayer = 'Patient' AND Submits & F_Patient != 0) OR
         (CurrentPayer = 'Ins4'    AND Submits & F_Insco_4 != 0) OR
         (CurrentPayer = 'Ins3'    AND Submits & F_Insco_3 != 0) OR
         (CurrentPayer = 'Ins2'    AND Submits & F_Insco_2 != 0) OR
         (CurrentPayer = 'Ins1'    AND Submits & F_Insco_1 != 0)); --
END