CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_doctor`(P_DoctorID INT)
BEGIN
  CALL `dmeworks`.`mir_update_doctor`(P_DoctorID); --
END