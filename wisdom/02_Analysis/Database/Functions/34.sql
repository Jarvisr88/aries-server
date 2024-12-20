CREATE DEFINER=`root`@`localhost` PROCEDURE `mir_update_cmnform`(P_CMNFormID INT)
BEGIN
  UPDATE tbl_cmnform
         LEFT JOIN tbl_customer as tbl_customer ON tbl_cmnform.CustomerID = tbl_customer.ID
         LEFT JOIN tbl_doctor   as tbl_doctor   ON tbl_cmnform.DoctorID   = tbl_doctor  .ID
         LEFT JOIN tbl_facility as tbl_facility ON tbl_cmnform.FacilityID = tbl_facility.ID
  SET tbl_cmnform.`MIR` =
      CONCAT_WS(',',
          IF(IFNULL(tbl_cmnform.CMNType              , '') = '', 'CMNType'              , null),
          IF(IFNULL(tbl_cmnform.Signature_Name       , '') = '', 'Signature_Name'       , null),
          IF(tbl_cmnform.InitialDate    is null, 'InitialDate'   , null),
          IF(tbl_cmnform.POSTypeID      is null, 'POSTypeID'     , null),
          IF(tbl_cmnform.Signature_Date is null, 'Signature_Date', null),
          CASE WHEN tbl_cmnform.EstimatedLengthOfNeed is null THEN 'EstimatedLengthOfNeed'
               WHEN tbl_cmnform.EstimatedLengthOfNeed <= 0    THEN 'EstimatedLengthOfNeed'
               ELSE null END,
          IF(tbl_customer.ID IS NULL, 'CustomerID', null),
          IF(tbl_customer.MIR != '' , 'Customer'  , null),
          IF(tbl_doctor  .ID IS NULL, 'DoctorID'  , null),
          IF(tbl_doctor  .MIR != '' , 'Doctor'    , null))
  WHERE (tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_icd9 as icd_1 ON tbl_cmnform.Customer_ICD9_1 = icd_1.Code
         LEFT JOIN tbl_icd9 as icd_2 ON tbl_cmnform.Customer_ICD9_2 = icd_2.Code
         LEFT JOIN tbl_icd9 as icd_3 ON tbl_cmnform.Customer_ICD9_3 = icd_3.Code
         LEFT JOIN tbl_icd9 as icd_4 ON tbl_cmnform.Customer_ICD9_4 = icd_4.Code
  SET tbl_cmnform.`MIR` =
      CONCAT_WS(',',
          tbl_cmnform.`MIR`,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_1, '') = ''  THEN 'ICD9_1.Required'
               WHEN icd_1.Code is null                            THEN 'ICD9_1.Unknown'
               WHEN icd_1.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_1.Inactive'
               ELSE null END,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_2, '') = ''  THEN null
               WHEN icd_2.Code is null                            THEN 'ICD9_2.Unknown'
               WHEN icd_2.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_2.Inactive'
               ELSE null END,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_3, '') = ''  THEN null
               WHEN icd_3.Code is null                            THEN 'ICD9_3.Unknown'
               WHEN icd_3.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_3.Inactive'
               ELSE null END,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_4, '') = ''  THEN null
               WHEN icd_4.Code is null                            THEN 'ICD9_4.Unknown'
               WHEN icd_4.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_4.Inactive'
               ELSE null END)
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.Customer_UsingICD10 != 1 OR tbl_cmnform.Customer_UsingICD10 IS NULL); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_icd10 as icd_1 ON tbl_cmnform.Customer_ICD9_1 = icd_1.Code
         LEFT JOIN tbl_icd10 as icd_2 ON tbl_cmnform.Customer_ICD9_2 = icd_2.Code
         LEFT JOIN tbl_icd10 as icd_3 ON tbl_cmnform.Customer_ICD9_3 = icd_3.Code
         LEFT JOIN tbl_icd10 as icd_4 ON tbl_cmnform.Customer_ICD9_4 = icd_4.Code
  SET tbl_cmnform.`MIR` =
      CONCAT_WS(',',
          tbl_cmnform.`MIR`,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_1, '') = ''  THEN 'ICD9_1.Required'
               WHEN icd_1.Code is null                            THEN 'ICD9_1.Unknown'
               WHEN icd_1.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_1.Inactive'
               ELSE null END,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_2, '') = ''  THEN null
               WHEN icd_2.Code is null                            THEN 'ICD9_2.Unknown'
               WHEN icd_2.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_2.Inactive'
               ELSE null END,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_3, '') = ''  THEN null
               WHEN icd_3.Code is null                            THEN 'ICD9_3.Unknown'
               WHEN icd_3.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_3.Inactive'
               ELSE null END,
          CASE WHEN IFNULL(tbl_cmnform.Customer_ICD9_4, '') = ''  THEN null
               WHEN icd_4.Code is null                            THEN 'ICD9_4.Unknown'
               WHEN icd_4.InactiveDate <= tbl_cmnform.InitialDate THEN 'ICD9_4.Inactive'
               ELSE null END)
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.Customer_UsingICD10 = 1); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0102a ON tbl_cmnform.ID = tbl_cmnform_0102a.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 01.02A')
    AND (IFNULL(tbl_cmnform_0102a.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102a.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102a.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102a.Answer5, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102a.Answer6, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102a.Answer7, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0102b ON tbl_cmnform.ID = tbl_cmnform_0102b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 01.02B')
    AND (IFNULL(tbl_cmnform_0102b.Answer12, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer13, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer14, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer15, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer16, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer19, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer20, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0102b.Answer22, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0203a ON tbl_cmnform.ID = tbl_cmnform_0203a.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 02.03A')
    AND (IFNULL(tbl_cmnform_0203a.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203a.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203a.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203a.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203a.Answer6, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203a.Answer7, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0203b ON tbl_cmnform.ID = tbl_cmnform_0203b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 02.03B')
    AND (IFNULL(tbl_cmnform_0203b.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203b.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203b.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203b.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203b.Answer8, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0203b.Answer9, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0302 ON tbl_cmnform.ID = tbl_cmnform_0302.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 03.02')
    AND (IFNULL(tbl_cmnform_0302.Answer14, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0403b ON tbl_cmnform.ID = tbl_cmnform_0403b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 04.03B')
    AND (IFNULL(tbl_cmnform_0403b.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403b.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403b.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403b.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403b.Answer5, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0403c ON tbl_cmnform.ID = tbl_cmnform_0403c.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 04.03C')
    AND (IFNULL(tbl_cmnform_0403c.Answer6a , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403c.Answer7a , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403c.Answer8  , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403c.Answer9a , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403c.Answer10a, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0403c.Answer11a, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0602b ON tbl_cmnform.ID = tbl_cmnform_0602b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 06.02B')
    AND (IFNULL(tbl_cmnform_0602b.Answer1 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0602b.Answer3 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0602b.Answer6 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0602b.Answer7 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0602b.Answer11, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0702a ON tbl_cmnform.ID = tbl_cmnform_0702a.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 07.02A')
    AND (IFNULL(tbl_cmnform_0702a.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702a.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702a.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702a.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702a.Answer5, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0702b ON tbl_cmnform.ID = tbl_cmnform_0702b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 07.02B')
    AND (IFNULL(tbl_cmnform_0702b.Answer6 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702b.Answer7 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702b.Answer8 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702b.Answer12, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702b.Answer13, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0702b.Answer14, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0902 ON tbl_cmnform.ID = tbl_cmnform_0902.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 09.02')
    AND (IFNULL(tbl_cmnform_0902.Answer7, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_1002a ON tbl_cmnform.ID = tbl_cmnform_1002a.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 10.02A')
    AND (IFNULL(tbl_cmnform_1002a.Answer1, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_1002b ON tbl_cmnform.ID = tbl_cmnform_1002b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 10.02B')
    AND (IFNULL(tbl_cmnform_1002b.Answer7 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_1002b.Answer8 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_1002b.Answer14, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_4842 ON tbl_cmnform.ID = tbl_cmnform_4842.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DMERC 484.2')
    AND (IFNULL(tbl_cmnform_4842.Answer2 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_4842.Answer5 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_4842.Answer8 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_4842.Answer9 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_4842.Answer10, '') != 'Y'); --

  -- new forms

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0404b ON tbl_cmnform.ID = tbl_cmnform_0404b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DME 04.04B')
    AND (IFNULL(tbl_cmnform_0404b.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404b.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404b.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404b.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404b.Answer5, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0404c ON tbl_cmnform.ID = tbl_cmnform_0404c.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DME 04.04C')
    AND (IFNULL(tbl_cmnform_0404c.Answer6  , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404c.Answer7a , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404c.Answer8  , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404c.Answer9a , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404c.Answer10a, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404c.Answer11 , '') != 'Y')
    AND (IFNULL(tbl_cmnform_0404c.Answer12 , '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0603b ON tbl_cmnform.ID = tbl_cmnform_0603b.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DME 06.03B')
    AND (IFNULL(tbl_cmnform_0603b.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0603b.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0603b.Answer5, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_0703a ON tbl_cmnform.ID = tbl_cmnform_0703a.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DME 07.03A')
    AND (IFNULL(tbl_cmnform_0703a.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0703a.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0703a.Answer3, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0703a.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_0703a.Answer5, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_1003 ON tbl_cmnform.ID = tbl_cmnform_1003.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DME 10.03')
    AND (IFNULL(tbl_cmnform_1003.Answer1, '') != 'Y')
    AND (IFNULL(tbl_cmnform_1003.Answer2, '') != 'Y')
    AND (IFNULL(tbl_cmnform_1003.Answer7, '') != 'Y'); --

  UPDATE tbl_cmnform
         LEFT JOIN tbl_cmnform_48403 ON tbl_cmnform.ID = tbl_cmnform_48403.CMNFormID
  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
    AND (tbl_cmnform.CMNType = 'DME 484.03')
    AND ((tbl_cmnform_48403.Answer1a is null) OR
         (tbl_cmnform_48403.Answer1b is null) OR
         (IFNULL(tbl_cmnform_48403.Answer1c, '0000-00-00') = '0000-00-00'))
    AND (IFNULL(tbl_cmnform_48403.Answer2, '')  = '')
    AND (IFNULL(tbl_cmnform_48403.Answer3, '')  = '')
    AND (IFNULL(tbl_cmnform_48403.Answer4, '') != 'Y')
    AND (IFNULL(tbl_cmnform_48403.Answer7, '') != 'Y')
    AND (IFNULL(tbl_cmnform_48403.Answer8, '') != 'Y')
    AND (IFNULL(tbl_cmnform_48403.Answer9, '') != 'Y'); --

--  `Answer1a` int(11) default NULL,
--  `Answer1b` int(11) default NULL,
--  `Answer1c` date default NULL,
--  `Answer2` enum('1','2','3') NOT NULL default '1',
--  `Answer3` enum('1','2','3') NOT NULL default '1',
--  `Answer4` enum('Y','N','D') NOT NULL default 'D',
--  `Answer5` varchar(10) default NULL,
--  `Answer6a` int(11) default NULL,
--  `Answer6b` int(11) default NULL,
--  `Answer6c` date default NULL,
--  `Answer7` enum('Y','N') NOT NULL default 'Y',
--  `Answer8` enum('Y','N') NOT NULL default 'Y',
--  `Answer9` enum('Y','N') NOT NULL default 'Y',

--  UPDATE tbl_cmnform
--         LEFT JOIN tbl_cmnform_drorder ON tbl_cmnform.ID = tbl_cmnform_drorder.CMNFormID
--  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
--  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
--    AND (tbl_cmnform.CMNType = 'DMERC DRORDER')
--    AND  (1 != 1); --

--  UPDATE tbl_cmnform
--         LEFT JOIN tbl_cmnform_uro ON tbl_cmnform.ID = tbl_cmnform_uro.CMNFormID
--  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
--  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
--    AND (tbl_cmnform.CMNType = 'DMERC URO')
--    AND  (1 != 1); --

--  UPDATE tbl_cmnform
--         LEFT JOIN tbl_cmnform_0903 ON tbl_cmnform.ID = tbl_cmnform_0903.CMNFormID
--  SET tbl_cmnform.MIR = CONCAT_WS(',', 'Answers', IF(tbl_cmnform.MIR != '', tbl_cmnform.MIR, null))
--  WHERE ((tbl_cmnform.ID = P_CMNFormID) OR (P_CMNFormID IS NULL))
--    AND (tbl_cmnform.CMNType = 'DME 09.03')
--    AND (1 != 1); --
END