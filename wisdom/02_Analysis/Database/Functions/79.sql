CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_Reflag`(P_InvoiceID INT, P_Extra TEXT, P_LastUpdateUserID SMALLINT)
BEGIN
  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, NULL); --
  CALL Invoice_InternalReflag                    (P_InvoiceID, P_Extra, P_LastUpdateUserID); --
  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, NULL); --
END