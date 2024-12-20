CREATE DEFINER=`root`@`localhost` FUNCTION `GetNewDosTo`(P_NewFromDate DATETIME, P_OldFromDate DATETIME, P_OldToDate DATETIME, P_Frequency VARCHAR(50)) RETURNS datetime
    DETERMINISTIC
BEGIN
  DECLARE V_LENGTH INT; --

  IF     P_Frequency = 'One time'         THEN RETURN P_NewFromDate; --
  ELSEIF P_Frequency = 'Daily'            THEN RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL 01 DAY  ), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Weekly'           THEN RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL 07 DAY  ), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Monthly'          THEN RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL 01 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Calendar Monthly' THEN
    SET P_NewFromDate = DATE_ADD(P_NewFromDate, INTERVAL 01 MONTH); --
    RETURN DATE_ADD(P_NewFromDate, INTERVAL 0-DAY(P_NewFromDate) DAY); -- end of month
  ELSEIF P_Frequency = 'Quarterly'        THEN RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL 03 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Semi-Annually'    THEN RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL 06 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Annually'         THEN RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL 12 MONTH), INTERVAL -1 DAY); --
  ELSEIF P_Frequency = 'Custom'           THEN
    SET V_LENGTH = DATEDIFF(P_OldToDate, P_OldFromDate) + 1; --
    RETURN DATE_ADD(DATE_ADD(P_NewFromDate, INTERVAL V_LENGTH DAY), INTERVAL -1 DAY); --
  END IF; --

  RETURN NULL; --
END