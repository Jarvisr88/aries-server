CREATE DEFINER=`root`@`localhost` PROCEDURE `order_update_dos`(P_OrderID INT, P_DOSFrom DATE)
BEGIN
  IF P_DOSFrom IS NOT NULL THEN
    UPDATE view_orderdetails as details
           INNER JOIN tbl_order ON details.CustomerID = tbl_order.CustomerID
                               AND details.OrderID    = tbl_order.ID
    SET
      details.DosFrom = P_DOSFrom
    , details.DosTo   = GetNewDosTo(P_DOSFrom, details.DosFrom, details.DosTo, details.ActualBilledWhen)
    -- ordered quantity will not change
    , details.BilledQuantity = OrderedQty2BilledQty(P_DOSFrom, GetNewDosTo(P_DOSFrom, details.DosFrom, details.DosTo, details.ActualBilledWhen),
        details.OrderedQuantity, details.OrderedWhen, details.BilledWhen,
        details.OrderedConverter, details.DeliveryConverter, details.BilledConverter)
    , details.DeliveryQuantity = OrderedQty2DeliveryQty(P_DOSFrom, GetNewDosTo(P_DOSFrom, details.DosFrom, details.DosTo, details.ActualBilledWhen),
        details.OrderedQuantity, details.OrderedWhen, details.BilledWhen,
        details.OrderedConverter, details.DeliveryConverter, details.BilledConverter)
    WHERE (tbl_order.ID = P_OrderID)
      AND (tbl_order.Approved = 0); --
  END IF; --
END