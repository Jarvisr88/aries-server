"""
Customer Management Domain Models
Version: 2024-12-14_17-45
"""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Table, Boolean, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.system import TimestampMixin
from app.core.database import Base

# Association tables
customer_facilities = Table(
    'customer_facilities',
    Base.metadata,
    Column('customer_id', Integer, ForeignKey('customers.id'), primary_key=True),
    Column('facility_id', Integer, ForeignKey('facilities.id'), primary_key=True)
)

customer_doctors = Table(
    'customer_doctors',
    Base.metadata,
    Column('customer_id', Integer, ForeignKey('customers.id'), primary_key=True),
    Column('doctor_id', Integer, ForeignKey('doctors.id'), primary_key=True)
)

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

class Customer(Base, TimestampMixin):
    """Customer/Patient model - migrated from c01.tbl_customer"""
    __tablename__ = 'customers'

    id: Mapped[int] = Column(Integer, primary_key=True)
    company_id: Mapped[int] = Column(Integer, ForeignKey('companies.id'), nullable=False)
    
    # Personal Information
    first_name: Mapped[str] = Column(String(50), nullable=False)
    last_name: Mapped[str] = Column(String(50), nullable=False)
    middle_name: Mapped[Optional[str]] = Column(String(50))
    date_of_birth: Mapped[date] = Column(Date, nullable=False)
    ssn: Mapped[Optional[str]] = Column(String(11))
    gender: Mapped[Gender] = Column(SQLEnum(Gender), nullable=False)
    marital_status: Mapped[MaritalStatus] = Column(SQLEnum(MaritalStatus))
    
    # Contact Information
    email: Mapped[Optional[str]] = Column(String(100))
    phone_home: Mapped[Optional[str]] = Column(String(20))
    phone_work: Mapped[Optional[str]] = Column(String(20))
    phone_mobile: Mapped[Optional[str]] = Column(String(20))
    
    # Status
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    status_date: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    # Medical
    height: Mapped[Optional[int]] = Column(Integer)  # in inches
    weight: Mapped[Optional[int]] = Column(Integer)  # in pounds
    
    # Relationships
    addresses: Mapped[List["CustomerAddress"]] = relationship("CustomerAddress", back_populates="customer")
    insurance_policies: Mapped[List["CustomerInsurance"]] = relationship("CustomerInsurance", back_populates="customer")
    facilities: Mapped[List["Facility"]] = relationship(
        "Facility",
        secondary=customer_facilities,
        back_populates="customers"
    )
    doctors: Mapped[List["Doctor"]] = relationship(
        "Doctor",
        secondary=customer_doctors,
        back_populates="customers"
    )
    orders = relationship("Order", back_populates="customer")  # Will be defined in Order domain

    @hybrid_property
    def full_name(self) -> str:
        """Returns the full name of the customer"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

class CustomerAddress(Base, TimestampMixin):
    """Customer Address model - migrated from c01.tbl_customer_address"""
    __tablename__ = 'customer_addresses'

    id: Mapped[int] = Column(Integer, primary_key=True)
    customer_id: Mapped[int] = Column(Integer, ForeignKey('customers.id'), nullable=False)
    address_type: Mapped[str] = Column(String(20), nullable=False)  # billing, shipping, etc.
    
    address1: Mapped[str] = Column(String(100), nullable=False)
    address2: Mapped[Optional[str]] = Column(String(100))
    city: Mapped[str] = Column(String(50), nullable=False)
    state: Mapped[str] = Column(String(2), nullable=False)
    zip_code: Mapped[str] = Column(String(10), nullable=False)
    
    is_primary: Mapped[bool] = Column(Boolean, default=False)
    is_billing: Mapped[bool] = Column(Boolean, default=False)
    is_shipping: Mapped[bool] = Column(Boolean, default=False)
    
    customer: Mapped[Customer] = relationship("Customer", back_populates="addresses")

class InsuranceCompany(Base, TimestampMixin):
    """Insurance Company model - migrated from c01.tbl_insurance_company"""
    __tablename__ = 'insurance_companies'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    payer_id: Mapped[str] = Column(String(50), nullable=False, unique=True)
    
    address1: Mapped[Optional[str]] = Column(String(100))
    address2: Mapped[Optional[str]] = Column(String(100))
    city: Mapped[Optional[str]] = Column(String(50))
    state: Mapped[Optional[str]] = Column(String(2))
    zip_code: Mapped[Optional[str]] = Column(String(10))
    
    phone: Mapped[Optional[str]] = Column(String(20))
    fax: Mapped[Optional[str]] = Column(String(20))
    
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    policies: Mapped[List["CustomerInsurance"]] = relationship("CustomerInsurance", back_populates="insurance_company")

class CustomerInsurance(Base, TimestampMixin):
    """Customer Insurance model - migrated from c01.tbl_customer_insurance"""
    __tablename__ = 'customer_insurances'

    id: Mapped[int] = Column(Integer, primary_key=True)
    customer_id: Mapped[int] = Column(Integer, ForeignKey('customers.id'), nullable=False)
    insurance_company_id: Mapped[int] = Column(Integer, ForeignKey('insurance_companies.id'), nullable=False)
    
    policy_number: Mapped[str] = Column(String(50), nullable=False)
    group_number: Mapped[Optional[str]] = Column(String(50))
    
    effective_date: Mapped[Optional[date]] = Column(Date)
    termination_date: Mapped[Optional[date]] = Column(Date)
    
    is_primary: Mapped[bool] = Column(Boolean, default=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    verification_date: Mapped[Optional[datetime]] = Column(DateTime)
    verification_method: Mapped[Optional[str]] = Column(String(50))
    verification_reference: Mapped[Optional[str]] = Column(String(50))
    
    customer: Mapped[Customer] = relationship("Customer", back_populates="insurance_policies")
    insurance_company: Mapped[InsuranceCompany] = relationship("InsuranceCompany", back_populates="policies")

class Doctor(Base, TimestampMixin):
    """Doctor model - migrated from c01.tbl_doctor"""
    __tablename__ = 'doctors'

    id: Mapped[int] = Column(Integer, primary_key=True)
    
    # Personal Information
    first_name: Mapped[str] = Column(String(50), nullable=False)
    last_name: Mapped[str] = Column(String(50), nullable=False)
    middle_name: Mapped[Optional[str]] = Column(String(1))
    suffix: Mapped[Optional[str]] = Column(String(10))
    
    # Professional Information
    npi: Mapped[str] = Column(String(10), unique=True, nullable=False)
    license_number: Mapped[str] = Column(String(50), nullable=False)
    license_expiry: Mapped[Optional[date]] = Column(Date)
    upin_number: Mapped[Optional[str]] = Column(String(20))
    medicaid_number: Mapped[Optional[str]] = Column(String(20))
    
    # Contact Information
    address1: Mapped[str] = Column(String(100), nullable=False)
    address2: Mapped[Optional[str]] = Column(String(100))
    city: Mapped[str] = Column(String(50), nullable=False)
    state: Mapped[str] = Column(String(2), nullable=False)
    zip_code: Mapped[str] = Column(String(10), nullable=False)
    
    phone: Mapped[Optional[str]] = Column(String(20))
    fax: Mapped[Optional[str]] = Column(String(20))
    email: Mapped[Optional[str]] = Column(String(100))
    
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # Relationships
    customers: Mapped[List[Customer]] = relationship(
        "Customer",
        secondary=customer_doctors,
        back_populates="doctors"
    )

class Facility(Base, TimestampMixin):
    """Facility model - migrated from c01.tbl_facility"""
    __tablename__ = 'facilities'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    facility_type: Mapped[str] = Column(String(50), nullable=False)
    
    address1: Mapped[str] = Column(String(100), nullable=False)
    address2: Mapped[Optional[str]] = Column(String(100))
    city: Mapped[str] = Column(String(50), nullable=False)
    state: Mapped[str] = Column(String(2), nullable=False)
    zip_code: Mapped[str] = Column(String(10), nullable=False)
    
    phone: Mapped[Optional[str]] = Column(String(20))
    fax: Mapped[Optional[str]] = Column(String(20))
    email: Mapped[Optional[str]] = Column(String(100))
    
    npi: Mapped[Optional[str]] = Column(String(10))
    tax_id: Mapped[Optional[str]] = Column(String(20))
    
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # Relationships
    customers: Mapped[List[Customer]] = relationship(
        "Customer",
        secondary=customer_facilities,
        back_populates="facilities"
    )
