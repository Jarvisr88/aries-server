CREATE DEFINER=`root`@`localhost` FUNCTION `GetPeriodEnd2`(P_FromDate DATETIME, P_ToDate DATETIME, P_PickupDate DATETIME, P_Frequency VARCHAR(50)) RETURNS datetime
    DETERMINISTIC
BEGIN
  DECLARE V_PeriodEnd DATETIME; --

  SET V_PeriodEnd = `GetPeriodEnd`(P_FromDate, P_ToDate, P_Frequency); --

  IF     P_PickupDate IS NULL        THEN RETURN V_PeriodEnd; --
  ELSEIF V_PeriodEnd <= P_PickupDate THEN RETURN V_PeriodEnd; --
  ELSEIF P_FromDate  <= P_PickupDate THEN RETURN P_PickupDate; --
  END IF; --

  RETURN P_FromDate; --
END