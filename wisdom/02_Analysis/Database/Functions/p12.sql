CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_WriteoffBalance`( P_InvoiceID TEXT
, P_InvoiceDetailsID TEXT
, P_LastUpdateUserID SMALLINT)
BEGIN
  CALL InvoiceDetails_RecalculateInternals   (P_InvoiceID, P_InvoiceDetailsID); --
  CALL InvoiceDetails_InternalWriteoffBalance(P_InvoiceID, P_InvoiceDetailsID, P_LastUpdateUserID); --
  CALL InvoiceDetails_RecalculateInternals   (P_InvoiceID, P_InvoiceDetailsID); --
END