CREATE DEFINER=`root`@`localhost` PROCEDURE `order_process`(P_OrderID INT, P_BillingMonth INT, P_BillingFlags INT, P_InvoiceDate DATE, OUT P_InvoiceID INT)
BEGIN
  CALL `Order_InternalProcess`(P_OrderID, P_BillingMonth, P_BillingFlags, P_InvoiceDate, P_InvoiceID); --
  IF (P_InvoiceID IS NOT NULL) THEN
    CALL `InvoiceDetails_RecalculateInternals_Single`(P_InvoiceID, null); --
    CALL `Invoice_InternalUpdatePendingSubmissions`  (P_InvoiceID); --
    CALL `InvoiceDetails_RecalculateInternals_Single`(P_InvoiceID, null); --
    CALL `Invoice_InternalUpdateBalance`             (P_InvoiceID); --
  END IF; --
END