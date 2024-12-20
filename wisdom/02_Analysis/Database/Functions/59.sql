CREATE DEFINER=`root`@`localhost` FUNCTION `GetInvoiceModifier`(
  P_DeliveryDate DATETIME, P_SaleRentType VARCHAR(50), P_BillingMonth INT, P_Index INT,
  P_Modifier1 VARCHAR(8), P_Modifier2 VARCHAR(8),
  P_Modifier3 VARCHAR(8), P_Modifier4 VARCHAR(8)) RETURNS varchar(2) CHARSET latin1 COLLATE latin1_general_ci
    DETERMINISTIC
BEGIN
  IF P_BillingMonth <= 0 THEN
    SET P_BillingMonth = 1; --
  END IF; --

  IF P_SaleRentType = 'Capped Rental' OR P_SaleRentType = 'Parental Capped Rental' THEN
    IF     P_Index = 1 THEN
      IF (22 <= P_BillingMonth) AND ((P_BillingMonth - 22) Mod 6 = 0) THEN
        RETURN 'MS'; --
      ELSE
        RETURN 'RR'; --
      END IF; --
    ELSEIF P_Index = 2 THEN
      IF P_BillingMonth = 1 THEN
        RETURN 'KH'; --
      ELSEIF P_BillingMonth <= 3 THEN
        RETURN 'KI'; --
      ELSEIF P_BillingMonth <= 15 THEN
        RETURN 'KJ'; --
      ELSEIF (22 <= P_BillingMonth) AND ((P_BillingMonth - 22) Mod 6 = 0) THEN
        IF P_Modifier4 = 'KX' THEN
          RETURN 'KX'; --
        ELSE
          RETURN ''; --
        END IF; --
      ELSE
        RETURN ''; --
      END IF; --
    ELSEIF P_Index = 3 THEN
      IF P_DeliveryDate < '2006-01-01' THEN
        IF (22 <= P_BillingMonth) AND ((P_BillingMonth - 22) Mod 6 = 0) THEN
          RETURN ''; --
        END IF; --
      ELSE
        IF (P_BillingMonth >= 12) THEN
          RETURN 'KX'; --
        END IF; --
      END IF; --
    ELSEIF P_Index = 4 THEN
      IF P_DeliveryDate < '2006-01-01' THEN
        IF (22 <= P_BillingMonth) AND ((P_BillingMonth - 22) Mod 6 = 0) THEN
          RETURN ''; --
        END IF; --
      ELSE
        IF (P_BillingMonth >= 12) THEN
          RETURN ''; --
        END IF; --
      END IF; --
    END IF; --
  END IF; --

  IF     P_Index = 1 THEN
    RETURN P_Modifier1; --
  ELSEIF P_Index = 2 THEN
    RETURN P_Modifier2; --
  ELSEIF P_Index = 3 THEN
    RETURN P_Modifier3; --
  ELSEIF P_Index = 4 THEN
    RETURN P_Modifier4; --
  ELSE
    RETURN ''; --
  END IF; --
END