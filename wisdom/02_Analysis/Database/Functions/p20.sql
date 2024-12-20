CREATE DEFINER=`root`@`localhost` FUNCTION `InvoiceMustBeSkipped`(
  P_DeliveryDate DATETIME, P_DosFrom DATETIME, P_SaleRentType VARCHAR(50), P_BillingMonth INT,
  P_Modifier1 VARCHAR(8), P_Modifier2 VARCHAR(8), P_Modifier3 VARCHAR(8), P_Modifier4 VARCHAR(8)) RETURNS bit(1)
    DETERMINISTIC
BEGIN
  -- means that we should not generate invoice
  -- 'Capped rental' with delivery date after 2006-01-01 will be treated like 'Rent to Purchase'
  IF P_BillingMonth <= 0 THEN
    SET P_BillingMonth = 1; --
  END IF; --

  IF P_SaleRentType IN ('One Time Sale', 'Re-occurring Sale', 'One Time Rental') THEN
    RETURN (1 < P_BillingMonth); --
  ELSEIF P_SaleRentType = 'Medicare Oxygen Rental' THEN
    IF P_DeliveryDate < '2006-01-01' THEN
      RETURN ('2009-01-01' <= P_DosFrom) AND (36 < P_BillingMonth); --
    ELSE
      RETURN (36 < P_BillingMonth); --
    END IF; --
  ELSEIF P_SaleRentType = 'Monthly Rental' THEN
    RETURN 0; --
  ELSEIF P_SaleRentType = 'Rent to Purchase' THEN
    RETURN (10 < P_BillingMonth); --
  ELSEIF P_SaleRentType = 'Capped Rental' OR P_SaleRentType = 'Parental Capped Rental' THEN
    IF P_DeliveryDate < '2006-01-01' THEN
      IF (P_BillingMonth <= 15) THEN
        RETURN 0; --
      ELSEIF (P_BillingMonth < 22) THEN
        RETURN 1; --
      ELSE
        RETURN ((P_BillingMonth - 22) mod 6 != 0); --
      END IF; --
    ELSE
      RETURN (13 < P_BillingMonth); --
    END IF; --
  END IF; --

  RETURN 0; --
END