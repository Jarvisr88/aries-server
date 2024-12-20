CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_insurancecompany`(P_InsuranceCompanyID INT)
BEGIN
  CALL `dmeworks`.`mir_update_insurancecompany`(P_InsuranceCompanyID); --
END