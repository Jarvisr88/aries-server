CREATE DEFINER=`root`@`localhost` PROCEDURE `InvoiceDetails_RecalculateInternals_Single`(P_InvoiceID INT, P_InvoiceDetailsID INT)
BEGIN
  DECLARE done INT DEFAULT 0; --
  DECLARE
    V_PrevCustomerID,
    V_PrevInvoiceID,
    V_PrevDetailsID,
    cur_CustomerID,
    cur_InvoiceID,
    cur_DetailsID,
    cur_TranID INT; --
  -- cursor variables
  DECLARE
    cur_CustomerInsuranceID_1,
    cur_CustomerInsuranceID_2,
    cur_CustomerInsuranceID_3,
    cur_CustomerInsuranceID_4,
    cur_InsuranceCompanyID_1,
    cur_InsuranceCompanyID_2,
    cur_InsuranceCompanyID_3,
    cur_InsuranceCompanyID_4 INT; --
  DECLARE
    V_CustomerInsuranceID_1,
    V_CustomerInsuranceID_2,
    V_CustomerInsuranceID_3,
    V_CustomerInsuranceID_4,
    V_InsuranceCompanyID_1,
    V_InsuranceCompanyID_2,
    V_InsuranceCompanyID_3,
    V_InsuranceCompanyID_4 INT; --
  DECLARE
    cur_TranAmount,
    V_PaymentAmount_Insco_1,
    V_PaymentAmount_Insco_2,
    V_PaymentAmount_Insco_3,
    V_PaymentAmount_Insco_4,
    V_PaymentAmount_Patient,
    V_PaymentAmount,
    V_WriteoffAmount,
    V_DeductibleAmount decimal(18,2); --
  DECLARE
    cur_Percent int; --
  DECLARE
    cur_Basis VARCHAR(7); --
  DECLARE
    cur_TranType VARCHAR(50); --
  DECLARE
    cur_TranOwner,
    cur_Insurances,
    V_ProposedPayer, -- modified by 'Change Current Payee' transaction
    V_CurrentPayer,  -- used only to simplify evaluations
    V_Insurances,    -- insurances available for current line
    V_Pendings,
    V_Submits,
    V_ZeroPayments tinyint; --
  DECLARE
    cur_TranDate,
    V_SubmitDate_1,
    V_SubmitDate_2,
    V_SubmitDate_3,
    V_SubmitDate_4,
    V_SubmitDate_P DATE; --

  DECLARE F_Insco_1 tinyint DEFAULT 01; --
  DECLARE F_Insco_2 tinyint DEFAULT 02; --
  DECLARE F_Insco_3 tinyint DEFAULT 04; --
  DECLARE F_Insco_4 tinyint DEFAULT 08; --
  DECLARE F_Patient tinyint DEFAULT 16; --

  DECLARE cur CURSOR FOR
    SELECT
      `detail`.CustomerID,
      `detail`.InvoiceID,
      `detail`.ID as InvoiceDetailsID,
      `tran`.`ID` as TranID,
      `trantype`.`Name` as TranType,
      `tran`.`Amount` as TranAmount,
      `tran`.`TransactionDate` as TranDate,
      CASE WHEN `tran`.CustomerInsuranceID = `invoice`.CustomerInsurance1_ID THEN F_Insco_1
           WHEN `tran`.CustomerInsuranceID = `invoice`.CustomerInsurance2_ID THEN F_Insco_2
           WHEN `tran`.CustomerInsuranceID = `invoice`.CustomerInsurance3_ID THEN F_Insco_3
           WHEN `tran`.CustomerInsuranceID = `invoice`.CustomerInsurance4_ID THEN F_Insco_4
           WHEN `tran`.CustomerInsuranceID IS NULL                           THEN F_Patient
           ELSE 0 END AS TranOwner,
      IF((`insurance1`.ID IS NOT NULL) AND (`detail`.BillIns1 = 1) AND (`detail`.NopayIns1 = 0), F_Insco_1, 0) +
      IF((`insurance2`.ID IS NOT NULL) AND (`detail`.BillIns2 = 1), F_Insco_2, 0) +
      IF((`insurance3`.ID IS NOT NULL) AND (`detail`.BillIns3 = 1), F_Insco_3, 0) +
      IF((`insurance4`.ID IS NOT NULL) AND (`detail`.BillIns4 = 1), F_Insco_4, 0) as Insurances,
      `insurance1`.ID as CustomerInsuranceID_1,
      `insurance2`.ID as CustomerInsuranceID_2,
      `insurance3`.ID as CustomerInsuranceID_3,
      `insurance4`.ID as CustomerInsuranceID_4,
      `insurance1`.InsuranceCompanyID as InsuranceCompanyID_1,
      `insurance2`.InsuranceCompanyID as InsuranceCompanyID_2,
      `insurance3`.InsuranceCompanyID as InsuranceCompanyID_3,
      `insurance4`.InsuranceCompanyID as InsuranceCompanyID_4,
       CASE WHEN IFNULL(`insurance1`.PaymentPercent, 0) < 000 THEN 000
            WHEN 100 < IFNULL(`insurance1`.PaymentPercent, 0) THEN 100
            ELSE IFNULL(`insurance1`.PaymentPercent, 0) END as Percent,
       IFNULL(`insurance1`.Basis, 'Bill') as Basis
    FROM tbl_invoicedetails as `detail`
         INNER JOIN tbl_invoice as `invoice` ON `invoice`.CustomerID = `detail`.CustomerID
                                            AND `invoice`.ID         = `detail`.InvoiceID
         LEFT JOIN `tbl_customer_insurance` as `insurance1` ON `insurance1`.ID         = `invoice`.CustomerInsurance1_ID
                                                           AND `insurance1`.CustomerID = `invoice`.CustomerID
         LEFT JOIN `tbl_customer_insurance` as `insurance2` ON `insurance2`.ID         = `invoice`.CustomerInsurance2_ID
                                                           AND `insurance2`.CustomerID = `invoice`.CustomerID
         LEFT JOIN `tbl_customer_insurance` as `insurance3` ON `insurance3`.ID         = `invoice`.CustomerInsurance3_ID
                                                           AND `insurance3`.CustomerID = `invoice`.CustomerID
         LEFT JOIN `tbl_customer_insurance` as `insurance4` ON `insurance4`.ID         = `invoice`.CustomerInsurance4_ID
                                                           AND `insurance4`.CustomerID = `invoice`.CustomerID
         LEFT JOIN tbl_invoice_transaction as `tran` ON `tran`.InvoiceDetailsID = `detail`.ID
                                                    AND `tran`.InvoiceID        = `detail`.InvoiceID
                                                    AND `tran`.CustomerID       = `detail`.CustomerID
         LEFT JOIN tbl_invoice_transactiontype as `trantype` ON `trantype`.ID = `tran`.TransactionTypeID
  WHERE ((P_InvoiceID        IS NULL) OR (`invoice`.ID = P_InvoiceID       ))
    AND ((P_InvoiceDetailsID IS NULL) OR (`detail`.ID  = P_InvoiceDetailsID))
  ORDER BY `detail`.CustomerID, `detail`.InvoiceID, `detail`.ID, `tran`.`ID`; --

  DECLARE CONTINUE HANDLER FOR SQLSTATE '02000' SET done = 1; --

  SET V_PrevCustomerID = null; --
  SET V_PrevInvoiceID  = null; --
  SET V_PrevDetailsID  = null; --

  OPEN cur; --

  REPEAT
    FETCH cur INTO
      cur_CustomerID,
      cur_InvoiceID,
      cur_DetailsID,
      cur_TranID,
      cur_TranType,
      cur_TranAmount,
      cur_TranDate,
      cur_TranOwner,
      cur_Insurances,
      cur_CustomerInsuranceID_1,
      cur_CustomerInsuranceID_2,
      cur_CustomerInsuranceID_3,
      cur_CustomerInsuranceID_4,
      cur_InsuranceCompanyID_1,
      cur_InsuranceCompanyID_2,
      cur_InsuranceCompanyID_3,
      cur_InsuranceCompanyID_4,
      cur_Percent,
      cur_Basis; --

    IF (done != 0)
    OR (V_PrevCustomerID IS NULL) OR (cur_CustomerID != V_PrevCustomerID)
    OR (V_PrevInvoiceID  IS NULL) OR (cur_InvoiceID  != V_PrevInvoiceID)
    OR (V_PrevDetailsID  IS NULL) OR (cur_DetailsID  != V_PrevDetailsID)
    THEN
      IF  (V_PrevCustomerID IS NOT NULL)
      AND (V_PrevInvoiceID  IS NOT NULL)
      AND (V_PrevDetailsID  IS NOT NULL)
      THEN
        -- we must allow changing payer regardless of the payments (zero payments and total amount paid)
        SET V_CurrentPayer
          = CASE WHEN (V_ProposedPayer = F_Insco_1) THEN F_Insco_1
                 WHEN (V_ProposedPayer = F_Insco_2) THEN F_Insco_2
                 WHEN (V_ProposedPayer = F_Insco_3) THEN F_Insco_3
                 WHEN (V_ProposedPayer = F_Insco_4) THEN F_Insco_4
                 WHEN (V_ProposedPayer = F_Patient) THEN F_Patient
                 WHEN (V_Insurances & F_Insco_1 != 0) AND (V_PaymentAmount_Insco_1 < 0.01) AND (V_ZeroPayments & F_Insco_1 = 0) THEN F_Insco_1
                 WHEN (V_Insurances & F_Insco_2 != 0) AND (V_PaymentAmount_Insco_2 < 0.01) AND (V_ZeroPayments & F_Insco_2 = 0) THEN F_Insco_2
                 WHEN (V_Insurances & F_Insco_3 != 0) AND (V_PaymentAmount_Insco_3 < 0.01) AND (V_ZeroPayments & F_Insco_3 = 0) THEN F_Insco_3
                 WHEN (V_Insurances & F_Insco_4 != 0) AND (V_PaymentAmount_Insco_4 < 0.01) AND (V_ZeroPayments & F_Insco_4 = 0) THEN F_Insco_4
                 ELSE F_Patient END; -- we should never switch from patient - somebody must pay --

        -- save into db
        UPDATE tbl_invoicedetails
        SET Balance = BillableAmount - V_PaymentAmount - V_WriteoffAmount,
            PaymentAmount  = V_PaymentAmount,
            WriteoffAmount = V_WriteoffAmount,
            DeductibleAmount = V_DeductibleAmount,
            CurrentPayer
              = CASE WHEN BillableAmount - V_PaymentAmount - V_WriteoffAmount < 0.01 THEN 'None'
                     WHEN V_CurrentPayer = F_Insco_1 THEN 'Ins1'
                     WHEN V_CurrentPayer = F_Insco_2 THEN 'Ins2'
                     WHEN V_CurrentPayer = F_Insco_3 THEN 'Ins3'
                     WHEN V_CurrentPayer = F_Insco_4 THEN 'Ins4'
                     WHEN V_CurrentPayer = F_Patient THEN 'Patient'
                     ELSE 'None' END,
            SubmittedDate
              = CASE WHEN BillableAmount - V_PaymentAmount - V_WriteoffAmount < 0.01 THEN null
                     WHEN V_CurrentPayer = F_Insco_1 THEN V_SubmitDate_1
                     WHEN V_CurrentPayer = F_Insco_2 THEN V_SubmitDate_2
                     WHEN V_CurrentPayer = F_Insco_3 THEN V_SubmitDate_3
                     WHEN V_CurrentPayer = F_Insco_4 THEN V_SubmitDate_4
                     WHEN V_CurrentPayer = F_Patient THEN V_SubmitDate_P
                     ELSE null END,
            Submitted
              = CASE WHEN BillableAmount - V_PaymentAmount - V_WriteoffAmount < 0.01 THEN 1
                     WHEN V_CurrentPayer = F_Insco_1 THEN IF(V_SubmitDate_1 IS NOT NULL, 1, 0)
                     WHEN V_CurrentPayer = F_Insco_2 THEN IF(V_SubmitDate_2 IS NOT NULL, 1, 0)
                     WHEN V_CurrentPayer = F_Insco_3 THEN IF(V_SubmitDate_3 IS NOT NULL, 1, 0)
                     WHEN V_CurrentPayer = F_Insco_4 THEN IF(V_SubmitDate_4 IS NOT NULL, 1, 0)
                     WHEN V_CurrentPayer = F_Patient THEN IF(V_SubmitDate_P IS NOT NULL, 1, 0)
                     ELSE 1 END,
            CurrentInsuranceCompanyID
              = CASE WHEN BillableAmount - V_PaymentAmount - V_WriteoffAmount < 0.01 THEN null
                     WHEN V_CurrentPayer = F_Insco_1 THEN V_InsuranceCompanyID_1
                     WHEN V_CurrentPayer = F_Insco_2 THEN V_InsuranceCompanyID_2
                     WHEN V_CurrentPayer = F_Insco_3 THEN V_InsuranceCompanyID_3
                     WHEN V_CurrentPayer = F_Insco_4 THEN V_InsuranceCompanyID_4
                     WHEN V_CurrentPayer = F_Patient THEN null
                     ELSE null END,
            CurrentCustomerInsuranceID
              = CASE WHEN BillableAmount - V_PaymentAmount - V_WriteoffAmount < 0.01 THEN null
                     WHEN V_CurrentPayer = F_Insco_1 THEN V_CustomerInsuranceID_1
                     WHEN V_CurrentPayer = F_Insco_2 THEN V_CustomerInsuranceID_2
                     WHEN V_CurrentPayer = F_Insco_3 THEN V_CustomerInsuranceID_3
                     WHEN V_CurrentPayer = F_Insco_4 THEN V_CustomerInsuranceID_4
                     WHEN V_CurrentPayer = F_Patient THEN null
                     ELSE null END,
            -- for debugging
            Pendings    = V_Pendings,
            Submits     = V_Submits,
            Payments
              = CASE WHEN 0.01 <= V_PaymentAmount_Insco_1 OR V_ZeroPayments & F_Insco_1 != 0 THEN F_Insco_1 ELSE 0 END
              + CASE WHEN 0.01 <= V_PaymentAmount_Insco_2 OR V_ZeroPayments & F_Insco_2 != 0 THEN F_Insco_2 ELSE 0 END
              + CASE WHEN 0.01 <= V_PaymentAmount_Insco_3 OR V_ZeroPayments & F_Insco_3 != 0 THEN F_Insco_3 ELSE 0 END
              + CASE WHEN 0.01 <= V_PaymentAmount_Insco_4 OR V_ZeroPayments & F_Insco_4 != 0 THEN F_Insco_4 ELSE 0 END
              + CASE WHEN 0.01 <= V_PaymentAmount_Patient THEN F_Patient ELSE 0 END
        WHERE (CustomerID = V_PrevCustomerID) AND (InvoiceID = V_PrevInvoiceID) AND (ID = V_PrevDetailsID); --
      END IF; --

      -- init / reinit
      SET V_PrevCustomerID = cur_CustomerID; --
      SET V_PrevInvoiceID  = cur_InvoiceID; --
      SET V_PrevDetailsID  = cur_DetailsID; --

      SET V_PaymentAmount_Insco_1 = 0.0; --
      SET V_PaymentAmount_Insco_2 = 0.0; --
      SET V_PaymentAmount_Insco_3 = 0.0; --
      SET V_PaymentAmount_Insco_4 = 0.0; --
      SET V_PaymentAmount_Patient = 0.0; --
      SET V_PaymentAmount  = 0.0; --
      SET V_WriteoffAmount = 0.0; --
      SET V_DeductibleAmount = 0.0; --
      SET V_ProposedPayer = null; --
      SET V_Insurances = cur_Insurances; -- snapshot of insurances available for current line
      SET V_Pendings = 0; --
      SET V_Submits  = 0; --
      SET V_ZeroPayments = 0; --
      SET V_SubmitDate_1 = null; --
      SET V_SubmitDate_2 = null; --
      SET V_SubmitDate_3 = null; --
      SET V_SubmitDate_4 = null; --
      SET V_SubmitDate_P = null; --
      SET V_InsuranceCompanyID_1 = cur_InsuranceCompanyID_1; --
      SET V_InsuranceCompanyID_2 = cur_InsuranceCompanyID_2; --
      SET V_InsuranceCompanyID_3 = cur_InsuranceCompanyID_3; --
      SET V_InsuranceCompanyID_4 = cur_InsuranceCompanyID_4; --
      SET V_CustomerInsuranceID_1 = cur_CustomerInsuranceID_1; --
      SET V_CustomerInsuranceID_2 = cur_CustomerInsuranceID_2; --
      SET V_CustomerInsuranceID_3 = cur_CustomerInsuranceID_3; --
      SET V_CustomerInsuranceID_4 = cur_CustomerInsuranceID_4; --
    END IF; --

    IF (done = 0)
    AND (cur_TranID IS NOT NULL)
    THEN
      -- Only 'Payment' and 'Change Current Payee' changes current payer
      IF (cur_TranType = 'Contractual Writeoff') OR (cur_TranType = 'Writeoff') THEN
        SET V_WriteoffAmount = V_WriteoffAmount + IFNULL(cur_TranAmount, 0); --

      ELSEIF (cur_TranType = 'Submit') OR (cur_TranType = 'Auto Submit') THEN
        SET V_Submits = V_Submits | cur_TranOwner; --
        IF     (cur_TranOwner = F_Insco_1) THEN
          SET V_SubmitDate_1 = cur_TranDate; --
        ELSEIF (cur_TranOwner = F_Insco_2) THEN
          SET V_SubmitDate_2 = cur_TranDate; --
        ELSEIF (cur_TranOwner = F_Insco_3) THEN
          SET V_SubmitDate_3 = cur_TranDate; --
        ELSEIF (cur_TranOwner = F_Insco_4) THEN
          SET V_SubmitDate_4 = cur_TranDate; --
        ELSEIF (cur_TranOwner = F_Patient) THEN
          SET V_SubmitDate_P = cur_TranDate; --
        END IF; --

      ELSEIF (cur_TranType = 'Voided Submission') THEN
        SET V_Submits = V_Submits & ~cur_TranOwner; --
        IF     (cur_TranOwner = F_Insco_1) THEN
          SET V_SubmitDate_1 = null; --
        ELSEIF (cur_TranOwner = F_Insco_2) THEN
          SET V_SubmitDate_2 = null; --
        ELSEIF (cur_TranOwner = F_Insco_3) THEN
          SET V_SubmitDate_3 = null; --
        ELSEIF (cur_TranOwner = F_Insco_4) THEN
          SET V_SubmitDate_4 = null; --
        ELSEIF (cur_TranOwner = F_Patient) THEN
          SET V_SubmitDate_P = null; --
        END IF; --

      ELSEIF (cur_TranType = 'Pending Submission') THEN
        SET V_Pendings = V_Pendings | cur_TranOwner; --

      ELSEIF (cur_TranType = 'Change Current Payee') THEN
        IF (cur_TranOwner = F_Insco_1 and V_Insurances & F_Insco_1 != 0)
        OR (cur_TranOwner = F_Insco_2 and V_Insurances & F_Insco_2 != 0)
        OR (cur_TranOwner = F_Insco_3 and V_Insurances & F_Insco_3 != 0)
        OR (cur_TranOwner = F_Insco_4 and V_Insurances & F_Insco_4 != 0)
        OR (cur_TranOwner = F_Patient)
        THEN
          -- "Change Current Payee" transaction changes responsibility unconditionally
          SET V_ProposedPayer = cur_TranOwner; --
        END IF; --

      ELSEIF (cur_TranType = 'Payment') THEN
        IF (ABS(cur_TranAmount) < 0.01) THEN
          SET V_ZeroPayments = V_ZeroPayments | cur_TranOwner; --
        ELSE
          SET V_ZeroPayments = V_ZeroPayments & ~cur_TranOwner; --
        END IF; --

        IF (cur_TranOwner = F_Insco_1) THEN
          SET V_PaymentAmount_Insco_1 = V_PaymentAmount_Insco_1 + cur_TranAmount; --
        ELSEIF (cur_TranOwner = F_Insco_2) THEN
          SET V_PaymentAmount_Insco_2 = V_PaymentAmount_Insco_2 + cur_TranAmount; --
        ELSEIF (cur_TranOwner = F_Insco_3) THEN
          SET V_PaymentAmount_Insco_3 = V_PaymentAmount_Insco_3 + cur_TranAmount; --
        ELSEIF (cur_TranOwner = F_Insco_4) THEN
          SET V_PaymentAmount_Insco_4 = V_PaymentAmount_Insco_4 + cur_TranAmount; --
        ELSEIF (cur_TranOwner = F_Patient) THEN
          SET V_PaymentAmount_Patient = V_PaymentAmount_Patient + cur_TranAmount; --
        END IF; --

        SET V_PaymentAmount = V_PaymentAmount + cur_TranAmount; --

        IF (cur_TranOwner = V_ProposedPayer)
        AND (0.00 <= cur_TranAmount) THEN
          -- "Payment" transaction (with positive or zero amount) advances responsibility to next payer
          SET V_ProposedPayer = null; --
        END IF; --

      ELSEIF (cur_TranType = 'Deductible') THEN
        -- I guess we should use deductible amount of first insurance only
        IF (cur_TranOwner = F_Insco_1) THEN
          SET V_DeductibleAmount = IFNULL(cur_TranAmount, 0.0); --
        END IF; --

      END IF; --
    END IF; --
  UNTIL done END REPEAT; --

  CLOSE cur; --
END