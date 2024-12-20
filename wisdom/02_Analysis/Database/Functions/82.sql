CREATE DEFINER=`root`@`localhost` FUNCTION `OrderMustBeClosed`(
  P_DeliveryDate DATETIME, P_DosFrom DATETIME, P_SaleRentType VARCHAR(50), P_BillingMonth INT,
  P_Modifier1 VARCHAR(8), P_Modifier2 VARCHAR(8), P_Modifier3 VARCHAR(8), P_Modifier4 VARCHAR(8)) RETURNS bit(1)
    DETERMINISTIC
BEGIN
  -- means that we should stop billing (that is we should set EndDate = InvoiceDate and State = 'Closed')
  IF P_BillingMonth <= 0 THEN
    SET P_BillingMonth = 1; --
  END IF; --

  IF P_SaleRentType IN ('One Time Sale', 'Re-occurring Sale', 'One Time Rental') THEN
    RETURN (1 <= P_BillingMonth); --
  ELSEIF P_SaleRentType = 'Medicare Oxygent Rental' THEN
    IF P_DeliveryDate < '2006-01-01' THEN
      RETURN ('2009-01-01' <= P_DosFrom) AND (36 <= P_BillingMonth); --
    ELSE
      -- we bill only 36 monthes but contract is 60 monthes
      RETURN (60 <= P_BillingMonth); --
    END IF; --
  ELSEIF P_SaleRentType = 'Monthly Rental' THEN
    RETURN 0; --
  ELSEIF P_SaleRentType = 'Rent to Purchase' THEN
    RETURN (10 <= P_BillingMonth); --
  ELSEIF P_SaleRentType = 'Capped Rental' OR P_SaleRentType = 'Parental Capped Rental' THEN
    IF P_DeliveryDate < '2006-01-01' THEN
      RETURN (12 <= P_BillingMonth) and (P_BillingMonth <= 13) and (P_Modifier3 = 'BP'); --
    ELSE
      RETURN (13 <= P_BillingMonth); --
    END IF; --
  END IF; --

  RETURN 0; --
END