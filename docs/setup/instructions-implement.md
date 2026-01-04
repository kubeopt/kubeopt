# Instructions for Claude CLI

## Context
I have a KubeOpt tool that generates implementation plans using Claude API. The plans are successfully being generated and stored in the database (confirmed by logs showing "✅ Stored implementation plan"). Now I need to integrate the implementation plan display into the unified_dashboard.html UI.

## Current State
- ✅ Backend generates implementation plans using Claude API (working)
- ✅ Plans are stored in database with format: `plan_{resource_group}_{cluster_name}_{timestamp}`
- ✅ I have a `unified_dashboard.html` file with tabs (Overview, Implementation, etc.)
- ❌ The Implementation tab is not displaying the plans (needs integration)

## Implementation Plan JSON Structure
The stored plans follow this exact JSON structure:

```json
{
  "implementation_plan": {
    "metadata": {
      "plan_id": "string",
      "cluster_name": "string",
      "generated_date": "ISO date",
      "last_analyzed_display": "string"
    },
    "cluster_dna_analysis": {
      "overall_score": number,
      "description": "string",
      "metrics": [
        {
          "label": "string",
          "value": number,
          "percentage": number,
          "rating": "string",
          "color": "excellent|good|fair|poor"
        }
      ],
      "data_sources": [
        {"name": "string", "available": boolean}
      ]
    },
    "build_quality_assessment": {
      "quality_checks": [
        {
          "label": "string",
          "status": "string",
          "status_type": "good|warning|error"
        }
      ],
      "strengths": ["string"],
      "improvements": ["string"],
      "best_practices_scorecard": [
        {
          "category": "string",
          "score": number,
          "max_score": number,
          "color": "excellent|good|fair|poor"
        }
      ]
    },
    "naming_conventions_analysis": {
      "overall_score": number,
      "max_score": number,
      "color": "string",
      "resources": [
        {
          "resource_type": "string",
          "example": "string",
          "pattern": "string",
          "compliance": "string",
          "badge_type": "success|warning"
        }
      ],
      "strengths": ["string"],
      "recommendations": ["string"]
    },
    "roi_analysis": {
      "summary_metrics": [
        {
          "label": "string",
          "value": "string",
          "subtitle": "string",
          "color": "green|blue|purple|red"
        }
      ],
      "calculation_breakdown": {
        "total_effort_hours": number,
        "hourly_rate": number,
        "implementation_cost": number,
        "monthly_savings": number,
        "annual_savings": number,
        "payback_months": number,
        "roi_percentage_year1": number
      },
      "financial_summary": ["string"],
      "savings_by_phase": [
        {
          "phase": "string",
          "duration": "string",
          "effort_hours": number,
          "monthly_savings": number,
          "annual_savings": number
        }
      ]
    },
    "implementation_summary": {
      "cluster_name": "string",
      "environment": "string",
      "location": "string",
      "kubernetes_version": "string",
      "current_monthly_cost": number,
      "projected_monthly_cost": number,
      "cost_reduction_percentage": number,
      "implementation_duration": "string",
      "total_phases": number,
      "risk_level": "string"
    },
    "phases": [
      {
        "phase_number": number,
        "phase_name": "string",
        "description": "string",
        "duration": "string",
        "start_date": "string",
        "end_date": "string",
        "total_savings_monthly": number,
        "risk_level": "string",
        "effort_hours": number,
        "actions": [
          {
            "action_id": "string",
            "title": "string",
            "description": "string",
            "savings_monthly": number,
            "risk": "string",
            "effort_hours": number,
            "issue_type": "warning|info",
            "issue_text": "string",
            "steps": [
              {
                "step_number": number,
                "label": "string",
                "command": "string",
                "expected_output": "string|null"
              }
            ],
            "notes": [
              {"type": "note", "text": "string"}
            ],
            "success_criteria": ["string"],
            "rollback": {
              "command": "string",
              "description": "string"
            }
          }
        ]
      }
    ],
    "monitoring": {
      "title": "string",
      "description": "string",
      "commands": [
        {
          "label": "string",
          "command": "string"
        }
      ],
      "key_metrics": [
        {
          "metric": "string",
          "target": "string"
        }
      ]
    },
    "review_schedule": [
      {
        "day": number,
        "title": "string"
      }
    ]
  }
}
```

## Your Tasks

### Task 1: Create Backend API Endpoint
File: `app.py` (or wherever Flask routes are defined)

Add this endpoint to retrieve implementation plans:

```python
@app.route('/api/implementation-plan/<resource_group>/<cluster_name>', methods=['GET'])
def get_implementation_plan(resource_group, cluster_name):
    """
    Fetch the latest implementation plan for a given cluster
    """
    try:
        from infrastructure.persistence.cluster_database import ClusterDatabase
        
        db = ClusterDatabase()
        cluster_key = f"{resource_group}_{cluster_name}"
        
        # Get the latest plan for this cluster
        # Based on logs, plans are stored with keys like: plan_rg-name_aks-name_timestamp
        plan_data = db.get_latest_plan(cluster_key)
        
        if not plan_data:
            return jsonify({
                'error': 'Implementation plan not found',
                'message': f'No plan available for cluster {cluster_name}'
            }), 404
        
        # If plan_data is a JSON string, parse it
        if isinstance(plan_data, str):
            import json
            plan_data = json.loads(plan_data)
        
        return jsonify(plan_data), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching implementation plan: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
```

**Note**: You may need to implement `get_latest_plan()` method in `ClusterDatabase` class if it doesn't exist. It should query the database for plans matching the cluster_key pattern and return the most recent one.

### Task 2: Create JavaScript Renderer
File: `static/js/implementation_plan_renderer.js`

Create a new file with a complete JavaScript class that:
1. Fetches the implementation plan JSON from the API endpoint
2. Renders all sections (Cluster DNA, Build Quality, Naming Conventions, ROI, Phases with commands, Monitoring, Review Schedule)
3. Includes copy-to-clipboard functionality for all command blocks
4. Handles loading states and errors
5. Uses the same green theme styling as shown in the UI mockup

Requirements:
- Main container ID: `implementation-content`
- API endpoint: `/api/implementation-plan/{resource_group}/{cluster_name}`
- Style: Green gradient theme (#7ba573, #6b9563)
- Each kubectl command should have a "Copy" button
- Progress bars for scores/metrics
- Color-coded quality checks (green=good, yellow=warning, red=error)
- Tables for naming conventions and ROI breakdown
- Collapsible sections for phases
- All styling should be inline or in the JavaScript (no external CSS dependencies)

### Task 3: Integrate into unified_dashboard.html
File: `templates/unified_dashboard.html` (or wherever the dashboard HTML is)

1. Find the Implementation tab content area
2. Ensure it has this structure:
```html
<div id="implementation-tab" class="tab-content" style="display:none;">
    <div id="implementation-content"></div>
</div>
```

3. Add the script tag before `</body>`:
```html
<script src="/static/js/implementation_plan_renderer.js"></script>
```

4. Find the tab switching function and add logic to load implementation plan:
```javascript
function showTab(tabName) {
    // existing tab switching logic...
    
    if (tabName === 'implementation') {
        // Get current selected cluster info
        const currentCluster = getCurrentSelectedCluster(); // or however you track this
        
        if (currentCluster) {
            implementationRenderer.init(
                currentCluster.resourceGroup,
                currentCluster.clusterName
            );
        }
    }
}
```

### Task 4: Add Database Method (if needed)
File: `infrastructure/persistence/cluster_database.py`

If the `get_latest_plan()` method doesn't exist in `ClusterDatabase`, add it:

```python
def get_latest_plan(self, cluster_key):
    """
    Get the latest implementation plan for a cluster
    Plans are stored with keys like: plan_{resource_group}_{cluster_name}_{timestamp}
    """
    try:
        # Find all plans for this cluster
        pattern = f"plan_{cluster_key}_*"
        matching_keys = self.redis_client.keys(pattern)
        
        if not matching_keys:
            return None
        
        # Sort by timestamp (keys are sorted lexicographically)
        latest_key = sorted(matching_keys)[-1]
        
        # Retrieve the plan data
        plan_data = self.redis_client.get(latest_key)
        
        if isinstance(plan_data, bytes):
            plan_data = plan_data.decode('utf-8')
        
        return json.loads(plan_data)
        
    except Exception as e:
        logger.error(f"Error retrieving latest plan: {str(e)}")
        return None
```

## Design Requirements

**CRITICAL**: The rendered UI should match the EXACT theme and styling I shared earlier in our conversation (the screenshot with green sidebar navigation). Reference that design for:

- **Color scheme**: Green gradient theme using #7ba573 and #6b9563 (matching the sidebar)
- **Typography**: Same font family, sizes, and weights as the existing dashboard
- **Spacing**: Match the padding, margins, and gaps from the existing UI
- **Layout**: Align with the existing dashboard structure and tab content styling
- **Section headers**: Same divider style (horizontal gradient line) as shown in the screenshot
- **Command blocks**: Light gray background (#f8f9fa) with green Copy buttons matching the theme
- **Info/Warning boxes**: Green info boxes (#e8f5e9) and yellow warning boxes (#fff3cd) with left border accent

Specific elements to match:
- **Sections**: Header with rocket icon, Cluster DNA Score (purple gradient card), Build Quality checks, Naming table, ROI metrics, Implementation Summary, Phases with commands, Monitoring commands, Review schedule
- **Interactive elements**: Copy buttons for all commands, progress bars for scores
- **Responsive**: Should work on different screen sizes
- **Copy button behavior**: Change to "Copied!" in green for 2 seconds after clicking
- **Green theme consistency**: All primary actions, progress bars, and accent colors should use the green palette from the existing dashboard

The implementation tab should feel like a seamless part of the existing dashboard, not a separate component. Match the existing design language exactly.

## Testing Instructions

After implementation, test with these steps:

1. **Test API endpoint**:
```bash
curl http://localhost:5000/api/implementation-plan/rg-dpl-mad-dev-ne2-2/aks-dpl-mad-dev-ne2-1
```
Should return JSON with implementation_plan structure.

2. **Test frontend**:
- Open unified_dashboard.html
- Select a cluster that has a plan generated
- Switch to Implementation tab
- Should see loading spinner, then rendered plan
- Click Copy button on any command - should copy to clipboard

3. **Check browser console**: No errors should appear

## Important Notes

- The plans are already being generated successfully (logs confirm this)
- Use the EXACT JSON structure provided above
- Match the styling from the mockup (green theme, progress bars, tables)
- All kubectl commands must have working Copy buttons
- Handle loading and error states gracefully
- The old implementation plan generator code was deleted, so build this integration from scratch

## Expected Result

When complete, clicking the Implementation tab should display a beautiful, formatted implementation plan with:
- Overall DNA score in a purple gradient card
- Quality checks with color-coded badges
- Naming conventions table
- ROI analysis with savings breakdown
- All 4 phases with step-by-step kubectl commands
- Copy buttons that work on all commands
- Monitoring commands and review schedule

The UI should match the design shown in the mockup with the green theme and clean, professional styling.

---

Please implement all 4 tasks above, ensuring the integration works properly with the existing codebase structure.