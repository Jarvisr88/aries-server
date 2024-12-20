# Aries Project Guiding Principles

## Core Principles

### 1. Framework Decisions
✅ **FastAPI**
- NOT Django
- Modern async capabilities
- Type safety with Pydantic

### 2. UI Implementation
✅ **Custom Material-UI**
- NOT Materio Admin Template
- Custom component library
- Healthcare-specific patterns

### 3. Analysis Methodology
✅ **Comprehensive Documentation**
- All analysis must be interconnected
- New analysis supplements existing documentation
- Cross-reference related analyses
- Build upon previous insights
- Maintain consistency across documents

### 4. Project Structure
✅ **Clear Separation of Concerns**
- `/client`: All frontend logic and UI components
  - Material-UI custom components
  - Frontend application code
  - Frontend assets and resources
- `/server`: All backend logic and API endpoints
  - FastAPI implementation
  - Business logic
  - Database interactions
  - API endpoints
- Project root: Project-wide configuration and documentation
  - Build configurations
  - Project-level documentation
  - Shared utilities and resources

### 5. Project Documentation Structure
✅ **Wisdom Directory Organization**
- `/01_Planning`: Project planning, guiding principles, and strategic documents
- `/02_Analysis`: Business and technical analysis documentation
- `/03_Design`: System architecture and design specifications
- `/04_Code`: Code-related documentation and technical specifications
- `/05_Test`: Test strategies, test cases, and quality assurance documents

### 6. Version Control and Timestamps
✅ **Documentation Versioning**
- All documents will include timestamps for version control
- Format: YYYY-MM-DD_HH-MM
- Each major revision requires a new timestamp
- Maintain change history within documents
- Cross-reference between related document versions

### 7. Code Implementation Standards
✅ **Stored Procedures and Triggers**
- Convert all SQL stored procedures to Python classes
- Inherit from BaseProcedure for consistency
- Implement async/await patterns
- Include comprehensive error handling
- Maintain detailed logging
- Follow naming conventions:
  - Procedures: CamelCase with descriptive action names
  - Triggers: CamelCase with 'Trigger' suffix
  - Utility Functions: snake_case for standalone functions

### 8. Documentation Standards
✅ **Technical Documentation**
- Maintain class dictionary for all implementations
- Include purpose, methods, and dependencies
- Document relationships between classes
- Provide usage examples and patterns
- Keep documentation in sync with code changes
- Location: `/wisdom/01_Planning/Technical Specifications/`

### 9. Testing Requirements
✅ **Quality Assurance**
- Unit tests for all procedures and triggers
- Integration tests for workflows
- Edge case coverage
- Performance testing for critical paths
- Test documentation and scenarios

### 10. Code Organization
✅ **Directory Structure**
- `/server/app/procedures/`: All procedure implementations
  - Domain-specific subdirectories
  - Base classes and utilities
- `/server/app/triggers/`: All trigger implementations
  - Event-based logic
  - Database triggers as Python classes
- `/tests/procedures/`: Procedure tests
- `/tests/triggers/`: Trigger tests

### 11. Implementation Workflow
✅ **Development Process**
1. Analyze original SQL implementation
2. Design Python class structure
3. Implement core functionality
4. Add error handling and logging
5. Create comprehensive tests
6. Update technical documentation
7. Create status reports
8. Prepare handoff documentation

### Analysis Integration Guidelines

1. **Cross-Referencing**
   - Link related analyses
   - Reference previous findings
   - Note impacts on existing documentation
   - Highlight dependencies

2. **Documentation Structure**
   - Clear section organization
   - Consistent formatting
   - Version tracking
   - Change history

3. **Analysis Components**
   - Technical considerations
   - Business impact
   - Implementation details
   - Risk assessment
   - Recommendations

4. **Integration Points**
   - Reference related documents
   - Note affected systems
   - Identify dependencies
   - Track changes

## Analysis Standards

### Document Organization
- Clear structure
- Consistent formatting
- Cross-references
- Version control

### Content Requirements
- Technical accuracy
- Business context
- Implementation details
- Risk assessment
- Recommendations

### Integration Guidelines
- Reference related docs
- Build on previous analysis
- Note dependencies
- Track changes

## Important Notes

1. **Framework Choice**
   - FastAPI is our chosen backend framework
   - Do NOT implement Django patterns or components
   - Ignore any Django references in documentation

2. **UI Implementation**
   - Custom Material-UI implementation
   - Do NOT use Materio Admin Template
   - Ignore any references to Materio in documentation
   - Custom component library development

3. **Analysis Integration**
   - All analyses must cross-reference related documents
   - Build upon previous findings
   - Maintain consistency across documentation
   - Track changes and impacts

_Note: This document serves as the source of truth for project principles and decisions. Any conflicting information in other documents should defer to these guidelines. All analyses must follow the comprehensive documentation principle, building upon and referencing previous work._
