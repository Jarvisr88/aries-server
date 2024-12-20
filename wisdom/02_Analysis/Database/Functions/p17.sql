CREATE DEFINER=`root`@`localhost` FUNCTION `GetPeriodEnd`(P_FromDate DATETIME, P_ToDate DATETIME, P_Frequency VARCHAR(50)) RETURNS datetime
    DETERMINISTIC
BEGIN
  IF     P_Frequency = 'One time'         THEN RETURN P_FromDate; --
  ELSEIF P_Frequency = 'Daily'            THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 01 DAY  ), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Weekly'           THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 07 DAY  ), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Monthly'          THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 01 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Calendar Monthly' THEN
    SET P_FromDate = DATE_ADD(P_FromDate, INTERVAL 1 MONTH); --
    RETURN DATE_ADD(P_FromDate, INTERVAL 0-DAY(P_FromDate) DAY); --
  ELSEIF P_Frequency = 'Quarterly'        THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 03 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Semi-Annually'    THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 06 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Annually'         THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 12 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Custom'           THEN RETURN P_ToDate; --
  END IF; --

  RETURN NULL; --
END