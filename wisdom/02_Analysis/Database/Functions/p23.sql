CREATE DEFINER=`root`@`localhost` PROCEDURE `fixInvoicePolicies`()
BEGIN
  UPDATE tbl_invoice
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_invoice.CustomerInsurance1_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_invoice.CustomerID
  SET tbl_invoice.CustomerInsurance1_ID = tbl_customer_insurance.ID; --

  UPDATE tbl_invoice
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_invoice.CustomerInsurance2_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_invoice.CustomerID
  SET tbl_invoice.CustomerInsurance2_ID = tbl_customer_insurance.ID; --

  UPDATE tbl_invoice
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_invoice.CustomerInsurance3_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_invoice.CustomerID
  SET tbl_invoice.CustomerInsurance3_ID = tbl_customer_insurance.ID; --

  UPDATE tbl_invoice
        INNER JOIN tbl_customer_insurance ON tbl_customer_insurance.InsuranceCompanyID = tbl_invoice.CustomerInsurance4_ID
                                          AND tbl_customer_insurance.CustomerID = tbl_invoice.CustomerID
  SET tbl_invoice.CustomerInsurance4_ID = tbl_customer_insurance.ID; --
END