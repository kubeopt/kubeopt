# AKS Cost Optimizer - Unified Database Architecture Plan

## Current Issues
- Multiple fragmented databases for similar purposes
- JSON files used instead of proper database storage
- Poor naming conventions and scattered file locations
- Data duplication across multiple databases

## Proposed Unified Architecture

### 1. Core Databases (Keep as-is)
- **`alerts.db`** - Alerts and notifications management
- **`clusters.db`** - Cluster configurations and analysis results

### 2. New Consolidated Databases

#### **`ml_analytics.db`** - Machine Learning & Analytics
Consolidates: `enhanced_learning.db`, `learning_data.db`, `optimization_learning.db`

**Tables:**
- `learning_data` - Training data and features
- `model_metadata` - ML model information and versions
- `optimization_results` - Optimization outcomes and performance
- `pattern_analysis` - Workload patterns and classifications
- `feature_engineering` - Feature extraction and transformations
- `model_performance` - Model accuracy and validation metrics

#### **`security_analytics.db`** - Security & Compliance
Consolidates: `compliance.db`, `offline_security.db`, `security_posture.db`

**Tables:**
- `security_assessments` - Security posture evaluations
- `compliance_frameworks` - CIS, NIST, SOC2 compliance data
- `vulnerability_scans` - Security scan results
- `policy_violations` - Policy compliance violations
- `security_metrics` - Security scoring and trends
- `threat_intelligence` - Security threat data

#### **`operational_data.db`** - Operational Analytics
For JSON file data and operational metrics

**Tables:**
- `security_scan_results` - Data from JSON security result files
- `performance_metrics` - System performance data
- `cost_analysis_history` - Historical cost analysis data
- `resource_utilization` - Resource usage patterns
- `audit_logs` - System audit and activity logs

## Migration Benefits

1. **Reduced Complexity**: 4 databases instead of 9+ fragmented files
2. **Better Performance**: Proper indexing and query optimization
3. **Data Integrity**: Foreign key constraints and ACID compliance
4. **Easier Backup**: Fewer files to manage and backup
5. **Clear Separation**: Logical grouping of related functionality
6. **Scalability**: Better database design for future growth

## Implementation Plan

### Phase 1: Schema Design
- Design new database schemas
- Create migration scripts
- Set up proper indexes and constraints

### Phase 2: Data Migration
- Migrate data from fragmented databases
- Convert JSON files to database tables
- Validate data integrity

### Phase 3: Application Updates
- Update all database connections
- Modify data access layer
- Update configuration files

### Phase 4: Testing & Cleanup
- Test all functionality
- Remove old database files
- Update documentation

## File Organization

```
app/data/database/
├── alerts.db              # Alerts & notifications
├── clusters.db            # Cluster management
├── ml_analytics.db        # ML & analytics data
├── security_analytics.db  # Security & compliance
└── operational_data.db    # Operational metrics
```

## Estimated Impact
- **Storage Reduction**: ~30-40% reduction in total database size
- **Performance Improvement**: 50-70% faster queries with proper indexing
- **Maintenance Effort**: 60% reduction in database maintenance tasks
- **Development Speed**: Faster feature development with cleaner architecture