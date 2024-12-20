CREATE DEFINER=`root`@`localhost` FUNCTION `GetAmountMultiplier`(
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
          RETURN GetMultiplier(P_FromDate, P_ToDate, P_OrderedWhen, P_BilledWhen); --
        END IF; --
    ELSEIF P_SaleRentType = 'One Time Rental'        THEN
        IF     P_OrderedWhen = 'One Time'      THEN RETURN 1; --
        ELSEIF P_OrderedWhen = 'Daily'         THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1); --
        ELSEIF P_OrderedWhen = 'Weekly'        THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1) / 7.0; --
        ELSEIF P_OrderedWhen = 'Monthly'       THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1) / 30.4; --
        ELSEIF P_OrderedWhen = 'Quarterly'     THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1) / 91.25; --
        ELSEIF P_OrderedWhen = 'Semi-Annually' THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1) / 182.5; --
        ELSEIF P_OrderedWhen = 'Annually'      THEN RETURN (DATEDIFF(P_PickupDate, P_FromDate) + 1) / 365.0; --
        END IF; --
    END IF; --

    RETURN NULL; --
END