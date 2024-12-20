CREATE ALGORITHM=MERGE DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `c01`.`tbl_insurancecompany` AS select `dmeworks`.`tbl_insurancecompany`.`Address1` AS `Address1`,`dmeworks`.`tbl_insurancecompany`.`Address2` AS `Address2`,`dmeworks`.`tbl_insurancecompany`.`Basis` AS `Basis`,`dmeworks`.`tbl_insurancecompany`.`City` AS `City`,`dmeworks`.`tbl_insurancecompany`.`Contact` AS `Contact`,`dmeworks`.`tbl_insurancecompany`.`ECSFormat` AS `ECSFormat`,`dmeworks`.`tbl_insurancecompany`.`ExpectedPercent` AS `ExpectedPercent`,`dmeworks`.`tbl_insurancecompany`.`Fax` AS `Fax`,`dmeworks`.`tbl_insurancecompany`.`ID` AS `ID`,`dmeworks`.`tbl_insurancecompany`.`Name` AS `Name`,`dmeworks`.`tbl_insurancecompany`.`Phone` AS `Phone`,`dmeworks`.`tbl_insurancecompany`.`Phone2` AS `Phone2`,`dmeworks`.`tbl_insurancecompany`.`PriceCodeID` AS `PriceCodeID`,`dmeworks`.`tbl_insurancecompany`.`PrintHAOOnInvoice` AS `PrintHAOOnInvoice`,`dmeworks`.`tbl_insurancecompany`.`PrintInvOnInvoice` AS `PrintInvOnInvoice`,`dmeworks`.`tbl_insurancecompany`.`State` AS `State`,`dmeworks`.`tbl_insurancecompany`.`Title` AS `Title`,`dmeworks`.`tbl_insurancecompany`.`Type` AS `Type`,`dmeworks`.`tbl_insurancecompany`.`Zip` AS `Zip`,`dmeworks`.`tbl_insurancecompany`.`MedicareNumber` AS `MedicareNumber`,`dmeworks`.`tbl_insurancecompany`.`OfficeAllyNumber` AS `OfficeAllyNumber`,`dmeworks`.`tbl_insurancecompany`.`ZirmedNumber` AS `ZirmedNumber`,`dmeworks`.`tbl_insurancecompany`.`LastUpdateUserID` AS `LastUpdateUserID`,`dmeworks`.`tbl_insurancecompany`.`LastUpdateDatetime` AS `LastUpdateDatetime`,`dmeworks`.`tbl_insurancecompany`.`InvoiceFormID` AS `InvoiceFormID`,`dmeworks`.`tbl_insurancecompany`.`MedicaidNumber` AS `MedicaidNumber`,`dmeworks`.`tbl_insurancecompany`.`MIR` AS `MIR`,`dmeworks`.`tbl_insurancecompany`.`GroupID` AS `GroupID`,`dmeworks`.`tbl_insurancecompany`.`AvailityNumber` AS `AvailityNumber`,`dmeworks`.`tbl_insurancecompany`.`AbilityNumber` AS `AbilityNumber`,`dmeworks`.`tbl_insurancecompany`.`AbilityEligibilityPayerId` AS `AbilityEligibilityPayerId` from `dmeworks`.`tbl_insurancecompany`