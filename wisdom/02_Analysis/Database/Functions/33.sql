CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_AddSubmitted`(
  P_InvoiceDetailsID INT,
  P_Amount DECIMAL(18,2),
  P_SubmittedTo VARCHAR(50),
  P_SubmittedBy VARCHAR(50),
  P_SubmittedBatch VARCHAR(50),
  P_LastUpdateUserID smallint)
BEGIN
  CALL InvoiceDetails_InternalAddSubmitted(P_InvoiceDetailsID, P_Amount, P_SubmittedTo, P_SubmittedBy, P_SubmittedBatch, P_LastUpdateUserID); --
  CALL InvoiceDetails_RecalculateInternals_Single(null, P_InvoiceDetailsID); --
END