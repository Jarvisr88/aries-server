CREATE DEFINER=`root`@`localhost` PROCEDURE `process_reoccuring_purchaseorder`(P_PurchaseOrderID INT)
BEGIN
    -- reoccuring purchase order support
    DECLARE V_NewOrderID INT; --

    -- create order
    INSERT INTO tbl_purchaseorder
      (Approved
      ,Reoccuring
      ,Cost
      ,Freight
      ,Tax
      ,TotalDue
      ,VendorID
      ,ShipToName
      ,ShipToAddress1
      ,ShipToAddress2
      ,ShipToCity
      ,ShipToState
      ,ShipToZip
      ,ShipToPhone
      ,OrderDate
      ,CompanyName
      ,CompanyAddress1
      ,CompanyAddress2
      ,CompanyCity
      ,CompanyState
      ,CompanyZip
      ,ShipVia
      ,FOB
      ,VendorSalesRep
      ,Terms
      ,CompanyPhone
      ,TaxRateID
      ,LastUpdateUserID)
    SELECT
       Approved
      ,Reoccuring
      ,Cost
      ,Freight
      ,Tax
      ,TotalDue
      ,VendorID
      ,ShipToName
      ,ShipToAddress1
      ,ShipToAddress2
      ,ShipToCity
      ,ShipToState
      ,ShipToZip
      ,ShipToPhone
      ,OrderDate
      ,CompanyName
      ,CompanyAddress1
      ,CompanyAddress2
      ,CompanyCity
      ,CompanyState
      ,CompanyZip
      ,ShipVia
      ,FOB
      ,VendorSalesRep
      ,Terms
      ,CompanyPhone
      ,TaxRateID
      ,LastUpdateUserID
    FROM
    (
        SELECT
             0 as Approved
            ,1 as Reoccuring
            ,Cost
            ,Freight
            ,Tax
            ,TotalDue
            ,VendorID
            ,ShipToName
            ,ShipToAddress1
            ,ShipToAddress2
            ,ShipToCity
            ,ShipToState
            ,ShipToZip
            ,ShipToPhone
            ,DATE_ADD(OrderDate, INTERVAL 1 MONTH) as OrderDate
            ,CompanyName
            ,CompanyAddress1
            ,CompanyAddress2
            ,CompanyCity
            ,CompanyState
            ,CompanyZip
            ,ShipVia
            ,FOB
            ,VendorSalesRep
            ,Terms
            ,CompanyPhone
            ,TaxRateID
            ,0 as LastUpdateUserID
        FROM tbl_purchaseorder
        WHERE (Reoccuring = 1)
          AND (ID = P_PurchaseOrderID)
    ) as `tmp`; --

    SELECT LAST_INSERT_ID() INTO V_NewOrderID; --

  IF V_NewOrderID <> 0 THEN
    -- add line items to order
    INSERT INTO tbl_purchaseorderdetails
      (BackOrder
      ,Ordered
      ,Received
      ,Price
      ,Customer
      ,DatePromised
      ,DateReceived
      ,DropShipToCustomer
      ,InventoryItemID
      ,PurchaseOrderID
      ,WarehouseID
      ,LastUpdateUserID
      ,LastUpdateDatetime
      ,VendorSTKNumber
      ,ReferenceNumber)
    SELECT
       BackOrder
      ,Ordered
      ,Received
      ,Price
      ,Customer
      ,DatePromised
      ,DateReceived
      ,DropShipToCustomer
      ,InventoryItemID
      ,PurchaseOrderID
      ,WarehouseID
      ,LastUpdateUserID
      ,LastUpdateDatetime
      ,VendorSTKNumber
      ,ReferenceNumber
    FROM (
        SELECT
           0 as BackOrder
          ,Ordered as Ordered
          ,0 as Received
          ,Price
          ,Customer
          ,DATE_ADD(DatePromised, INTERVAL 1 MONTH) as DatePromised
          ,null as DateReceived
          ,DropShipToCustomer
          ,InventoryItemID
          ,V_NewOrderID as PurchaseOrderID
          ,WarehouseID
          ,LastUpdateUserID
          ,CURRENT_DATE as LastUpdateDatetime
          ,VendorSTKNumber
          ,ReferenceNumber
        FROM tbl_purchaseorderdetails
        WHERE (PurchaseOrderID = P_PurchaseOrderID)
    ) as `tmp`; --

    -- update source -- mark them as one time sales
    UPDATE tbl_purchaseorder
    SET Reoccuring = 0
    WHERE (Reoccuring = 1)
      AND (ID = P_PurchaseOrderID); --
  END IF; --
END