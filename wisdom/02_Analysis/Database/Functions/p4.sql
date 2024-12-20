CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_Reflag`(P_InvoiceID TEXT, P_InvoiceDetailsID TEXT, P_LastUpdateUserID SMALLINT)
BEGIN
  CALL InvoiceDetails_RecalculateInternals(P_InvoiceID, P_InvoiceDetailsID); --
  CALL InvoiceDetails_InternalReflag      (P_InvoiceID, P_InvoiceDetailsID, P_LastUpdateUserID); --
  CALL InvoiceDetails_RecalculateInternals(P_InvoiceID, P_InvoiceDetailsID); --
END