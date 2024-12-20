CREATE DEFINER=`root`@`localhost` FUNCTION `OrderedQty2DeliveryQty`(
    P_FromDate DATE,
    P_ToDate DATE,
    P_OrderedQty DOUBLE,
    P_OrderedWhen VARCHAR(50),
    P_BilledWhen VARCHAR(50),
    P_OrderedConverter DOUBLE,
    P_DeliveryConverter DOUBLE,
    P_BilledConverter DOUBLE /* Unused parameter */) RETURNS double
    DETERMINISTIC
BEGIN
  DECLARE V_Multiplier INT; --

  IF P_OrderedConverter < 0.000000001 THEN
    RETURN 0; /* Parameter OrderedConverter must be greater than zero */
  END IF; --

  IF P_DeliveryConverter < 0.000000001 THEN
    RETURN 0; /* Paramater DeliveryConverter must be greater than zero */
  END IF; --

  SET V_Multiplier = GetMultiplier(P_FromDate, P_ToDate, P_OrderedWhen, P_BilledWhen); --

  RETURN CEILING(P_OrderedQty * V_Multiplier * P_OrderedConverter / P_DeliveryConverter); --
END