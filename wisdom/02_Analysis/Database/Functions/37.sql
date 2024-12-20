CREATE DEFINER=`root`@`localhost` PROCEDURE `retailinvoice_addpayments`( P_InvoiceID INT
, P_TransactionDate DATETIME
, P_Extra TEXT
, P_LastUpdateUserID SMALLINT)
BEGIN
  DECLARE V_InvoiceDetailsID INT; --
  DECLARE V_Amount DECIMAL(18, 2); --
  DECLARE V_Extra TEXT; --
  DECLARE V_NewXml VARCHAR(50); --
  DECLARE V_Result VARCHAR(50); --
  DECLARE done INT DEFAULT 0; --
  DECLARE cur CURSOR FOR
    SELECT ID, BillableAmount FROM tbl_invoicedetails WHERE (InvoiceID = P_InvoiceID); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  OPEN cur; --

  DETAILS_LOOP: LOOP
    FETCH cur INTO V_InvoiceDetailsID, V_Amount; --

    IF done THEN
      LEAVE DETAILS_LOOP; --
    END IF; --

    SET V_NewXml = CONCAT('<v n="Paid">', CAST(V_Amount as CHAR), '</v>'); --
    SET V_Extra = UpdateXML(P_Extra, 'values/v[@n="Paid"]' COLLATE latin1_general_ci, V_NewXml COLLATE latin1_general_ci); --

    CALL `InvoiceDetails_AddPayment`
    ( V_InvoiceDetailsID
    , NULL -- P_InsuranceCompanyID
    , P_TransactionDate
    , V_Extra
    , '' -- P_Comments
    , '' -- P_Options
    , P_LastUpdateUserID
    , V_Result); --
  END LOOP DETAILS_LOOP; --

  CLOSE cur; --
END