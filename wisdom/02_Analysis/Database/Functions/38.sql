CREATE DEFINER=`root`@`localhost` FUNCTION `GetAllowableAmount`(
  P_SaleRentType VARCHAR(50),
  P_BillingMonth INT,
  P_Price DECIMAL(18, 2),
  P_Quantity INT,
  P_SalePrice DECIMAL(18, 2),
  B_FlatRate BIT) RETURNS decimal(18,2)
    DETERMINISTIC
BEGIN
  IF P_BillingMonth <= 0 THEN
    SET P_BillingMonth = 1; --
  END IF; --

  IF B_FlatRate = 1 THEN
    SET P_Quantity = 1; --
  END IF; --

  IF P_SaleRentType IN ('One Time Sale', 'Re-occurring Sale', 'One Time Rental') THEN
    IF P_BillingMonth = 1 THEN
      RETURN P_Price * P_Quantity; --
    END IF; --
  ELSEIF P_SaleRentType IN ('Medicare Oxygen Rental','Monthly Rental') THEN
    RETURN P_Price * P_Quantity; --
  ELSEIF P_SaleRentType = 'Rent to Purchase' THEN
    IF P_BillingMonth <= 9 THEN
      RETURN P_Price * P_Quantity; --
    ELSEIF P_BillingMonth = 10 THEN
      RETURN (P_SalePrice - 9 * P_Price) * P_Quantity; --
    END IF; --
  ELSEIF P_SaleRentType = 'Capped Rental' THEN
    IF P_BillingMonth <= 3 THEN
      RETURN P_Price * P_Quantity; --
    ELSEIF P_BillingMonth <= 15 THEN
      RETURN 0.75 * P_Price * P_Quantity; --
    ELSEIF (22 <= P_BillingMonth) AND ((P_BillingMonth - 22) Mod 6 = 0) THEN
      RETURN P_Price * P_Quantity; --
    END IF; --
  ELSEIF P_SaleRentType = 'Parental Capped Rental' THEN
    IF P_BillingMonth <= 15 THEN
      RETURN P_Price * P_Quantity; --
    ELSEIF (22 <= P_BillingMonth) AND ((P_BillingMonth - 22) Mod 6 = 0) THEN
      RETURN P_Price * P_Quantity; --
    END IF; --
  END IF; --

  RETURN 0.00; --
END