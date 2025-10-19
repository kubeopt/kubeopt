# STRICT CODING STANDARDS - NO FALLBACKS MODE

## 🚨 CRITICAL: PRODUCTION-READY CODE ONLY

This project enforces **STRICT NO-FALLBACK** coding standards. Every piece of code must be production-ready, with proper error handling and validation.

## FORBIDDEN PATTERNS ❌

### 1. Silent Failures
```python
# ❌ FORBIDDEN
try:
    result = risky_operation()
except:
    pass  # Silent failure hides bugs

# ❌ FORBIDDEN  
try:
    result = api_call()
except Exception:
    return None  # Should raise explicit error

# ✅ REQUIRED
try:
    result = api_call()
except ApiError as e:
    raise ValueError(f"API call failed: {e}") from e
```

### 2. Mock Objects & Fallbacks
```python
# ❌ FORBIDDEN
class MockPlan:
    def __init__(self):
        self.status = "unknown"

# ❌ FORBIDDEN
class FallbackModel:
    pass

# ✅ REQUIRED
from pydantic import BaseModel, validator

class ImplementationPlan(BaseModel):
    status: str
    steps: List[str]
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['pending', 'in_progress', 'completed']:
            raise ValueError(f"Invalid status: {v}")
        return v
```

### 3. Defensive Programming
```python
# ❌ FORBIDDEN
if data is None:
    return None

# ❌ FORBIDDEN
if not data:
    return default_value

# ✅ REQUIRED
def validate_input_data(data: Dict) -> Dict:
    if data is None:
        raise ValueError("Input data cannot be None")
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")
    return data
```

### 4. TODOs & Hacks
```python
# ❌ FORBIDDEN
# TODO: fix this later
# FIXME: temporary solution
# HACK: workaround for API issue

# ✅ REQUIRED
# Implement complete solution immediately
```

### 5. Weak Error Handling
```python
# ❌ FORBIDDEN
try:
    result = database_query()
except:
    result = []  # Return empty on any error

# ✅ REQUIRED
try:
    result = database_query()
except DatabaseConnectionError as e:
    raise RuntimeError(f"Database connection failed: {e}") from e
except QueryTimeoutError as e:
    raise RuntimeError(f"Query timed out: {e}") from e
```

## REQUIRED PATTERNS ✅

### 1. Explicit Validation
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class ClusterData(BaseModel):
    name: str = Field(..., min_length=1)
    region: str = Field(..., regex=r'^[a-z0-9-]+$')
    node_count: int = Field(..., gt=0)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Cluster name cannot be empty")
        return v.strip()
```

### 2. Explicit Error Raising
```python
def process_cluster_data(data: Dict) -> ClusterData:
    if not data:
        raise ValueError("Cluster data is required")
    
    try:
        return ClusterData(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid cluster data: {e}") from e
```

### 3. Database Operations
```python
# ❌ FORBIDDEN: Query wrong column and transform
def get_cluster_name(cluster_id: str) -> str:
    row = db.execute("SELECT display_name FROM clusters WHERE id = ?", cluster_id)
    if row and row[0]:
        return row[0]
    # Fallback to ID - BAD!
    return cluster_id

# ✅ REQUIRED: Query correct column and validate
def get_cluster_name(cluster_id: str) -> str:
    if not cluster_id:
        raise ValueError("Cluster ID is required")
    
    row = db.execute("SELECT name FROM clusters WHERE id = ?", cluster_id)
    if not row:
        raise ValueError(f"Cluster not found: {cluster_id}")
    
    name = row[0]
    if not name:
        raise ValueError(f"Cluster {cluster_id} has no name")
    
    return name
```

### 4. API Operations
```python
# ❌ FORBIDDEN: Fallback on API failure
def generate_plan(data: Dict) -> Dict:
    try:
        return claude_api.generate(data)
    except ApiError:
        return {"status": "error", "plan": []}  # BAD!

# ✅ REQUIRED: Explicit error handling
def generate_plan(data: Dict) -> ImplementationPlan:
    validate_input_data(data)
    
    try:
        response = claude_api.generate(data)
        return ImplementationPlan.parse_obj(response)
    except ApiError as e:
        raise RuntimeError(f"Plan generation failed: {e}") from e
    except ValidationError as e:
        raise ValueError(f"Invalid plan response: {e}") from e
```

## VALIDATION TOOLS

### 1. Pre-commit Hook
Automatically runs on every commit:
```bash
# Installed at .git/hooks/pre-commit
python scripts/validate_no_fallbacks.py
```

### 2. Manual Validation
Run before committing:
```bash
python scripts/validate_no_fallbacks.py
```

### 3. Configuration File
Settings in `.clauderc`:
- `allow_fallbacks: false`
- `allow_none_returns: false`
- `require_explicit_errors: true`

## DEVELOPMENT WORKFLOW

### 1. Before Writing Code
- Read this document
- Check `.clauderc` configuration
- Understand the data schema

### 2. While Writing Code
- Use Pydantic models for all data
- Validate all inputs explicitly
- Raise explicit errors
- No defensive programming

### 3. Before Committing
- Run validation script
- Fix all violations
- Test with real data
- Ensure pre-commit hook passes

### 4. Code Review Checklist
- [ ] No try-except with pass
- [ ] No Mock/Fallback classes
- [ ] No TODO/FIXME comments
- [ ] Proper Pydantic validation
- [ ] Explicit error messages
- [ ] Real data testing

## EXAMPLES OF PROPER IMPLEMENTATION

### Complete Data Flow
```python
from pydantic import BaseModel, validator
from typing import List, Dict, Any

class EnhancedClusterInput(BaseModel):
    resource_group: str = Field(..., min_length=1)
    cluster_name: str = Field(..., min_length=1)
    metrics: Dict[str, Any] = Field(...)
    
    @validator('metrics')
    def validate_metrics(cls, v):
        required_keys = ['cpu_usage', 'memory_usage', 'node_count']
        missing = [k for k in required_keys if k not in v]
        if missing:
            raise ValueError(f"Missing required metrics: {missing}")
        return v

class ImplementationStep(BaseModel):
    action: str = Field(..., min_length=1)
    resource: str = Field(..., min_length=1)
    current_value: str = Field(...)
    target_value: str = Field(...)
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['scale', 'resize', 'update', 'delete']
        if v not in valid_actions:
            raise ValueError(f"Invalid action: {v}. Must be one of {valid_actions}")
        return v

class ImplementationPlan(BaseModel):
    cluster_id: str = Field(..., min_length=1)
    steps: List[ImplementationStep] = Field(..., min_items=1)
    estimated_cost_savings: float = Field(..., ge=0)
    
    @validator('steps')
    def validate_steps(cls, v):
        if not v:
            raise ValueError("Implementation plan must have at least one step")
        return v

def generate_implementation_plan(enhanced_input: Dict) -> ImplementationPlan:
    """Generate implementation plan with full validation"""
    
    # Validate input
    try:
        validated_input = EnhancedClusterInput(**enhanced_input)
    except ValidationError as e:
        raise ValueError(f"Invalid cluster input: {e}") from e
    
    # Generate plan via API
    try:
        api_response = claude_api.generate_plan(validated_input.dict())
    except ApiConnectionError as e:
        raise RuntimeError(f"Failed to connect to plan generation API: {e}") from e
    except ApiTimeoutError as e:
        raise RuntimeError(f"Plan generation timed out: {e}") from e
    
    # Validate response
    try:
        plan = ImplementationPlan(**api_response)
    except ValidationError as e:
        raise ValueError(f"Invalid plan response from API: {e}") from e
    
    # Store in database
    try:
        store_plan_in_database(plan)
    except DatabaseError as e:
        raise RuntimeError(f"Failed to store plan: {e}") from e
    
    return plan
```

## REMEMBER

- **Fix root causes, not symptoms**
- **Fail loudly, not silently**
- **Validate everything explicitly**
- **No defensive programming**
- **Production-ready code only**

## ENFORCEMENT

This project uses:
- Pre-commit hooks (automatic)
- Validation scripts (manual)
- Code review requirements
- Configuration enforcement

**ALL CODE MUST PASS VALIDATION TO BE COMMITTED**