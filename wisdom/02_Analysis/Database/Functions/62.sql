CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_InternalWriteoffBalance`( P_InvoiceID TEXT
, P_InvoiceDetailsID TEXT
, P_LastUpdateUserID SMALLINT)
    MODIFIES SQL DATA
BEGIN
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
  , CONCAT('Wrote off by ', usr.Login) as Comments
  , 0.00 as Taxes
  , ''   as BatchNumber
  , null as Extra
  , 1    as Approved
  , P_LastUpdateUserID
  FROM tbl_invoicedetails as det
       INNER JOIN tbl_invoice_transactiontype as itt ON itt.Name = 'Writeoff'
       LEFT JOIN tbl_user as usr ON usr.ID = P_LastUpdateUserID
  WHERE ((0 < FIND_IN_SET(det.InvoiceID, P_InvoiceID)) OR (P_InvoiceID IS NULL) OR (P_InvoiceID = ''))
    AND ((0 < FIND_IN_SET(det.ID, P_InvoiceDetailsID)) OR (P_InvoiceDetailsID IS NULL) OR (P_InvoiceDetailsID = ''))
    AND (0.01 <= det.Balance); --
END