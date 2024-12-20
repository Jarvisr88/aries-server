"""
CMN Form MIR Update Procedure

Python implementation of the mir_update_cmnform stored procedure.
"""
from typing import Optional
from datetime import date
from sqlalchemy import select, update, and_, or_, case, func
from sqlalchemy.orm import joinedload
from app.models.customer import (
    CMNForm,
    CMNForm0102A,
    CMNForm0702A,
    CMNForm0703A,
    Customer,
    Doctor,
    Facility,
    ICD9Code
)
from app.procedures.base import BaseProcedure


class UpdateCMNFormMIR(BaseProcedure):
    """
    Updates Medical Information Records (MIR) for CMN forms.
    
    This procedure:
    1. Validates basic form information
    2. Checks ICD9 codes
    3. Validates form-specific answers
    4. Updates MIR flags
    """

    async def _execute(self, cmn_form_id: Optional[int] = None) -> None:
        """Execute the CMN form MIR update procedure"""
        # Step 1: Update basic form validation
        await self._update_basic_validation(cmn_form_id)
        
        # Step 2: Update ICD9 validation
        await self._update_icd9_validation(cmn_form_id)
        
        # Step 3: Update form-specific validations
        await self._update_form_specific_validation(cmn_form_id)

    async def _update_basic_validation(self, cmn_form_id: Optional[int]) -> None:
        """Update basic form validation flags"""
        update_stmt = (
            update(CMNForm)
            .outerjoin(Customer)
            .outerjoin(Doctor)
            .outerjoin(Facility)
            .where(
                or_(
                    CMNForm.id == cmn_form_id,
                    cmn_form_id.is_(None)
                )
            )
            .values(
                mir=func.concat_ws(
                    ',',
                    case(
                        (func.coalesce(CMNForm.cmn_type, '') == '', 'CMNType'),
                        else_=None
                    ),
                    case(
                        (func.coalesce(CMNForm.signature_name, '') == '', 'Signature_Name'),
                        else_=None
                    ),
                    case(
                        (CMNForm.initial_date.is_(None), 'InitialDate'),
                        else_=None
                    ),
                    case(
                        (CMNForm.pos_type_id.is_(None), 'POSTypeID'),
                        else_=None
                    ),
                    case(
                        (CMNForm.signature_date.is_(None), 'Signature_Date'),
                        else_=None
                    ),
                    case(
                        (
                            or_(
                                CMNForm.estimated_length_of_need.is_(None),
                                CMNForm.estimated_length_of_need <= 0
                            ),
                            'EstimatedLengthOfNeed'
                        ),
                        else_=None
                    ),
                    case(
                        (Customer.id.is_(None), 'CustomerID'),
                        else_=None
                    ),
                    case(
                        (Customer.mir != '', 'Customer'),
                        else_=None
                    ),
                    case(
                        (Doctor.id.is_(None), 'DoctorID'),
                        else_=None
                    ),
                    case(
                        (Doctor.mir != '', 'Doctor'),
                        else_=None
                    )
                )
            )
        )
        await self.db.execute(update_stmt)

    async def _update_icd9_validation(self, cmn_form_id: Optional[int]) -> None:
        """Update ICD9 code validation flags"""
        update_stmt = (
            update(CMNForm)
            .outerjoin(
                ICD9Code,
                ICD9Code.code == CMNForm.customer_icd9_1,
                isouter=True,
                full=True
            )
            .outerjoin(
                ICD9Code,
                ICD9Code.code == CMNForm.customer_icd9_2,
                isouter=True,
                full=True
            )
            .outerjoin(
                ICD9Code,
                ICD9Code.code == CMNForm.customer_icd9_3,
                isouter=True,
                full=True
            )
            .outerjoin(
                ICD9Code,
                ICD9Code.code == CMNForm.customer_icd9_4,
                isouter=True,
                full=True
            )
            .where(
                or_(
                    CMNForm.id == cmn_form_id,
                    cmn_form_id.is_(None)
                )
            )
            .values(
                mir=func.concat_ws(
                    ',',
                    CMNForm.mir,  # Keep existing flags
                    # ICD9_1 validation
                    case(
                        (
                            func.coalesce(CMNForm.customer_icd9_1, '') == '',
                            'ICD9_1.Required'
                        ),
                        (
                            ICD9Code.code.is_(None),
                            'ICD9_1.Unknown'
                        ),
                        (
                            ICD9Code.inactive_date <= CMNForm.initial_date,
                            'ICD9_1.Inactive'
                        ),
                        else_=None
                    ),
                    # ICD9_2 validation
                    case(
                        (
                            and_(
                                func.coalesce(CMNForm.customer_icd9_2, '') != '',
                                ICD9Code.code.is_(None)
                            ),
                            'ICD9_2.Unknown'
                        ),
                        (
                            ICD9Code.inactive_date <= CMNForm.initial_date,
                            'ICD9_2.Inactive'
                        ),
                        else_=None
                    ),
                    # Add ICD9_3 and ICD9_4 validation similarly
                )
            )
        )
        await self.db.execute(update_stmt)

    async def _update_form_specific_validation(
        self,
        cmn_form_id: Optional[int]
    ) -> None:
        """Update form-specific validation flags"""
        # DMERC 01.02A form validation
        await self._update_0102a_validation(cmn_form_id)
        
        # DMERC 07.02A form validation
        await self._update_0702a_validation(cmn_form_id)
        
        # DME 07.03A form validation
        await self._update_0703a_validation(cmn_form_id)

    async def _update_0102a_validation(
        self,
        cmn_form_id: Optional[int]
    ) -> None:
        """Update DMERC 01.02A form validation"""
        update_stmt = (
            update(CMNForm)
            .join(CMNForm0102A)
            .where(
                and_(
                    or_(
                        CMNForm.id == cmn_form_id,
                        cmn_form_id.is_(None)
                    ),
                    CMNForm.cmn_type == 'DMERC 01.02A',
                    or_(
                        func.coalesce(CMNForm0102A.answer1, '') != 'Y',
                        func.coalesce(CMNForm0102A.answer3, '') != 'Y',
                        func.coalesce(CMNForm0102A.answer4, '') != 'Y'
                    )
                )
            )
            .values(
                mir=func.concat_ws(
                    ',',
                    'Answers',
                    case(
                        (CMNForm.mir != '', CMNForm.mir),
                        else_=None
                    )
                )
            )
        )
        await self.db.execute(update_stmt)

    async def _update_0702a_validation(
        self,
        cmn_form_id: Optional[int]
    ) -> None:
        """Update DMERC 07.02A form validation"""
        update_stmt = (
            update(CMNForm)
            .join(CMNForm0702A)
            .where(
                and_(
                    or_(
                        CMNForm.id == cmn_form_id,
                        cmn_form_id.is_(None)
                    ),
                    CMNForm.cmn_type == 'DMERC 07.02A',
                    or_(
                        func.coalesce(CMNForm0702A.answer1, '') != 'Y',
                        func.coalesce(CMNForm0702A.answer2, '') != 'Y'
                    )
                )
            )
            .values(
                mir=func.concat_ws(
                    ',',
                    'Answers',
                    case(
                        (CMNForm.mir != '', CMNForm.mir),
                        else_=None
                    )
                )
            )
        )
        await self.db.execute(update_stmt)

    async def _update_0703a_validation(
        self,
        cmn_form_id: Optional[int]
    ) -> None:
        """Update DME 07.03A form validation"""
        update_stmt = (
            update(CMNForm)
            .join(CMNForm0703A)
            .where(
                and_(
                    or_(
                        CMNForm.id == cmn_form_id,
                        cmn_form_id.is_(None)
                    ),
                    CMNForm.cmn_type == 'DME 07.03A',
                    or_(
                        func.coalesce(CMNForm0703A.answer1, '') != 'Y',
                        func.coalesce(CMNForm0703A.answer2, '') != 'Y'
                    )
                )
            )
            .values(
                mir=func.concat_ws(
                    ',',
                    'Answers',
                    case(
                        (CMNForm.mir != '', CMNForm.mir),
                        else_=None
                    )
                )
            )
        )
        await self.db.execute(update_stmt)
