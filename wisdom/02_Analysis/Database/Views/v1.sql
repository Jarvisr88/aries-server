CREATE ALGORITHM=MERGE DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `c01`.`view_invoicetransaction_statistics` AS select sql_small_result `detail`.`CustomerID` AS `CustomerID`,`detail`.`OrderID` AS `OrderID`,`detail`.`InvoiceID` AS `InvoiceID`,`detail`.`ID` AS `InvoiceDetailsID`,`detail`.`BillableAmount` AS `BillableAmount`,`detail`.`AllowableAmount` AS `AllowableAmount`,`detail`.`Quantity` AS `Quantity`,`detail`.`Hardship` AS `Hardship`,`detail`.`BillingCode` AS `BillingCode`,`detail`.`InventoryItemID` AS `InventoryItemID`,`detail`.`DOSFrom` AS `DOSFrom`,`detail`.`DOSTo` AS `DOSTo`,`insurance1`.`ID` AS `Insurance1_ID`,`insurance2`.`ID` AS `Insurance2_ID`,`insurance3`.`ID` AS `Insurance3_ID`,`insurance4`.`ID` AS `Insurance4_ID`,`insurance1`.`InsuranceCompanyID` AS `InsuranceCompany1_ID`,`insurance2`.`InsuranceCompanyID` AS `InsuranceCompany2_ID`,`insurance3`.`InsuranceCompanyID` AS `InsuranceCompany3_ID`,`insurance4`.`InsuranceCompanyID` AS `InsuranceCompany4_ID`,(case when (ifnull(`insurance1`.`PaymentPercent`,0) < 0) then 0 when (100 < ifnull(`insurance1`.`PaymentPercent`,0)) then 100 else ifnull(`insurance1`.`PaymentPercent`,0) end) AS `Percent`,ifnull(`insurance1`.`Basis`,'Bill') AS `Basis`,`detail`.`PaymentAmount` AS `PaymentAmount`,`detail`.`WriteoffAmount` AS `WriteoffAmount`,((((if((`insurance1`.`ID` is not null),1,0) + if((`insurance2`.`ID` is not null),2,0)) + if((`insurance3`.`ID` is not null),4,0)) + if((`insurance4`.`ID` is not null),8,0)) + if((1 = 1),16,0)) AS `Insurances`,((((if((`insurance1`.`ID` is not null),(`detail`.`Pendings` & 1),0) + if((`insurance2`.`ID` is not null),(`detail`.`Pendings` & 2),0)) + if((`insurance3`.`ID` is not null),(`detail`.`Pendings` & 4),0)) + if((`insurance4`.`ID` is not null),(`detail`.`Pendings` & 8),0)) + if((1 = 1),(`detail`.`Pendings` & 16),0)) AS `PendingSubmissions`,((((if((`insurance1`.`ID` is not null),(`detail`.`Submits` & 1),0) + if((`insurance2`.`ID` is not null),(`detail`.`Submits` & 2),0)) + if((`insurance3`.`ID` is not null),(`detail`.`Submits` & 4),0)) + if((`insurance4`.`ID` is not null),(`detail`.`Submits` & 8),0)) + if((1 = 1),(`detail`.`Submits` & 16),0)) AS `Submits`,((((if((`insurance1`.`ID` is not null),(`detail`.`Payments` & 1),0) + if((`insurance2`.`ID` is not null),(`detail`.`Payments` & 2),0)) + if((`insurance3`.`ID` is not null),(`detail`.`Payments` & 4),0)) + if((`insurance4`.`ID` is not null),(`detail`.`Payments` & 8),0)) + if((1 = 1),(`detail`.`Payments` & 16),0)) AS `Payments`,`detail`.`CurrentCustomerInsuranceID` AS `CurrentInsuranceID`,`detail`.`CurrentInsuranceCompanyID` AS `CurrentInsuranceCompanyID`,`detail`.`Submitted` AS `InvoiceSubmitted`,`detail`.`SubmittedDate` AS `SubmittedDate`,`detail`.`CurrentPayer` AS `CurrentPayer`,`detail`.`NopayIns1` AS `NopayIns1` from (((((`c01`.`tbl_invoicedetails` `detail` join `c01`.`tbl_invoice` `invoice` on(((`invoice`.`CustomerID` = `detail`.`CustomerID`) and (`invoice`.`ID` = `detail`.`InvoiceID`)))) left join `c01`.`tbl_customer_insurance` `insurance1` on(((`insurance1`.`ID` = `invoice`.`CustomerInsurance1_ID`) and (`insurance1`.`CustomerID` = `invoice`.`CustomerID`) and (`detail`.`BillIns1` = 1)))) left join `c01`.`tbl_customer_insurance` `insurance2` on(((`insurance2`.`ID` = `invoice`.`CustomerInsurance2_ID`) and (`insurance2`.`CustomerID` = `invoice`.`CustomerID`) and (`detail`.`BillIns2` = 1)))) left join `c01`.`tbl_customer_insurance` `insurance3` on(((`insurance3`.`ID` = `invoice`.`CustomerInsurance3_ID`) and (`insurance3`.`CustomerID` = `invoice`.`CustomerID`) and (`detail`.`BillIns3` = 1)))) left join `c01`.`tbl_customer_insurance` `insurance4` on(((`insurance4`.`ID` = `invoice`.`CustomerInsurance4_ID`) and (`insurance4`.`CustomerID` = `invoice`.`CustomerID`) and (`detail`.`BillIns4` = 1))))