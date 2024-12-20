CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_facility`(P_FacilityID INT)
BEGIN
  UPDATE tbl_facility
  SET `MIR` =
      CONCAT_WS(',',
          IF(IFNULL(Name      , '') = '', 'Name'      , null),
          IF(IFNULL(Address1  , '') = '', 'Address1'  , null),
          IF(IFNULL(City      , '') = '', 'City'      , null),
          IF(IFNULL(State     , '') = '', 'State'     , null),
          IF(IFNULL(Zip       , '') = '', 'Zip'       , null),
          IF(IFNULL(POSTypeID , '') = '', 'POSTypeID' , null),
          IF(NPI REGEXP '[[:digit:]]{10}[[:blank:]]*', null, 'NPI')
               )
  WHERE (ID = P_FacilityID) OR (P_FacilityID IS NULL); --
END