CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_customer_insurance`(P_CustomerID INT)
BEGIN
  UPDATE tbl_customer_insurance as policy
         LEFT JOIN tbl_customer ON policy.CustomerID = tbl_customer.ID
         LEFT JOIN tbl_insurancecompany ON policy.InsuranceCompanyID = tbl_insurancecompany.ID
  SET policy.`MIR` =
      IF(tbl_customer.CommercialAccount = 0
        ,CONCAT_WS(','
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.FirstName, '') = ''), 'FirstName'  , null)
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.LastName , '') = ''), 'LastName'   , null)
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.Address1 , '') = ''), 'Address1'   , null)
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.City     , '') = ''), 'City'       , null)
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.State    , '') = ''), 'State'      , null)
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.Zip      , '') = ''), 'Zip'        , null)
                  ,IF((policy.RelationshipCode != '18') AND (IFNULL(policy.Gender   , '') = ''), 'Gender'     , null)
                  ,IF((policy.RelationshipCode != '18') AND (policy.DateofBirth IS NULL       ), 'DateofBirth', null)
                  ,IF(IFNULL(policy.InsuranceType   , '') = '', 'InsuranceType'   , null)
                  ,IF(IFNULL(policy.PolicyNumber    , '') = '', 'PolicyNumber'    , null)
                  ,IF(IFNULL(policy.RelationshipCode, '') = '', 'RelationshipCode', null)
                  ,IF(tbl_insurancecompany.ID IS NULL, 'InsuranceCompanyID', null)
                  ,IF(tbl_insurancecompany.MIR != '' , 'InsuranceCompany'  , null)
                  )
        ,'')
  WHERE (policy.CustomerID = P_CustomerID) OR (P_CustomerID IS NULL); --
END