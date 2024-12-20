CREATE DEFINER=`root`@`localhost` FUNCTION `GetQuantityMultiplier`(
    P_FromDate DATETIME,
    P_ToDate DATETIME,
    P_PickupDate DATETIME,
    P_SaleRentType VARCHAR(50),
    P_OrderedWhen VARCHAR(50),
    P_BilledWhen VARCHAR(50)) RETURNS double
    DETERMINISTIC
BEGIN
    DECLARE V_NextToDate DATETIME; --

    IF     P_SaleRentType = 'One Time Sale'          THEN RETURN 1; --
    ELSEIF P_SaleRentType = 'Re-occurring Sale'      THEN RETURN 1; --
    ELSEIF P_SaleRentType = 'Rent to Purchase'       THEN RETURN 1; --
    ELSEIF P_SaleRentType = 'Capped Rental'          THEN RETURN 1; --
    ELSEIF P_SaleRentType = 'Parental Capped Rental' THEN RETURN 1; --
    ELSEIF P_SaleRentType = 'Medicare Oxygen Rental' THEN RETURN 1; --
    ELSEIF P_SaleRentType = 'Monthly Rental'         THEN
        IF (P_OrderedWhen = 'Daily') THEN
            SET V_NextToDate = GetNextDosFrom(P_FromDate, P_ToDate, P_BilledWhen); --
            IF P_PickupDate IS NULL THEN
                RETURN DATEDIFF(V_NextToDate, P_FromDate); --
            ELSEIF V_NextToDate <= P_PickupDate THEN
                RETURN DATEDIFF(V_NextToDate, P_FromDate); --
            ELSEIF P_FromDate <= P_PickupDate THEN
                RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1); --
            ELSE -- P_PickupDate < P_FromDate
                RETURN 0; --
            END IF; --
        ELSE
            RETURN 1; --
        END IF; --
    ELSEIF P_SaleRentType = 'One Time Rental'        THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1); --
    END IF; --

    RETURN NULL; --
END