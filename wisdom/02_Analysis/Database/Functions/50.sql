CREATE DEFINER=`root`@`localhost` PROCEDURE `order_process_2`(P_OrderID INT, P_BillingMonth INT, P_BillingFlags INT, P_InvoiceDate DATE)
BEGIN
  DECLARE V_InvoiceID INT; --
  SET V_InvoiceID = null; --

  CALL `Order_InternalProcess`(P_OrderID, P_BillingMonth, P_BillingFlags, P_InvoiceDate, V_InvoiceID); --
  IF (V_InvoiceID IS NOT NULL) THEN
    CALL `InvoiceDetails_RecalculateInternals_Single`(V_InvoiceID, null); --
    CALL `Invoice_InternalUpdatePendingSubmissions`  (V_InvoiceID); --
    CALL `InvoiceDetails_RecalculateInternals_Single`(V_InvoiceID, null); --
    CALL `Invoice_InternalUpdateBalance`             (V_InvoiceID); --
  END IF; --
END