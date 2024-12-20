CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_AddAutoSubmit`(
  P_InvoiceID INT,
  P_AutoSubmittedTo VARCHAR(5),
  P_LastUpdateUserID smallint)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE V_InvoiceDetailsID INT; --
  DECLARE V_Result VARCHAR(50); --
  DECLARE cur CURSOR FOR SELECT ID FROM tbl_invoicedetails WHERE (InvoiceID = P_InvoiceID); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, null); --

  OPEN cur; --

  REPEAT
    FETCH cur INTO V_InvoiceDetailsID; --
    IF NOT done THEN
      CALL InvoiceDetails_InternalAddAutoSubmit(V_InvoiceDetailsID, P_AutoSubmittedTo, P_LastUpdateUserID, V_Result); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --

  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, null); --
END