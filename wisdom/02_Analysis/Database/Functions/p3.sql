CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_UpdateBalance`(P_InvoiceID INT, P_Recursive BOOL)
BEGIN
  IF P_Recursive THEN
    CALL `InvoiceDetails_RecalculateInternals_Single`(P_InvoiceID, null); --
  END IF; --

  CALL `Invoice_InternalUpdateBalance`(P_InvoiceID); --
END