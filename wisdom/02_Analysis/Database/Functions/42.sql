CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_customer`(P_CustomerID INT)
BEGIN
  UPDATE tbl_customer
         LEFT JOIN tbl_doctor ON tbl_customer.Doctor1_ID = tbl_doctor.ID
  SET tbl_customer.`MIR` =
      IF(tbl_customer.CommercialAccount = 0
        ,CONCAT_WS(','
                  ,IF(IFNULL(tbl_customer.AccountNumber   , '') = '', 'AccountNumber'   , null)
                  ,IF(IFNULL(tbl_customer.FirstName       , '') = '', 'FirstName'       , null)
                  ,IF(IFNULL(tbl_customer.LastName        , '') = '', 'LastName'        , null)
                  ,IF(IFNULL(tbl_customer.Address1        , '') = '', 'Address1'        , null)
                  ,IF(IFNULL(tbl_customer.City            , '') = '', 'City'            , null)
                  ,IF(IFNULL(tbl_customer.State           , '') = '', 'State'           , null)
                  ,IF(IFNULL(tbl_customer.Zip             , '') = '', 'Zip'             , null)
                  ,IF(IFNULL(tbl_customer.EmploymentStatus, '') = '', 'EmploymentStatus', null)
                  ,IF(IFNULL(tbl_customer.Gender          , '') = '', 'Gender'          , null)
                  ,IF(IFNULL(tbl_customer.MaritalStatus   , '') = '', 'MaritalStatus'   , null)
                  ,IF(IFNULL(tbl_customer.MilitaryBranch  , '') = '', 'MilitaryBranch'  , null)
                  ,IF(IFNULL(tbl_customer.MilitaryStatus  , '') = '', 'MilitaryStatus'  , null)
                  ,IF(IFNULL(tbl_customer.StudentStatus   , '') = '', 'StudentStatus'   , null)
                  ,IF(IFNULL(tbl_customer.MonthsValid     ,  0) =  0, 'MonthsValid'     , null)
                  ,IF(tbl_customer.DateofBirth     IS NULL, 'DateofBirth'    , null)
                  ,IF(tbl_customer.SignatureOnFile IS NULL, 'SignatureOnFile', null)
                  ,IF(tbl_doctor.ID IS NULL, 'Doctor1_ID', null)
                  ,IF(tbl_doctor.MIR != '' , 'Doctor1'   , null)
                  )
        ,'')
  WHERE (tbl_customer.ID = P_CustomerID) OR (P_CustomerID IS NULL); --
END