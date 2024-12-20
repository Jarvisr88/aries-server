CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update`()
BEGIN
  CALL mir_update_facility(null); --
  CALL mir_update_insurancecompany(null); --
  CALL mir_update_customer_insurance(null); --
  CALL mir_update_doctor(null); --
  CALL mir_update_customer(null); --
  CALL mir_update_cmnform(null); --
  CALL mir_update_orderdetails('ActiveOnly'); --
  CALL mir_update_order('ActiveOnly'); --
END