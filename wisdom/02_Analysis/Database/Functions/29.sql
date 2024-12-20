CREATE DEFINER=`root`@`localhost` PROCEDURE `PurchaseOrder_UpdateTotals`(P_PurchaseOrderID INT)
BEGIN
  DECLARE V_Cost double; --

  SELECT Sum(Price * Ordered)
  INTO V_Cost
  FROM tbl_purchaseorderdetails
  WHERE (PurchaseOrderID = P_PurchaseOrderID); --

  UPDATE tbl_purchaseorder
  SET Cost = IfNull(V_Cost, 0),
      TotalDue = IfNull(V_Cost, 0) + IfNull(Freight, 0) + IfNull(Tax, 0)
  WHERE (ID = P_PurchaseOrderID); --
END