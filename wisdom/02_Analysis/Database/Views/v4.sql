CREATE ALGORITHM=MERGE DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `c01`.`tbl_doctor` AS select `dmeworks`.`tbl_doctor`.`Address1` AS `Address1`,`dmeworks`.`tbl_doctor`.`Address2` AS `Address2`,`dmeworks`.`tbl_doctor`.`City` AS `City`,`dmeworks`.`tbl_doctor`.`Contact` AS `Contact`,`dmeworks`.`tbl_doctor`.`Courtesy` AS `Courtesy`,`dmeworks`.`tbl_doctor`.`Fax` AS `Fax`,`dmeworks`.`tbl_doctor`.`FirstName` AS `FirstName`,`dmeworks`.`tbl_doctor`.`ID` AS `ID`,`dmeworks`.`tbl_doctor`.`LastName` AS `LastName`,`dmeworks`.`tbl_doctor`.`LicenseNumber` AS `LicenseNumber`,`dmeworks`.`tbl_doctor`.`LicenseExpired` AS `LicenseExpired`,`dmeworks`.`tbl_doctor`.`MedicaidNumber` AS `MedicaidNumber`,`dmeworks`.`tbl_doctor`.`MiddleName` AS `MiddleName`,`dmeworks`.`tbl_doctor`.`OtherID` AS `OtherID`,`dmeworks`.`tbl_doctor`.`FEDTaxID` AS `FEDTaxID`,`dmeworks`.`tbl_doctor`.`DEANumber` AS `DEANumber`,`dmeworks`.`tbl_doctor`.`Phone` AS `Phone`,`dmeworks`.`tbl_doctor`.`Phone2` AS `Phone2`,`dmeworks`.`tbl_doctor`.`State` AS `State`,`dmeworks`.`tbl_doctor`.`Suffix` AS `Suffix`,`dmeworks`.`tbl_doctor`.`Title` AS `Title`,`dmeworks`.`tbl_doctor`.`TypeID` AS `TypeID`,`dmeworks`.`tbl_doctor`.`UPINNumber` AS `UPINNumber`,`dmeworks`.`tbl_doctor`.`Zip` AS `Zip`,`dmeworks`.`tbl_doctor`.`LastUpdateUserID` AS `LastUpdateUserID`,`dmeworks`.`tbl_doctor`.`LastUpdateDatetime` AS `LastUpdateDatetime`,`dmeworks`.`tbl_doctor`.`MIR` AS `MIR`,`dmeworks`.`tbl_doctor`.`NPI` AS `NPI`,`dmeworks`.`tbl_doctor`.`PecosEnrolled` AS `PecosEnrolled` from `dmeworks`.`tbl_doctor`