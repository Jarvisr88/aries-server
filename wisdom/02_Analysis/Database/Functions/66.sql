CREATE DEFINER=`root`@`localhost` FUNCTION `GetMultiplier`(P_FromDate DATETIME, P_ToDate DATETIME, P_OrderedWhen VARCHAR(50), P_BilledWhen VARCHAR(50)) RETURNS double
    DETERMINISTIC
BEGIN
  IF P_OrderedWhen = 'One Time' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'  AND P_BilledWhen = 'Daily' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'  AND P_BilledWhen = 'Weekly' THEN RETURN 7; --
  ELSEIF P_OrderedWhen = 'Weekly' AND P_BilledWhen = 'Weekly' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'   AND P_BilledWhen = 'Monthly' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate); --
  ELSEIF P_OrderedWhen = 'Weekly'  AND P_BilledWhen = 'Monthly' THEN RETURN 4; --
  ELSEIF P_OrderedWhen = 'Monthly' AND P_BilledWhen = 'Monthly' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'   AND P_BilledWhen = 'Calendar Monthly' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate); --
  ELSEIF P_OrderedWhen = 'Weekly'  AND P_BilledWhen = 'Calendar Monthly' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate) / 7.0; --
  ELSEIF P_OrderedWhen = 'Monthly' AND P_BilledWhen = 'Calendar Monthly' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'     AND P_BilledWhen = 'Quarterly' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate); --
  ELSEIF P_OrderedWhen = 'Weekly'    AND P_BilledWhen = 'Quarterly' THEN RETURN 13; --
  ELSEIF P_OrderedWhen = 'Monthly'   AND P_BilledWhen = 'Quarterly' THEN RETURN 3; --
  ELSEIF P_OrderedWhen = 'Quarterly' AND P_BilledWhen = 'Quarterly' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'         AND P_BilledWhen = 'Semi-Annually' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate); --
  ELSEIF P_OrderedWhen = 'Weekly'        AND P_BilledWhen = 'Semi-Annually' THEN RETURN 26; --
  ELSEIF P_OrderedWhen = 'Monthly'       AND P_BilledWhen = 'Semi-Annually' THEN RETURN 6; --
  ELSEIF P_OrderedWhen = 'Quarterly'     AND P_BilledWhen = 'Semi-Annually' THEN RETURN 2; --
  ELSEIF P_OrderedWhen = 'Semi-Annually' AND P_BilledWhen = 'Semi-Annually' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'         AND P_BilledWhen = 'Annually' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate); --
  ELSEIF P_OrderedWhen = 'Weekly'        AND P_BilledWhen = 'Annually' THEN RETURN 52; --
  ELSEIF P_OrderedWhen = 'Monthly'       AND P_BilledWhen = 'Annually' THEN RETURN 12; --
  ELSEIF P_OrderedWhen = 'Quarterly'     AND P_BilledWhen = 'Annually' THEN RETURN 4; --
  ELSEIF P_OrderedWhen = 'Semi-Annually' AND P_BilledWhen = 'Annually' THEN RETURN 2; --
  ELSEIF P_OrderedWhen = 'Annually'      AND P_BilledWhen = 'Annually' THEN RETURN 1; --

  ELSEIF P_OrderedWhen = 'Daily'  AND P_BilledWhen = 'Custom' THEN RETURN DATEDIFF(GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen), P_FromDate); --

  END IF; --

  RETURN NULL; --
END