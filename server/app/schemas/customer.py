"""
Customer Management Domain Schemas
Version: 2024-12-14_17-45
"""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, EmailStr, constr, validator, Field

from app.schemas.system import TimestampSchema

# Enums
class Gender(str, Enum):
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'

class MaritalStatus(str, Enum):
    SINGLE = 'S'
    MARRIED = 'M'
    DIVORCED = 'D'
    WIDOWED = 'W'
    OTHER = 'O'

# Customer Schemas
class CustomerBase(BaseModel):
    company_id: int
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    middle_name: Optional[str] = None
    date_of_birth: date
    ssn: Optional[constr(regex=r'^\d{3}-?\d{2}-?\d{4}$')] = None
    gender: Gender
    marital_status: Optional[MaritalStatus] = None
    email: Optional[EmailStr] = None
    phone_home: Optional[str] = None
    phone_work: Optional[str] = None
    phone_mobile: Optional[str] = None
    height: Optional[int] = Field(None, ge=0, le=120)  # max 10 feet in inches
    weight: Optional[int] = Field(None, ge=0, le=1000)  # max 1000 pounds

    @validator('ssn')
    def format_ssn(cls, v):
        if v:
            # Remove any existing hyphens and add them in the correct positions
            clean_ssn = v.replace('-', '')
            return f"{clean_ssn[:3]}-{clean_ssn[3:5]}-{clean_ssn[5:]}"
        return v

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class Customer(CustomerBase, TimestampSchema):
    id: int
    is_active: bool
    status_date: datetime
    full_name: str

    class Config:
        from_attributes = True

# Address Schemas
class CustomerAddressBase(BaseModel):
    customer_id: int
    address_type: constr(min_length=1, max_length=20)
    address1: constr(min_length=1, max_length=100)
    address2: Optional[str] = None
    city: constr(min_length=1, max_length=50)
    state: constr(min_length=2, max_length=2)
    zip_code: constr(regex=r'^\d{5}(-\d{4})?$')
    is_primary: bool = False
    is_billing: bool = False
    is_shipping: bool = False

class CustomerAddressCreate(CustomerAddressBase):
    pass

class CustomerAddressUpdate(CustomerAddressBase):
    pass

class CustomerAddress(CustomerAddressBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# Insurance Company Schemas
class InsuranceCompanyBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    payer_id: constr(min_length=1, max_length=50)
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[constr(min_length=2, max_length=2)] = None
    zip_code: Optional[constr(regex=r'^\d{5}(-\d{4})?$')] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    is_active: bool = True

class InsuranceCompanyCreate(InsuranceCompanyBase):
    pass

class InsuranceCompanyUpdate(InsuranceCompanyBase):
    pass

class InsuranceCompany(InsuranceCompanyBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# Customer Insurance Schemas
class CustomerInsuranceBase(BaseModel):
    customer_id: int
    insurance_company_id: int
    policy_number: constr(min_length=1, max_length=50)
    group_number: Optional[str] = None
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    is_primary: bool = False
    is_active: bool = True
    verification_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    verification_reference: Optional[str] = None

    @validator('termination_date')
    def validate_termination_date(cls, v, values):
        if v and values.get('effective_date') and v < values['effective_date']:
            raise ValueError('Termination date must be after effective date')
        return v

class CustomerInsuranceCreate(CustomerInsuranceBase):
    pass

class CustomerInsuranceUpdate(CustomerInsuranceBase):
    pass

class CustomerInsurance(CustomerInsuranceBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# Doctor Schemas
class DoctorBase(BaseModel):
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    middle_name: Optional[str] = None
    suffix: Optional[str] = None
    npi: constr(regex=r'^\d{10}$')
    license_number: constr(min_length=1, max_length=50)
    license_expiry: Optional[date] = None
    upin_number: Optional[str] = None
    medicaid_number: Optional[str] = None
    address1: constr(min_length=1, max_length=100)
    address2: Optional[str] = None
    city: constr(min_length=1, max_length=50)
    state: constr(min_length=2, max_length=2)
    zip_code: constr(regex=r'^\d{5}(-\d{4})?$')
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool = True

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(DoctorBase):
    pass

class Doctor(DoctorBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True

# Facility Schemas
class FacilityBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    facility_type: constr(min_length=1, max_length=50)
    address1: constr(min_length=1, max_length=100)
    address2: Optional[str] = None
    city: constr(min_length=1, max_length=50)
    state: constr(min_length=2, max_length=2)
    zip_code: constr(regex=r'^\d{5}(-\d{4})?$')
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    npi: Optional[constr(regex=r'^\d{10}$')] = None
    tax_id: Optional[str] = None
    is_active: bool = True

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(FacilityBase):
    pass

class Facility(FacilityBase, TimestampSchema):
    id: int

    class Config:
        from_attributes = True
