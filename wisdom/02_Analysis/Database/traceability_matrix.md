# Database Objects Traceability Matrix
Version: 2024-12-16_10-12

## Overview
This matrix tracks the implementation status of database objects and their corresponding Python implementations across the Aries Enterprise system.

## Legend
- ✓ : Implemented
- 🚧 : In Progress
- ❌ : Not Started
- ➖ : Not Applicable

## Database Schemas

### Repository Schema (6 Tables)
| Table Name | Model Implementation | Service Implementation | Tests | Status |
|------------|---------------------|----------------------|--------|---------|
| tbl_batches | 🚧 Batch | 🚧 BatchService | ❌ | In Progress |
| tbl_certificates | 🚧 Certificate | 🚧 CertificateService | ❌ | In Progress |
| tbl_companies | 🚧 Company | 🚧 CompanyService | ❌ | In Progress |
| tbl_globals | 🚧 Global | 🚧 GlobalService | ❌ | In Progress |
| tbl_regions | 🚧 Region | 🚧 RegionService | ❌ | In Progress |
| tbl_variables | 🚧 Variable | 🚧 VariableService | ❌ | In Progress |

### DMEWorks Schema (10 Tables)
| Table Name | Model Implementation | Service Implementation | Tests | Status |
|------------|---------------------|----------------------|--------|---------|
| tbl_ability_eligibility_payer | 🚧 AbilityEligibilityPayer | 🚧 EligibilityService | ❌ | In Progress |
| tbl_doctor | 🚧 Doctor | 🚧 DoctorService | ❌ | In Progress |
| tbl_doctortype | 🚧 DoctorType | 🚧 DoctorService | ❌ | In Progress |
| tbl_icd10 | 🚧 ICD10 | 🚧 DiagnosisService | ❌ | In Progress |
| tbl_icd9 | 🚧 ICD9 | 🚧 DiagnosisService | ❌ | In Progress |
| tbl_insurancecompany | 🚧 InsuranceCompany | 🚧 InsuranceService | ❌ | In Progress |
| tbl_insurancecompanytype | 🚧 InsuranceCompanyType | 🚧 InsuranceService | ❌ | In Progress |
| tbl_insurancecompanytype_category | 🚧 InsuranceCompanyTypeCategory | 🚧 InsuranceService | ❌ | In Progress |
| tbl_insurancecompanytype_region | 🚧 InsuranceCompanyTypeRegion | 🚧 InsuranceService | ❌ | In Progress |
| tbl_insurancecompanytype_subcategory | 🚧 InsuranceCompanyTypeSubCategory | 🚧 InsuranceService | ❌ | In Progress |

### Customer Management Domain (Schema: c01)
| Database Object          | Model Implementation | Service Implementation | Tests | Notes |
|-------------------------|---------------------|----------------------|--------|--------|
| tbl_customer            | ✓ Customer          | ✓ CustomerService    | ✓      | Core customer management |
| tbl_customer_address    | ✓ CustomerAddress   | ✓ CustomerService    | ✓      | Handled in CustomerService |
| tbl_customer_contact    | ✓ CustomerContact   | ✓ CustomerService    | ✓      | Handled in CustomerService |
| tbl_customer_insurance  | ✓ CustomerInsurance | ✓ CustomerService    | ✓      | Handled in CustomerService |
| tbl_customer_documents  | ✓ CustomerDocument  | ✓ CustomerService    | ✓      | Handled in CustomerService |
| tbl_insurance_company   | ✓ InsuranceCompany  | ✓ InsuranceService   | ✓      | Insurance provider management |
| tbl_insurance_policy    | ✓ InsurancePolicy   | ✓ InsuranceService   | ✓      | Insurance policy management |
| tbl_facility           | ✓ Facility          | ✓ FacilityService    | ✓      | Healthcare facility management |
| tbl_doctor             | ✓ Doctor            | ✓ DoctorService      | ✓      | Healthcare provider management |

### Order Processing Domain (Schema: c01)
| Database Object          | Model Implementation | Service Implementation | Tests | Notes |
|-------------------------|---------------------|----------------------|--------|--------|
| tbl_order               | ✓ Order             | ✓ OrderService       | ✓      | Core order management |
| tbl_orderdetails        | ✓ OrderDetail       | ✓ OrderService       | ✓      | Handled in OrderService |
| tbl_order_status        | ✓ OrderStatus       | ✓ OrderService       | ✓      | Handled in OrderService |
| tbl_order_tracking      | ✓ OrderTracking     | ✓ OrderService       | ✓      | Handled in OrderService |
| tbl_shipping_method     | ✓ ShippingMethod    | ✓ OrderService       | ✓      | Shipping method management |
| tbl_delivery_schedule   | ✓ DeliverySchedule  | ✓ OrderService       | ✓      | Delivery scheduling |
| tbl_authorization       | ✓ Authorization     | ✓ OrderService       | ✓      | Order authorization |

### Inventory Management Domain (Schema: dmeworks)
| Database Object          | Model Implementation | Service Implementation | Tests | Notes |
|-------------------------|---------------------|----------------------|--------|--------|
| tbl_inventoryitem       | ✓ InventoryItem     | ✓ InventoryItemService| ✓      | Core inventory management |
| tbl_inventory_location  | ✓ InventoryLocation | ✓ InventoryItemService| ✓      | Location tracking |
| tbl_inventory_transaction| ✓ InventoryTransaction| ✓ InventoryItemService| ✓      | Stock movements |
| tbl_warehouse           | ✓ Warehouse         | ✓ WarehouseService   | ✓      | Warehouse management |
| tbl_item_category       | ✓ ItemCategory      | ✓ InventoryItemService| ✓      | Item categorization |
| tbl_supplier            | ✓ Supplier          | ✓ SupplierService    | ✓      | Supplier management |
| tbl_maintenance_schedule| ✓ MaintenanceSchedule| ✓ MaintenanceService | ✓      | Equipment maintenance |

### Billing & Insurance Domain (Schema: c01)
| Database Object          | Model Implementation | Service Implementation | Tests | Notes |
|-------------------------|---------------------|----------------------|--------|--------|
| tbl_invoice             | ✓ Invoice           | ✓ InvoiceService     | ✓      | Core billing management |
| tbl_invoice_details     | ✓ InvoiceDetail     | ✓ InvoiceService     | ✓      | Handled in InvoiceService |
| tbl_payment             | ✓ Payment           | ✓ PaymentService     | ✓      | Payment processing |
| tbl_insurance_claim     | ✓ InsuranceClaim    | ✓ InsuranceClaimService| ✓    | Claims management |
| tbl_billing_code        | ✓ BillingCode       | ✓ BillingCodeService | ✓      | Billing code management |
| tbl_price_code          | ✓ PriceCode         | ✓ BillingCodeService | ✓      | Price code management |
| tbl_payment_type        | ✓ PaymentType       | ✓ PaymentService     | ✓      | Payment type management |

### System Configuration Domain (Schema: repository)
| Database Object          | Model Implementation | Service Implementation | Tests | Notes |
|-------------------------|---------------------|----------------------|--------|--------|
| tbl_company             | ✓ Company           | ✓ CompanyService     | ✓      | Company management |
| tbl_user                | ✓ User              | ✓ UserService        | ✓      | User management |
| tbl_role                | ✓ Role              | ✓ RoleService        | ✓      | Role management |
| tbl_permission          | ✓ Permission        | ✓ PermissionService  | ✓      | Permission management |
| tbl_system_config       | ✓ SystemConfig      | ✓ SystemConfigService| ✓      | System configuration |
| tbl_audit_log           | ✓ AuditLog          | ✓ AuditLogService    | ✓      | Audit logging |
| tbl_batch_process       | ✓ BatchProcess      | ✓ BatchProcessService| ✓      | Batch process management |

## Custom Types

| Database Type           | Python Implementation | Used In | Notes |
|------------------------|---------------------|----------|--------|
| order_status_type      | ✓ OrderStatus (Enum) | Order Service | Order status tracking |
| payment_status_type    | ✓ PaymentStatus (Enum)| Payment Service | Payment status tracking |
| claim_status_type      | ✓ ClaimStatus (Enum) | Insurance Service | Claim status tracking |
| item_type              | ✓ ItemType (Enum)    | Inventory Service | Item categorization |
| item_status_type       | ✓ ItemStatus (Enum)  | Inventory Service | Item status tracking |
| maintenance_status_type| ✓ MaintenanceStatus (Enum)| Maintenance Service | Maintenance tracking |
| process_status_type    | ✓ ProcessStatus (Enum)| Batch Process Service | Process status tracking |
| document_type          | ✓ DocumentType (Enum)| Customer Service | Document categorization |
| address_type           | ✓ AddressType (Enum) | Customer Service | Address categorization |
| contact_type           | ✓ ContactType (Enum) | Customer Service | Contact categorization |

## Database Functions Implemented as Services

| Original DB Function    | Python Service Implementation | Tests | Notes |
|------------------------|----------------------------|--------|--------|
| fn_generate_order_number| ✓ OrderService.generate_order_number | ✓ | Order number generation |
| fn_calculate_order_total| ✓ OrderService.calculate_total | ✓ | Order total calculation |
| fn_check_stock_level   | ✓ InventoryService.check_stock_level | ✓ | Stock level verification |
| fn_process_payment     | ✓ PaymentService.process_payment | ✓ | Payment processing |
| fn_validate_insurance  | ✓ InsuranceService.validate_coverage | ✓ | Insurance validation |
| fn_generate_invoice    | ✓ InvoiceService.generate_invoice | ✓ | Invoice generation |
| fn_audit_log          | ✓ AuditLogService.log_action | ✓ | Audit logging |

## Stored Procedures

### Order Domain
| Original Procedure | Python Implementation | Tests | Status | Notes |
|-------------------|----------------------|--------|---------|--------|
| Order_InternalProcess | ✓ OrderInternalProcess | ✓ | Complete | Invoice generation and processing |
| Order_InternalUpdateBalance | ✓ OrderInternalBalance | ✓ | Complete | Balance calculations |
| fixOrderPolicies | ✓ OrderPolicyFixer | ✓ | Complete | Policy management |

### Purchase Domain
| Original Procedure | Python Implementation | Tests | Status | Notes |
|-------------------|----------------------|--------|---------|--------|
| PurchaseOrder_UpdateTotals | ✓ PurchaseOrderTotals | ✓ | Complete | Total calculations |

### Inventory Domain
| Original Procedure | Python Implementation | Tests | Status | Notes |
|-------------------|----------------------|--------|---------|--------|
| InventoryItem_Clone | ✓ InventoryItemCloner | ✓ | Complete | Item cloning |
| inventory_transaction_order_cleanup | ✓ InventoryTransactionCleanup | ✓ | Complete | Transaction maintenance |

### Serial Number Domain
| Original Procedure | Python Implementation | Tests | Status | Notes |
|-------------------|----------------------|--------|---------|--------|
| serial_add_transaction | ✓ SerialTransactionAdder | ✓ | Complete | Transaction management |

### MIR Domain
| Original Procedure | Python Implementation | Tests | Status | Notes |
|-------------------|----------------------|--------|---------|--------|
| mir_update_cmnform | ✓ CMNFormMIRUpdater | ✓ | Complete | CMN form updates |
| mir_update_customer | ✓ CustomerMIRUpdater | ✓ | Complete | Customer MIR updates |

### Utility Functions
| Original Function | Python Implementation | Tests | Status | Notes |
|-------------------|----------------------|--------|---------|--------|
| GetQuantityMultiplier | ✓ get_quantity_multiplier | ✓ | Complete | Billing calculations |
| GetNextDosFrom | ✓ get_next_dos_from | ✓ | Complete | DOS calculations |

## Database Triggers

### Invoice Domain
| Original Trigger | Python Implementation | Tests | Status | Notes |
|-----------------|----------------------|--------|---------|--------|
| tbl_invoice_transaction_beforeinsert | ✓ InvoiceTransactionTrigger | ✓ | Complete | Transaction validation |

## Implementation Progress Summary
- Tables/Models: 54/97 (56%)
- Custom Types: 10/10 (100%)
- Services: 20/35 (57%)
- Tests: 20/35 (57%)
- DB Functions as Services: 7/7 (100%)
- Stored Procedures: 11/11 (100%)
- Triggers: 1/1 (100%)

## Next Steps
1. Create database migration scripts for missing schemas
2. Implement SQLAlchemy models for missing tables
3. Create services for new models
4. Write comprehensive tests
5. Update API endpoints
6. Review and optimize service implementations
7. Monitor stored procedure performance
8. Review trigger implementations
9. Update technical documentation

## Change History
- 2024-12-16_10-12: Added missing schema tables and updated progress
- 2024-12-16_09-47: Added stored procedures and triggers sections
- 2024-12-14_19-30: Initial traceability matrix created
