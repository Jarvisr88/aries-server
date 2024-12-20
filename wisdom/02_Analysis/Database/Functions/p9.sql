CREATE DEFINER=`root`@`localhost` FUNCTION `GetNextDosTo`(P_FromDate DATETIME, P_ToDate DATETIME, P_Frequency VARCHAR(50)) RETURNS datetime
    DETERMINISTIC
BEGIN
  DECLARE V_LENGTH INT; --

  IF     P_Frequency = 'One time'         THEN RETURN P_FromDate; --
  ELSEIF P_Frequency = 'Daily'            THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * 01 DAY  ), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Weekly'           THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * 07 DAY  ), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Monthly'          THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * 01 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Calendar Monthly' THEN
    SET P_FromDate = DATE_ADD(P_FromDate, INTERVAL 02 MONTH); --
    RETURN DATE_ADD(P_FromDate, INTERVAL 0-DAY(P_FromDate) DAY); --
  ELSEIF P_Frequency = 'Quarterly'        THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * 03 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Semi-Annually'    THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * 06 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Annually'         THEN RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * 12 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Custom'           THEN
    SET V_LENGTH = DATEDIFF(P_ToDate, P_FromDate) + 1; --
    RETURN DATE_ADD(DATE_ADD(P_FromDate, INTERVAL 2 * V_LENGTH DAY), INTERVAL -1 DAY); --
  END IF; --

  RETURN NULL; --
END