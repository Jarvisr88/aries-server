CREATE DEFINER=`root`@`localhost` PROCEDURE `fixOrderPolicies`()
BEGIN
  UPDATE tbl_order
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_order.CustomerInsurance1_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_order.CustomerID
  SET tbl_order.CustomerInsurance1_ID = tbl_customer_insurance.ID; --

  UPDATE tbl_order
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_order.CustomerInsurance2_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_order.CustomerID
  SET tbl_order.CustomerInsurance2_ID = tbl_customer_insurance.ID; --

  UPDATE tbl_order
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_order.CustomerInsurance3_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_order.CustomerID
  SET tbl_order.CustomerInsurance3_ID = tbl_customer_insurance.ID; --

  UPDATE tbl_order
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_order.CustomerInsurance4_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_order.CustomerID
  SET tbl_order.CustomerInsurance4_ID = tbl_customer_insurance.ID; --
END