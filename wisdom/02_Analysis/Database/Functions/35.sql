CREATE DEFINER=`root`@`localhost` PROCEDURE `Order_InternalUpdateBalance`(P_OrderID INT)
BEGIN
  UPDATE tbl_invoice as i
  INNER JOIN tbl_order as o ON i.CustomerID = o.CustomerID
                           AND i.OrderID    = o.ID
  LEFT JOIN (SELECT tbl_invoicedetails.InvoiceID, Sum(tbl_invoicedetails.Balance) as Balance
             FROM tbl_order
                  INNER JOIN tbl_invoice ON tbl_invoice.CustomerID = tbl_order.CustomerID
                                        AND tbl_invoice.OrderID    = tbl_order.ID
                  INNER JOIN tbl_invoicedetails ON tbl_invoicedetails.CustomerID = tbl_invoice.CustomerID
                                               AND tbl_invoicedetails.InvoiceID  = tbl_invoice.ID
             WHERE (tbl_order.ID = P_OrderID)
             GROUP BY tbl_invoicedetails.InvoiceID) as b
         ON b.InvoiceID = i.ID
  SET i.InvoiceBalance = IFNULL(b.Balance, 0)
  WHERE (o.ID = P_OrderID); --
END