# Claude API Integration Guide

## Overview

KubeOpt now includes intelligent implementation plan generation powered by Claude API. This integration automatically creates detailed, actionable cost optimization plans after each cluster analysis.

## 🚀 Features

### ✅ What's Implemented

- **Automatic Plan Generation**: Plans are generated automatically after cost analysis
- **Intelligent Context Compacting**: Handles clusters of any size (1-1000+ workloads)
- **Smart Token Management**: Optimizes input to fit within Claude's limits
- **Robust Error Handling**: Graceful degradation when API is unavailable
- **Complete API Endpoints**: REST API for plan retrieval and management
- **Database Storage**: Persistent storage with versioning and history
- **Enhanced Validation**: Quality assessment for generated plans

### 🎯 Smart Context Optimization

| Cluster Size | Strategy | Description |
|--------------|----------|-------------|
| **Small** (<20k tokens) | Complete Data | Full cluster details for comprehensive analysis |
| **Medium** (20k-50k tokens) | Top 30 + Summary | Executive summary + 30 highest-cost workloads |
| **Large** (>50k tokens) | Top 10 + Stats | Aggregated statistics + 10 optimization targets |

## ⚙️ Setup & Configuration

### 1. Install Dependencies

```bash
pip install anthropic>=0.40.0 pydantic>=2.0.0 tiktoken>=0.5.0
```

### 2. Configure API Key

Add to your `.env` file:

```bash
# Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
MAX_CONTEXT_TOKENS=45000
```

### 3. Verify Integration

Run the integration test:

```bash
python3 test_claude_integration.py
```

Expected output with API key:
```
🚀 CLAUDE API INTEGRATION TEST SUITE
============================================================
✅ Database schema correct
✅ Context optimization working  
✅ Claude API plan generated successfully!
✅ Plan stored and retrieved correctly
```

## 🔧 Usage

### Automatic Plan Generation

Plans are generated automatically after each cluster analysis:

```python
# Analysis triggers plan generation automatically
analysis_result = run_cluster_analysis(cluster_id)

# Plan is automatically generated and stored
plan = get_latest_implementation_plan(cluster_id)
```

### Manual Plan Generation

Generate a new plan on-demand:

```python
from infrastructure.plan_generation.claude_plan_generator import ClaudePlanGenerator

# Initialize generator
generator = ClaudePlanGenerator()

# Generate plan
plan = await generator.generate_plan(
    enhanced_input=enhanced_analysis_data,
    cluster_name="production-cluster",
    cluster_id="cluster-123"
)
```

### Context Building

Understand how your cluster data is optimized:

```python
from infrastructure.plan_generation.context_builder import ContextBuilder

builder = ContextBuilder()
optimized_context = builder.build_optimized_context(
    enhanced_input=cluster_data,
    cluster_name="my-cluster"
)

print(f"Strategy: {optimized_context['context_type']}")
print(f"Token optimization: {optimized_context['token_optimization']}")
```

## 🌐 API Endpoints

### Get Latest Implementation Plan
```http
GET /api/clusters/{cluster_id}/plan
```

**Response:**
```json
{
  "status": "success",
  "plan": {
    "metadata": {
      "plan_id": "plan_cluster-123_20251018_143022",
      "cluster_name": "production-cluster",
      "generated_at": "2025-10-18T14:30:22Z"
    },
    "total_actions": 12,
    "total_monthly_savings": 2847.50,
    "phases": [...]
  }
}
```

### Get Plan History
```http
GET /api/clusters/{cluster_id}/plans?limit=10
```

### Get Specific Plan
```http
GET /api/plans/{plan_id}
```

### Generate New Plan
```http
POST /api/clusters/{cluster_id}/plan/generate
```

## 🗄️ Database Schema

### Implementation Plans Table

```sql
CREATE TABLE implementation_plans (
    plan_id TEXT PRIMARY KEY,
    cluster_id TEXT NOT NULL,
    analysis_id TEXT,
    plan_data BLOB NOT NULL,
    generated_at TEXT NOT NULL,
    total_savings REAL,
    total_actions INTEGER,
    version TEXT DEFAULT '1.0',
    generated_by TEXT,
    executed BOOLEAN DEFAULT 0,
    execution_status TEXT,
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);
```

### Storage Methods

```python
# Store a plan
plan_id = cluster_db.store_implementation_plan(
    cluster_id="cluster-123",
    plan=implementation_plan,
    analysis_id="analysis-456"
)

# Retrieve latest plan
plan = cluster_db.get_latest_plan("cluster-123")

# Get plan by ID
plan = cluster_db.get_plan_by_id("plan_cluster-123_20251018_143022")

# Get plan history
history = cluster_db.list_plans_for_cluster("cluster-123", limit=10)
```

## 🎯 Plan Structure

### Generated Plan Components

```json
{
  "metadata": {
    "plan_id": "plan_cluster-123_20251018_143022",
    "cluster_name": "production-cluster",
    "generated_at": "2025-10-18T14:30:22Z",
    "version": "1.0",
    "generated_by": "claude-api-claude-3-5-sonnet-20241022",
    "context_optimization": {
      "original_tokens": 75000,
      "optimized_tokens": 15000,
      "optimization_strategy": "aggressive_optimization",
      "reduction_percentage": 80.0
    }
  },
  "cluster_dna_analysis": {
    "overall_score": 78,
    "score_rating": "GOOD",
    "description": "Well-configured cluster with optimization opportunities"
  },
  "roi_analysis": {
    "calculation_breakdown": {
      "monthly_savings": 2847.50,
      "annual_savings": 34170.00,
      "implementation_cost": 5000.00,
      "payback_period_months": 1.8
    }
  },
  "implementation_summary": {
    "current_monthly_cost": 12500.00,
    "projected_monthly_cost": 9652.50,
    "cost_reduction_percentage": 22.8,
    "total_phases": 4
  },
  "phases": [
    {
      "phase_number": 1,
      "name": "Quick Wins",
      "description": "Immediate cost savings with minimal risk",
      "duration": "1-2 days",
      "total_savings_monthly": 425.75,
      "actions": [
        {
          "action_id": "qw-001",
          "title": "Remove Orphaned PVCs",
          "description": "Delete unused persistent volume claims",
          "monthly_savings": 125.50,
          "effort_hours": 1,
          "risk_level": "Low",
          "steps": [
            {
              "step_number": 1,
              "description": "List orphaned PVCs",
              "command": "kubectl get pvc --all-namespaces",
              "expected_outcome": "List of PVCs to review"
            }
          ],
          "rollback": {
            "description": "Restore PVC from backup if needed",
            "command": "kubectl apply -f pvc-backup.yaml"
          },
          "success_criteria": [
            "Storage costs reduced by $125.50/month",
            "No application impact"
          ]
        }
      ]
    }
  ],
  "monitoring": {
    "success_metrics": [
      "Monthly cost reduction of $2,847.50",
      "Resource utilization improvement to 60-80%"
    ],
    "tracking_commands": [
      "kubectl top nodes",
      "kubectl get hpa --all-namespaces"
    ]
  }
}
```

## 🔍 Quality Assessment

### Plan Validation

Plans are automatically validated for:

- **Schema Compliance**: Proper JSON structure and required fields
- **Business Logic**: Realistic savings estimates and risk assessments
- **Command Syntax**: Valid kubectl and Azure CLI commands
- **Dependencies**: Proper action ordering and dependencies
- **Context Quality**: Assessment based on optimization level

### Quality Metrics

```json
{
  "optimization_impact": {
    "data_reduction_percentage": 80.0,
    "plan_metrics": {
      "total_actions": 12,
      "total_monthly_savings": 2847.50,
      "average_action_savings": 237.29
    },
    "quality_indicators": {
      "command_specificity": 0.85,
      "has_rollback_procedures": 12,
      "actions_per_phase": 3.0
    }
  }
}
```

## 🚨 Error Handling

### Graceful Degradation

The system continues to work even when Claude API is unavailable:

1. **Analysis Completes**: Cost analysis always completes successfully
2. **Logging**: Clear warnings when plan generation fails
3. **Storage**: Analysis results are stored regardless of plan generation
4. **User Notification**: Users are informed about plan generation status

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `ANTHROPIC_API_KEY required` | Missing or invalid API key | Set valid API key in `.env` |
| `Plan generation failed` | API quota/rate limits | Wait and retry, check account status |
| `Context too large` | Cluster data exceeds limits | Automatic optimization handles this |
| `Invalid plan schema` | API response malformed | Automatic retry with validation |

## 📊 Performance Metrics

### Token Usage by Cluster Size

| Workloads | Original Tokens | Optimized Tokens | Reduction | Strategy |
|-----------|----------------|------------------|-----------|----------|
| 5-20 | 8k-15k | 8k-15k | 0% | Complete |
| 25-75 | 25k-40k | 15k-25k | 25-40% | Medium |
| 100+ | 60k+ | 10k-15k | 75-85% | Aggressive |

### Response Times

- **Small clusters**: 10-15 seconds
- **Medium clusters**: 15-25 seconds  
- **Large clusters**: 20-30 seconds

## 🔧 Advanced Configuration

### Custom Model Selection

```bash
# Use different Claude model
CLAUDE_MODEL=claude-3-opus-20240229

# Adjust token limits
MAX_CONTEXT_TOKENS=60000
```

### Custom Context Builder

```python
from infrastructure.plan_generation.context_builder import ContextBuilder

# Custom token limits
builder = ContextBuilder(target_token_limit=30000)

# Custom optimization thresholds
builder.small_threshold = 15000
builder.medium_threshold = 35000
```

## 🧪 Testing

### Run Full Test Suite

```bash
# Complete integration test
python3 test_claude_integration.py

# Test without API key (validates structure)
unset ANTHROPIC_API_KEY
python3 test_claude_integration.py
```

### Test Individual Components

```python
# Test context building
from infrastructure.plan_generation.context_builder import ContextBuilder
builder = ContextBuilder()
context = builder.build_optimized_context(data, "test-cluster")

# Test plan validation
from infrastructure.plan_generation.plan_validator import PlanValidator
validator = PlanValidator()
validated_plan = validator.validate(plan_json, "cluster-id", "cluster-name")
```

## 🚀 Production Deployment

### Environment Setup

1. **Secure API Key Storage**:
   ```bash
   # Use environment variables or secret management
   export ANTHROPIC_API_KEY="$(cat /secrets/claude-api-key)"
   ```

2. **Monitoring**:
   ```bash
   # Monitor plan generation success rate
   grep "Generated Claude API plan" /var/log/kubeopt.log | wc -l
   
   # Monitor API failures
   grep "Claude plan generation failed" /var/log/kubeopt.log
   ```

3. **Backup Strategy**:
   ```sql
   -- Backup implementation plans
   .backup /backups/implementation_plans_$(date +%Y%m%d).db
   ```

### Performance Tuning

```python
# Adjust for high-volume environments
ClaudePlanGenerator(
    target_token_limit=40000,  # Reduce for faster processing
    max_retries=2              # Reduce retries for faster failure
)
```

## 📈 Monitoring & Analytics

### Key Metrics to Track

1. **Plan Generation Success Rate**: `plans_generated / analyses_completed`
2. **Average Token Reduction**: Monitor optimization effectiveness
3. **API Response Times**: Track performance trends
4. **Cost Savings Accuracy**: Compare predicted vs actual savings

### Logs to Monitor

```bash
# Plan generation success
grep "Generated Claude API plan" /var/log/kubeopt.log

# Context optimization details
grep "Context optimization:" /var/log/kubeopt.log

# Validation warnings
grep "Plan validation" /var/log/kubeopt.log
```

## 🎯 Best Practices

### 1. API Key Management
- Use environment variables, not hardcoded keys
- Rotate API keys regularly
- Monitor API usage and quotas

### 2. Error Handling
- Always handle plan generation failures gracefully
- Provide meaningful error messages to users
- Log detailed errors for debugging

### 3. Performance Optimization
- Monitor token usage patterns
- Adjust context optimization thresholds based on your cluster sizes
- Cache frequently used context patterns

### 4. Quality Assurance
- Review generated plans periodically
- Validate cost savings estimates against actual results
- Monitor command syntax accuracy

## 🔄 Future Enhancements

### Planned Features
- **Plan Execution**: Automated implementation of approved plans
- **Custom Templates**: Industry-specific plan templates
- **Multi-Model Support**: Support for different AI models
- **Advanced Analytics**: Plan effectiveness tracking

### Extensibility
The architecture supports easy extension:
- Custom context builders for specific industries
- Additional validation rules for compliance
- Integration with CI/CD pipelines for automated optimization

---

## 📞 Support

For issues with Claude API integration:

1. **Check Logs**: Look for specific error messages in application logs
2. **Validate Configuration**: Ensure API key and environment are correct
3. **Test Components**: Use the integration test to isolate issues
4. **API Status**: Check Anthropic's API status page for service issues

## 📚 Additional Resources

- [Anthropic Claude API Documentation](https://docs.anthropic.com/claude/reference)
- [KubeOpt Architecture Guide](./ARCHITECTURE-GUIDE.md)
- [Cost Optimization Best Practices](./features_aks.md)
- [Production Deployment Guide](./PRODUCTION-DEPLOYMENT.md)