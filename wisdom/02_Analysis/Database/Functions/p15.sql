CREATE DEFINER=`root`@`localhost` PROCEDURE `serials_refresh`()
BEGIN
  DECLARE V_SerialID INT; --
  DECLARE done INT DEFAULT 0; --

  DECLARE cur CURSOR FOR
    SELECT ID
    FROM tbl_serial
    WHERE (1 = 1); --
  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO
      V_SerialID; --

    IF NOT done THEN
      CALL serial_refresh(V_SerialID); --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END