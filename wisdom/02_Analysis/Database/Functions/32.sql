CREATE DEFINER=`root`@`localhost` PROCEDURE `InventoryItem_Clone`(P_OldInventoryItemID INT, P_NewName VARCHAR(100), OUT P_NewInventoryItemID INT)
BEGIN
  DECLARE V_RowCount INT; --

  INSERT INTO tbl_inventoryitem (
    Barcode
  , BarcodeType
  , Basis
  , CommissionPaidAt
  , VendorID
  , FlatRate
  , FlatRateAmount
  , Frequency
  , InventoryCode
  , ModelNumber
  , Name
  , O2Tank
  , Percentage
  , PercentageAmount
  , PredefinedTextID
  , ProductTypeID
  , Serialized
  , Service
  , LastUpdateUserID
  , LastUpdateDatetime
  , Inactive
  , ManufacturerID
  , PurchasePrice
  ) SELECT
    Barcode
  , BarcodeType
  , Basis
  , CommissionPaidAt
  , VendorID
  , FlatRate
  , FlatRateAmount
  , Frequency
  , InventoryCode
  , ModelNumber
  , IFNULL(P_NewName, Name) as Name
  , O2Tank
  , Percentage
  , PercentageAmount
  , PredefinedTextID
  , ProductTypeID
  , Serialized
  , Service
  , LastUpdateUserID
  , LastUpdateDatetime
  , Inactive
  , ManufacturerID
  , PurchasePrice
  FROM tbl_inventoryitem
  WHERE (ID = P_OldInventoryItemID); --

  SELECT ROW_COUNT(), LAST_INSERT_ID() INTO V_RowCount, P_NewInventoryItemID; --

  IF (V_RowCount = 0) THEN
    SET P_NewInventoryItemID = NULL; --
  ELSE
    INSERT INTO `tbl_pricecode_item` (
      AcceptAssignment
    , OrderedQuantity
    , OrderedUnits
    , OrderedWhen
    , OrderedConverter
    , BilledUnits
    , BilledWhen
    , BilledConverter
    , DeliveryUnits
    , DeliveryConverter
    , BillingCode
    , BillItemOn
    , DefaultCMNType
    , DefaultOrderType
    , AuthorizationTypeID
    , FlatRate
    , InventoryItemID
    , Modifier1
    , Modifier2
    , Modifier3
    , Modifier4
    , PriceCodeID
    , PredefinedTextID
    , Rent_AllowablePrice
    , Rent_BillablePrice
    , Sale_AllowablePrice
    , Sale_BillablePrice
    , RentalType
    , ReoccuringSale
    , ShowSpanDates
    , Taxable
    , LastUpdateUserID
    , LastUpdateDatetime
    , BillInsurance
    , DrugNoteField
    , DrugControlNumber
    ) SELECT
      AcceptAssignment
    , OrderedQuantity
    , OrderedUnits
    , OrderedWhen
    , OrderedConverter
    , BilledUnits
    , BilledWhen
    , BilledConverter
    , DeliveryUnits
    , DeliveryConverter
    , BillingCode
    , BillItemOn
    , DefaultCMNType
    , DefaultOrderType
    , AuthorizationTypeID
    , FlatRate
    , P_NewInventoryItemID as InventoryItemID
    , Modifier1
    , Modifier2
    , Modifier3
    , Modifier4
    , PriceCodeID
    , PredefinedTextID
    , Rent_AllowablePrice
    , Rent_BillablePrice
    , Sale_AllowablePrice
    , Sale_BillablePrice
    , RentalType
    , ReoccuringSale
    , ShowSpanDates
    , Taxable
    , LastUpdateUserID
    , LastUpdateDatetime
    , BillInsurance
    , DrugNoteField
    , DrugControlNumber
    FROM `tbl_pricecode_item`
    WHERE (InventoryItemID = P_OldInventoryItemID); --
  END IF; --
END