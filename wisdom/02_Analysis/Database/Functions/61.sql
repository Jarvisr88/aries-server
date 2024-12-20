CREATE DEFINER=`root`@`localhost` PROCEDURE `Invoice_InternalUpdateBalance`(P_InvoiceID INT)
BEGIN
  UPDATE tbl_invoice as i
  LEFT JOIN (SELECT tbl_invoicedetails.InvoiceID, Sum(tbl_invoicedetails.Balance) as Balance
             FROM tbl_invoice
                  INNER JOIN tbl_invoicedetails ON tbl_invoicedetails.CustomerID = tbl_invoice.CustomerID
                                               AND tbl_invoicedetails.InvoiceID  = tbl_invoice.ID
             WHERE (tbl_invoice.ID = P_InvoiceID)
             GROUP BY tbl_invoicedetails.InvoiceID) as b
         ON b.InvoiceID = i.ID
  SET i.InvoiceBalance = IFNULL(b.Balance, 0)
  WHERE (i.ID = P_InvoiceID); --
END