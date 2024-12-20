CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_UpdatePendingSubmissions`(P_InvoiceID INT)
BEGIN
  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, null); --
  CALL Invoice_InternalUpdatePendingSubmissions  (P_InvoiceID); --
  CALL InvoiceDetails_RecalculateInternals_Single(P_InvoiceID, null); --
END