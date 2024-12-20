CREATE DEFINER=`root`@`localhost` PROCEDURE `customer_insurance_fixrank`(P_CustomerID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE V_ID, V_Rank INT; --
  DECLARE cur CURSOR FOR
    SELECT ID
    FROM tbl_customer_insurance
    WHERE (CustomerID = P_CustomerID)
    ORDER BY IF(InactiveDate <= Current_Date(), 1, 0), `Rank`, ID; --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  SET V_Rank = 1; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO V_ID; --

    IF NOT done THEN
      UPDATE tbl_customer_insurance SET `Rank` = IF(InactiveDate <= Current_Date(), 99999, V_Rank) WHERE (ID = V_ID) AND (CustomerID = P_CustomerID); --
      SET V_Rank = V_Rank + 1; --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END