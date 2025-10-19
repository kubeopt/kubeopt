"""
KubeOpt Plan Renderer

Renders KubeOpt implementation plans as interactive HTML with the specific
structure defined in the custom schema. Optimized for template compatibility.
"""

from jinja2 import Template
from .plan_schema import KubeOptImplementationPlan, ImplementationPlanDocument
import json
from typing import Dict, Any


class KubeOptPlanRenderer:
    """Renders KubeOpt implementation plans as HTML"""
    
    def __init__(self):
        self.template = self._create_template()
    
    def render_plan(self, plan: KubeOptImplementationPlan) -> str:
        """Generate interactive HTML for the KubeOpt plan"""
        return self.template.render(
            plan=plan,
            json_data=json.dumps(plan.model_dump(), indent=2, default=str)
        )
    
    def render_plan_summary(self, plan: KubeOptImplementationPlan) -> str:
        """Generate a condensed summary view"""
        summary_template = Template(self._get_summary_template())
        return summary_template.render(plan=plan)
    
    def _create_template(self) -> Template:
        """Create the main plan template"""
        return Template(self._get_main_template())
    
    def _get_main_template(self) -> str:
        """Main HTML template for full KubeOpt plan rendering"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KubeOpt Implementation Plan - {{ plan.metadata.cluster_name }}</title>
    <style>
        :root {
            --primary-color: #0066cc;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
            --excellent-color: #28a745;
            --good-color: #20c997;
            --fair-color: #ffc107;
            --poor-color: #fd7e14;
            --gray-50: #f8f9fa;
            --gray-100: #e9ecef;
            --gray-200: #dee2e6;
            --gray-300: #ced4da;
            --gray-600: #6c757d;
            --gray-800: #343a40;
            --gray-900: #212529;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--gray-800);
            background-color: var(--gray-50);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .analysis-card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-top: 4px solid var(--primary-color);
        }
        
        .analysis-card h2 {
            color: var(--gray-900);
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .dna-score {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .dna-score .score {
            font-size: 3rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .dna-score .rating {
            font-size: 1.1rem;
            color: var(--gray-600);
            margin-top: 5px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric {
            background: var(--gray-50);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .metric .label {
            font-size: 0.9rem;
            color: var(--gray-600);
            margin-bottom: 5px;
        }
        
        .metric .value {
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .metric.excellent .value { color: var(--excellent-color); }
        .metric.good .value { color: var(--good-color); }
        .metric.fair .value { color: var(--fair-color); }
        .metric.poor .value { color: var(--poor-color); }
        
        .quality-checks {
            margin: 20px 0;
        }
        
        .quality-check {
            display: flex;
            justify-content: between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--gray-200);
        }
        
        .quality-check:last-child {
            border-bottom: none;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .status-badge.good {
            background: rgba(40, 167, 69, 0.1);
            color: var(--success-color);
        }
        
        .status-badge.warning {
            background: rgba(255, 193, 7, 0.1);
            color: var(--warning-color);
        }
        
        .status-badge.error {
            background: rgba(220, 53, 69, 0.1);
            color: var(--danger-color);
        }
        
        .roi-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .roi-metric {
            text-align: center;
            padding: 20px;
            background: var(--gray-50);
            border-radius: 8px;
        }
        
        .roi-metric .value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .roi-metric.green .value { color: var(--success-color); }
        .roi-metric.blue .value { color: var(--info-color); }
        .roi-metric.purple .value { color: #6f42c1; }
        .roi-metric.red .value { color: var(--danger-color); }
        
        .roi-metric .subtitle {
            font-size: 0.9rem;
            color: var(--gray-600);
        }
        
        .implementation-summary {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .summary-item {
            padding: 15px;
            background: var(--gray-50);
            border-radius: 8px;
        }
        
        .summary-item .label {
            font-size: 0.9rem;
            color: var(--gray-600);
            margin-bottom: 5px;
        }
        
        .summary-item .value {
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        .phases-section {
            margin: 40px 0;
        }
        
        .phase {
            background: white;
            border-radius: 12px;
            margin: 30px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .phase-header {
            background: var(--primary-color);
            color: white;
            padding: 25px 30px;
        }
        
        .phase-header h3 {
            font-size: 1.4rem;
            margin-bottom: 10px;
        }
        
        .phase-meta {
            display: flex;
            gap: 30px;
            font-size: 0.9rem;
            opacity: 0.9;
            flex-wrap: wrap;
        }
        
        .phase-content {
            padding: 0;
        }
        
        .action {
            border-bottom: 1px solid var(--gray-200);
            padding: 25px 30px;
        }
        
        .action:last-child {
            border-bottom: none;
        }
        
        .action-header {
            display: flex;
            justify-content: between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .action-title h4 {
            font-size: 1.2rem;
            color: var(--gray-900);
            margin-bottom: 5px;
        }
        
        .action-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
            color: var(--gray-600);
            flex-wrap: wrap;
        }
        
        .risk-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .risk-badge.very-low, .risk-badge.low {
            background: rgba(40, 167, 69, 0.1);
            color: var(--success-color);
        }
        
        .risk-badge.medium {
            background: rgba(255, 193, 7, 0.1);
            color: var(--warning-color);
        }
        
        .risk-badge.high, .risk-badge.critical {
            background: rgba(220, 53, 69, 0.1);
            color: var(--danger-color);
        }
        
        .action-description {
            margin: 15px 0;
            color: var(--gray-700);
        }
        
        .issue-banner {
            background: var(--gray-50);
            border-left: 4px solid var(--warning-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 6px 6px 0;
        }
        
        .issue-banner.warning {
            border-left-color: var(--warning-color);
            background: rgba(255, 193, 7, 0.05);
        }
        
        .issue-banner.info {
            border-left-color: var(--info-color);
            background: rgba(23, 162, 184, 0.05);
        }
        
        .steps-container {
            margin: 20px 0;
        }
        
        .step {
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 6px;
            margin: 10px 0;
            overflow: hidden;
        }
        
        .step-header {
            background: var(--gray-50);
            padding: 12px 15px;
            font-weight: 500;
            border-bottom: 1px solid var(--gray-200);
        }
        
        .step-command {
            background: var(--gray-900);
            color: #f8f9fa;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            overflow-x: auto;
            cursor: pointer;
            position: relative;
        }
        
        .step-command::before {
            content: "$ ";
            color: var(--success-color);
        }
        
        .step-command:hover {
            background: #2d3748;
        }
        
        .expandable {
            margin: 15px 0;
        }
        
        .expandable summary {
            cursor: pointer;
            padding: 12px;
            background: var(--gray-100);
            border-radius: 6px;
            font-weight: 500;
            outline: none;
        }
        
        .expandable summary:hover {
            background: var(--gray-200);
        }
        
        .expandable-content {
            padding: 15px;
            background: var(--gray-50);
            border-radius: 0 0 6px 6px;
        }
        
        .monitoring-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .monitoring-commands {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .monitoring-command {
            background: var(--gray-50);
            padding: 15px;
            border-radius: 6px;
        }
        
        .monitoring-command .label {
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .monitoring-command .command {
            background: var(--gray-900);
            color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.8rem;
            cursor: pointer;
        }
        
        .review-schedule {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .review-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid var(--gray-200);
        }
        
        .review-item:last-child {
            border-bottom: none;
        }
        
        .review-day {
            background: var(--primary-color);
            color: white;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 20px;
        }
        
        .json-export {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-top: 30px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .json-content {
            background: var(--gray-900);
            color: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            max-height: 400px;
            overflow: auto;
        }
        
        @media (max-width: 768px) {
            .analysis-grid {
                grid-template-columns: 1fr;
            }
            
            .roi-summary {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .phase-meta {
                flex-direction: column;
                gap: 10px;
            }
            
            .action-meta {
                flex-direction: column;
                gap: 8px;
            }
            
            .monitoring-commands {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚀 KubeOpt Implementation Plan</h1>
            <div class="subtitle">
                {{ plan.metadata.cluster_name }} • 
                Generated {{ plan.metadata.generated_date.strftime('%B %d, %Y at %H:%M UTC') }} • 
                Analysis from {{ plan.metadata.last_analyzed_display }}
            </div>
        </div>

        <!-- Analysis Overview Grid -->
        <div class="analysis-grid">
            <!-- Cluster DNA Analysis -->
            <div class="analysis-card">
                <h2>🧬 Cluster DNA Analysis</h2>
                <div class="dna-score">
                    <div class="score">{{ plan.cluster_dna_analysis.overall_score }}</div>
                    <div class="rating">{{ plan.cluster_dna_analysis.score_rating }}</div>
                </div>
                <p>{{ plan.cluster_dna_analysis.description }}</p>
                
                <div class="metrics-grid">
                    {% for metric in plan.cluster_dna_analysis.metrics %}
                    <div class="metric {{ metric.color }}">
                        <div class="label">{{ metric.label }}</div>
                        <div class="value">{{ metric.value }}%</div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Build Quality Assessment -->
            <div class="analysis-card">
                <h2>🏗️ Build Quality Assessment</h2>
                <div class="quality-checks">
                    {% for check in plan.build_quality_assessment.quality_checks %}
                    <div class="quality-check">
                        <span>{{ check.label }}</span>
                        <span class="status-badge {{ check.status_type }}">{{ check.status }}</span>
                    </div>
                    {% endfor %}
                </div>
                
                <details class="expandable">
                    <summary>📈 Best Practices Scorecard</summary>
                    <div class="expandable-content">
                        {% for score in plan.build_quality_assessment.best_practices_scorecard %}
                        <div class="metric {{ score.color }}">
                            <div class="label">{{ score.category }}</div>
                            <div class="value">{{ score.score }}/{{ score.max_score }}</div>
                        </div>
                        {% endfor %}
                    </div>
                </details>
            </div>

            <!-- ROI Analysis -->
            <div class="analysis-card">
                <h2>💰 ROI Analysis</h2>
                <div class="roi-summary">
                    {% for metric in plan.roi_analysis.summary_metrics %}
                    <div class="roi-metric {{ metric.color }}">
                        <div class="value">{{ metric.value }}</div>
                        <div class="subtitle">{{ metric.subtitle }}</div>
                    </div>
                    {% endfor %}
                </div>
                
                <details class="expandable">
                    <summary>📊 Financial Summary</summary>
                    <div class="expandable-content">
                        <ul>
                        {% for summary in plan.roi_analysis.financial_summary %}
                            <li>{{ summary }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                </details>
            </div>

            <!-- Naming Conventions -->
            <div class="analysis-card">
                <h2>📝 Naming Conventions</h2>
                <div class="dna-score">
                    <div class="score">{{ plan.naming_conventions_analysis.overall_score }}</div>
                    <div class="rating">{{ plan.naming_conventions_analysis.color.upper() }}</div>
                </div>
                
                <details class="expandable">
                    <summary>🏷️ Resource Analysis</summary>
                    <div class="expandable-content">
                        {% for resource in plan.naming_conventions_analysis.resources %}
                        <div class="quality-check">
                            <span>{{ resource.resource_type }}</span>
                            <span class="status-badge {{ resource.badge_type }}">{{ resource.compliance }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </details>
            </div>
        </div>

        <!-- Implementation Summary -->
        <div class="implementation-summary">
            <h2>📋 Implementation Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="label">Environment</div>
                    <div class="value">{{ plan.implementation_summary.environment }}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Current Cost</div>
                    <div class="value">${{ "%.2f"|format(plan.implementation_summary.current_monthly_cost) }}/month</div>
                </div>
                <div class="summary-item">
                    <div class="label">Projected Cost</div>
                    <div class="value">${{ "%.2f"|format(plan.implementation_summary.projected_monthly_cost) }}/month</div>
                </div>
                <div class="summary-item">
                    <div class="label">Cost Reduction</div>
                    <div class="value">{{ "%.1f"|format(plan.implementation_summary.cost_reduction_percentage) }}%</div>
                </div>
                <div class="summary-item">
                    <div class="label">Duration</div>
                    <div class="value">{{ plan.implementation_summary.implementation_duration }}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Risk Level</div>
                    <div class="value">{{ plan.implementation_summary.risk_level }}</div>
                </div>
            </div>
        </div>

        <!-- Implementation Phases -->
        <div class="phases-section">
            <h2>🎯 Implementation Phases</h2>
            
            {% for phase in plan.phases %}
            <div class="phase">
                <div class="phase-header">
                    <h3>Phase {{ phase.phase_number }}: {{ phase.phase_name }}</h3>
                    <div class="phase-meta">
                        <span>💰 ${{ "%.2f"|format(phase.total_savings_monthly) }}/month</span>
                        <span>⏱️ {{ phase.duration }}</span>
                        <span>📅 {{ phase.start_date }} - {{ phase.end_date }}</span>
                        <span>⚠️ {{ phase.risk_level }} Risk</span>
                        <span>🕐 {{ phase.effort_hours }}h effort</span>
                    </div>
                </div>
                
                <div class="phase-content">
                    {% for action in phase.actions %}
                    <div class="action">
                        <div class="action-header">
                            <div class="action-title">
                                <h4>{{ action.title }}</h4>
                                <div class="action-meta">
                                    <span class="risk-badge {{ action.risk.lower().replace(' ', '-') }}">{{ action.risk }} Risk</span>
                                    <span>💰 ${{ "%.2f"|format(action.savings_monthly) }}/month</span>
                                    <span>⏱️ {{ action.effort_hours }}h</span>
                                    {% if action.target_namespace %}
                                    <span>🎯 {{ action.target_namespace }}{% if action.target_resource %}/{{ action.target_resource }}{% endif %}</span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        
                        <div class="action-description">
                            {{ action.description }}
                        </div>
                        
                        {% if action.issue_text %}
                        <div class="issue-banner {{ action.issue_type }}">
                            <strong>Current Issue:</strong><br>
                            {{ action.issue_text | replace('\\n', '<br>') | safe }}
                        </div>
                        {% endif %}
                        
                        <div class="steps-container">
                            <h5>🔧 Implementation Steps</h5>
                            {% for step in action.steps %}
                            <div class="step">
                                <div class="step-header">
                                    Step {{ step.step_number }}: {{ step.label }}
                                </div>
                                <div class="step-command" onclick="copyToClipboard(this)" title="Click to copy">{{ step.command }}</div>
                                {% if step.expected_output %}
                                <div style="padding: 10px 15px; background: var(--gray-50); font-size: 0.9rem;">
                                    <strong>Expected:</strong> {{ step.expected_output }}
                                </div>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                        
                        {% if action.success_criteria %}
                        <details class="expandable">
                            <summary>✅ Success Criteria</summary>
                            <div class="expandable-content">
                                <ul>
                                {% for criteria in action.success_criteria %}
                                    <li>{{ criteria }}</li>
                                {% endfor %}
                                </ul>
                            </div>
                        </details>
                        {% endif %}
                        
                        {% if action.rollback %}
                        <details class="expandable">
                            <summary>🔄 Rollback Plan</summary>
                            <div class="expandable-content">
                                <p><strong>Description:</strong> {{ action.rollback.description }}</p>
                                <div class="step-command" onclick="copyToClipboard(this)">{{ action.rollback.command }}</div>
                            </div>
                        </details>
                        {% endif %}
                        
                        {% if action.notes %}
                        <details class="expandable">
                            <summary>📝 Notes</summary>
                            <div class="expandable-content">
                                {% for note in action.notes %}
                                <div class="note {{ note.type }}">
                                    <strong>{{ note.type.title() }}:</strong> {{ note.text }}
                                </div>
                                {% endfor %}
                            </div>
                        </details>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Monitoring Section -->
        <div class="monitoring-section">
            <h2>📊 {{ plan.monitoring.title }}</h2>
            <p>{{ plan.monitoring.description }}</p>
            
            <div class="monitoring-commands">
                {% for cmd in plan.monitoring.commands %}
                <div class="monitoring-command">
                    <div class="label">{{ cmd.label }}</div>
                    <div class="command" onclick="copyToClipboard(this)">{{ cmd.command }}</div>
                </div>
                {% endfor %}
            </div>
            
            <h3>🎯 Key Metrics to Monitor</h3>
            <div class="quality-checks">
                {% for metric in plan.monitoring.key_metrics %}
                <div class="quality-check">
                    <span>{{ metric.metric }}</span>
                    <span style="font-size: 0.9rem; color: var(--gray-600);">{{ metric.target }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Review Schedule -->
        <div class="review-schedule">
            <h2>📅 Review Schedule</h2>
            {% for review in plan.review_schedule %}
            <div class="review-item">
                <div class="review-day">{{ review.day }}</div>
                <div>{{ review.title }}</div>
            </div>
            {% endfor %}
        </div>

        <!-- JSON Export -->
        <details class="json-export">
            <summary>📄 Export as JSON</summary>
            <pre class="json-content">{{ json_data }}</pre>
        </details>
    </div>

    <script>
        function copyToClipboard(element) {
            const text = element.textContent.replace(/^\$ /, '');
            navigator.clipboard.writeText(text).then(() => {
                const original = element.style.background;
                element.style.background = 'var(--success-color)';
                setTimeout(() => {
                    element.style.background = original;
                }, 200);
            });
        }
        
        // Add click-to-copy functionality for all command elements
        document.querySelectorAll('.step-command, .monitoring-command .command').forEach(cmd => {
            cmd.style.cursor = 'pointer';
            cmd.title = 'Click to copy';
        });
    </script>
</body>
</html>
        """
    
    def _get_summary_template(self) -> str:
        """Condensed summary template"""
        return """
<div class="kubeopt-plan-summary" style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: white;">
    <h3>{{ plan.metadata.cluster_name }} - KubeOpt Implementation Plan</h3>
    <div class="summary-stats" style="display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap;">
        <span class="stat">💰 ${{ "%.2f"|format(plan.total_monthly_savings) }}/month</span>
        <span class="stat">📋 {{ plan.total_actions }} actions</span>
        <span class="stat">📊 {{ plan.phases|length }} phases</span>
        <span class="stat">🧬 DNA Score: {{ plan.cluster_dna_analysis.overall_score }}/100</span>
        <span class="stat">⏱️ {{ plan.total_effort_hours }}h effort</span>
    </div>
    <div class="roi-highlight" style="background: #f0f7ff; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>ROI Summary:</strong>
        {% for metric in plan.roi_analysis.summary_metrics %}
        {{ metric.label }}: {{ metric.value }}{% if not loop.last %} • {% endif %}
        {% endfor %}
    </div>
</div>
        """


def create_kubeopt_plan_renderer() -> KubeOptPlanRenderer:
    """Factory function to create a KubeOpt plan renderer"""
    return KubeOptPlanRenderer()