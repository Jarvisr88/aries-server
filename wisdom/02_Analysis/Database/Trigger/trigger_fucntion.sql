-- FUNCTION: c01.tbl_invoice_transaction_beforeinsert()

-- DROP FUNCTION IF EXISTS c01.tbl_invoice_transaction_beforeinsert();

CREATE OR REPLACE FUNCTION c01.tbl_invoice_transaction_beforeinsert()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
DECLARE
    V_OldValue NUMERIC(18, 2) := 0; 
    V_Quantity DOUBLE PRECISION := 0;
    V_TranType VARCHAR(50);
BEGIN
    -- Retrieve the Transaction Type
    SELECT Name
    INTO V_TranType
    FROM c01.tbl_invoice_transactiontype
    WHERE ID = NEW.TransactionTypeID;

    -- Handle different Transaction Types
    IF V_TranType = 'Adjust Allowable' THEN
        SELECT AllowableAmount, Quantity
        INTO V_OldValue, V_Quantity
        FROM c01.tbl_invoicedetails
        WHERE CustomerID = NEW.CustomerID
          AND InvoiceID = NEW.InvoiceID
          AND ID = NEW.InvoiceDetailsID;

        NEW.Quantity := V_Quantity;
        NEW.Comments := CONCAT('Previous Value=', V_OldValue);

        IF ABS(V_OldValue - NEW.Amount) > 0.001 THEN
            UPDATE c01.tbl_invoicedetails
            SET AllowableAmount = NEW.Amount
            WHERE CustomerID = NEW.CustomerID
              AND InvoiceID = NEW.InvoiceID
              AND ID = NEW.InvoiceDetailsID;
        END IF;

    ELSIF V_TranType = 'Adjust Customary' THEN
        SELECT BillableAmount, Quantity
        INTO V_OldValue, V_Quantity
        FROM c01.tbl_invoicedetails
        WHERE CustomerID = NEW.CustomerID
          AND InvoiceID = NEW.InvoiceID
          AND ID = NEW.InvoiceDetailsID;

        NEW.Quantity := V_Quantity;
        NEW.Comments := CONCAT('Previous Value=', V_OldValue);

        IF ABS(V_OldValue - NEW.Amount) > 0.001 THEN
            UPDATE c01.tbl_invoicedetails
            SET BillableAmount = NEW.Amount
            WHERE CustomerID = NEW.CustomerID
              AND InvoiceID = NEW.InvoiceID
              AND ID = NEW.InvoiceDetailsID;
        END IF;

    ELSIF V_TranType = 'Adjust Taxes' THEN
        SELECT Taxes, Quantity
        INTO V_OldValue, V_Quantity
        FROM c01.tbl_invoicedetails
        WHERE CustomerID = NEW.CustomerID
          AND InvoiceID = NEW.InvoiceID
          AND ID = NEW.InvoiceDetailsID;

        NEW.Quantity := V_Quantity;
        NEW.Comments := CONCAT('Previous Value=', V_OldValue);

        IF ABS(V_OldValue - NEW.Amount) > 0.001 THEN
            UPDATE c01.tbl_invoicedetails
            SET Taxes = NEW.Amount
            WHERE CustomerID = NEW.CustomerID
              AND InvoiceID = NEW.InvoiceID
              AND ID = NEW.InvoiceDetailsID;
        END IF;
    END IF;

    RETURN NEW;
END;
$BODY$;

ALTER FUNCTION c01.tbl_invoice_transaction_beforeinsert()
    OWNER TO postgres;
