CREATE DEFINER=`root`@`localhost` PROCEDURE `Order_ConvertDepositsIntoPayments`(P_OrderID INT)
    MODIFIES SQL DATA
BEGIN
  -- for given OrderId we select all order lines with deposits that have invoice lines without "deposit" payments
  DECLARE V_InvoiceDetailsID INT; --
  DECLARE V_Amount, V_Billable DECIMAL(18, 2); --
  DECLARE V_Date DATE; --
  DECLARE V_PaymentMethod VARCHAR(20); --
  DECLARE V_Template, V_Extra TEXT; --
  DECLARE V_Element VARCHAR(100); --
  DECLARE V_Result VARCHAR(50); --
  DECLARE done INT DEFAULT 0; --
  DECLARE cur CURSOR FOR
    SELECT il.ID, dd.Amount, d.Date, d.PaymentMethod, il.BillableAmount
    FROM tbl_order AS o
         INNER JOIN tbl_orderdetails AS od ON od.CustomerID = o.CustomerID
                                          AND od.OrderID    = o.ID
         INNER JOIN tbl_deposits AS d ON d.CustomerID = od.CustomerID
                                     AND d.OrderID    = od.OrderID
         INNER JOIN tbl_depositdetails AS dd ON dd.CustomerID     = od.CustomerID
                                            AND dd.OrderID        = od.OrderID
                                            AND dd.OrderDetailsID = od.ID
         INNER JOIN tbl_invoice AS i ON i.CustomerID = o.CustomerID
                                    AND i.OrderID    = o.ID
         INNER JOIN tbl_invoicedetails AS il ON il.CustomerID     = i.CustomerID
                                            AND il.InvoiceID      = i.ID
                                            AND il.BillingMonth   = 1 -- only first billing month
                                            AND il.OrderID        = od.OrderID
                                            AND il.OrderDetailsID = od.ID
         INNER JOIN tbl_invoice_transactiontype as tt ON tt.Name = 'Payment'
         LEFT JOIN tbl_invoice_transaction as p ON p.CustomerID       = il.CustomerID
                                               AND p.InvoiceID        = il.InvoiceID
                                               AND p.InvoiceDetailsID = il.ID
                                               AND p.InsuranceCompanyID IS NULL
                                               AND p.CustomerInsuranceID IS NULL
                                               AND p.TransactionTypeID = tt.ID
                                               AND p.TransactionDate   = d.Date
                                               AND p.Amount            = dd.Amount
    WHERE (o.ID = P_OrderID)
      AND (p.ID is null); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  SET V_Template = '<values>
  <v n="Billable">0.00</v>
  <v n="CheckDate">00/00/0000</v>
  <v n="Paid">0.00</v>
  <v n="PaymentMethod">Check</v>
</values>'; --

  OPEN cur; --

  DEPOSITS_LOOP: LOOP
    FETCH cur INTO V_InvoiceDetailsID, V_Amount, V_Date, V_PaymentMethod, V_Billable; --

    IF done THEN
      LEAVE DEPOSITS_LOOP; --
    END IF; --

    SET V_Extra = V_Template; --
    SET V_Element = CONCAT('<v n="Billable">', IFNULL(CAST(V_Billable as CHAR), ''), '</v>'); --
    SET V_Extra = UpdateXML(V_Extra, 'values/v[@n="Billable"]' COLLATE latin1_general_ci, V_Element COLLATE latin1_general_ci); --
    SET V_Element = CONCAT('<v n="CheckDate">', IFNULL(DATE_FORMAT(V_Date, '%m/%d/%Y'), ''), '</v>'); --
    SET V_Extra = UpdateXML(V_Extra, 'values/v[@n="CheckDate"]' COLLATE latin1_general_ci, V_Element COLLATE latin1_general_ci); --
    SET V_Element = CONCAT('<v n="Paid">', IFNULL(CAST(V_Amount as CHAR), ''), '</v>'); --
    SET V_Extra = UpdateXML(V_Extra, 'values/v[@n="Paid"]' COLLATE latin1_general_ci, V_Element COLLATE latin1_general_ci); --
    SET V_Element = CONCAT('<v n="PaymentMethod">', IFNULL(CAST(V_PaymentMethod as CHAR), 'Check'), '</v>'); --
    SET V_Extra = UpdateXML(V_Extra, 'values/v[@n="PaymentMethod"]' COLLATE latin1_general_ci, V_Element COLLATE latin1_general_ci); --

    CALL `InvoiceDetails_AddPayment`
    ( V_InvoiceDetailsID
    , NULL -- P_InsuranceCompanyID
    , V_Date
    , V_Extra
    , 'Deposit' -- P_Comments
    , '' -- P_Options
    , IFNULL(@UserId, 1)
    , V_Result); --
  END LOOP DEPOSITS_LOOP; --

  CLOSE cur; --

  CALL `Order_InternalUpdateBalance`(P_OrderID); --
END