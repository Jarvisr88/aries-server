CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_AddSubmitted`(
  P_InvoiceID INT,
  P_SubmittedTo VARCHAR(50),
  P_SubmittedBy VARCHAR(50),
  P_SubmittedBatch VARCHAR(50),
  P_LastUpdateUserID smallint)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE V_InvoiceDetailsID INT; --
  DECLARE cur CURSOR FOR SELECT ID FROM tbl_invoicedetails WHERE (InvoiceID = P_InvoiceID) AND (CurrentPayer = P_SubmittedTo); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, null); --

  OPEN cur; --

  REPEAT
    FETCH cur INTO V_InvoiceDetailsID; --
    IF NOT done THEN
      CALL InvoiceDetails_AddSubmitted(V_InvoiceDetailsID, 0.00, P_SubmittedTo, P_SubmittedBy, P_SubmittedBatch, P_LastUpdateUserID); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --

  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, null); --
END