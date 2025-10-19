"""
from pydantic import BaseModel, Field, validator
Plan Renderer

Renders implementation plans as interactive HTML with modern styling.
Provides clear visualization of execution phases, actions, and commands.
"""

from jinja2 import Template
from .plan_schema import KubeOptImplementationPlan
import json
from typing import Dict, Any


class PlanRenderer:
    """Renders implementation plans as HTML"""
    
    def __init__(self):
        self.template = self._create_template()
    
    def render_plan(self, plan: KubeOptImplementationPlan) -> str:
        """Generate interactive HTML for the plan"""
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
        """Main HTML template for full plan rendering"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Implementation Plan - {{ plan.cluster_name }}</title>
    <style>
        :root {
            --primary-color: #0078d4;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-600: #4b5563;
            --gray-800: #1f2937;
            --gray-900: #111827;
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
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: var(--gray-900);
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: var(--gray-600);
            font-size: 1.1rem;
        }
        
        .executive-summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .executive-summary h2 {
            font-size: 1.8rem;
            margin-bottom: 20px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        
        .summary-card .label {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .summary-card .value {
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .savings {
            color: var(--success-color);
            font-weight: bold;
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
            padding: 20px 30px;
            border-left: 6px solid rgba(255, 255, 255, 0.3);
        }
        
        .phase-header h2 {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }
        
        .phase-meta {
            display: flex;
            gap: 30px;
            margin-top: 10px;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .phase-content {
            padding: 0;
        }
        
        .action {
            border-bottom: 1px solid var(--gray-200);
            padding: 25px 30px;
            transition: background-color 0.2s;
        }
        
        .action:last-child {
            border-bottom: none;
        }
        
        .action:hover {
            background-color: var(--gray-50);
        }
        
        .action.low-risk {
            border-left: 4px solid var(--success-color);
        }
        
        .action.medium-risk {
            border-left: 4px solid var(--warning-color);
        }
        
        .action.high-risk {
            border-left: 4px solid var(--danger-color);
        }
        
        .action-header {
            display: flex;
            justify-content: between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .action-title {
            flex: 1;
        }
        
        .action-title h3 {
            font-size: 1.2rem;
            color: var(--gray-900);
            margin-bottom: 5px;
        }
        
        .action-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
            color: var(--gray-600);
        }
        
        .risk-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .risk-badge.low {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success-color);
        }
        
        .risk-badge.medium {
            background: rgba(245, 158, 11, 0.1);
            color: var(--warning-color);
        }
        
        .risk-badge.high {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger-color);
        }
        
        .action-description {
            margin: 15px 0;
            color: var(--gray-700);
        }
        
        .action-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .detail-group h4 {
            font-size: 0.9rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .detail-value {
            font-weight: 500;
        }
        
        .command {
            background: var(--gray-900);
            color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            margin: 10px 0;
            overflow-x: auto;
            position: relative;
        }
        
        .command::before {
            content: "$ ";
            color: var(--success-color);
        }
        
        .command-section {
            margin: 20px 0;
        }
        
        .command-section h4 {
            margin-bottom: 10px;
            color: var(--gray-700);
        }
        
        .expandable {
            margin: 15px 0;
        }
        
        .expandable summary {
            cursor: pointer;
            padding: 10px;
            background: var(--gray-100);
            border-radius: 6px;
            font-weight: 500;
            outline: none;
        }
        
        .expandable summary:hover {
            background: var(--gray-200);
        }
        
        .expandable-content {
            padding: 15px 10px;
            background: var(--gray-50);
            border-radius: 0 0 6px 6px;
        }
        
        .recommendations {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-top: 30px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .recommendations h3 {
            color: var(--gray-900);
            margin-bottom: 15px;
        }
        
        .recommendations ol {
            padding-left: 20px;
        }
        
        .recommendations li {
            margin: 8px 0;
            color: var(--gray-700);
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
            .summary-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .phase-meta {
                flex-direction: column;
                gap: 10px;
            }
            
            .action-details {
                grid-template-columns: 1fr;
            }
            
            .action-meta {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚀 Implementation Plan</h1>
            <div class="subtitle">{{ plan.cluster_name }} • Generated {{ plan.generated_at.strftime('%B %d, %Y at %H:%M UTC') }}</div>
        </div>

        <!-- Executive Summary -->
        <div class="executive-summary">
            <h2>💡 Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="label">Total Potential Savings</div>
                    <div class="value">${{ "%.2f"|format(plan.executive_summary.total_potential_savings) }}/month</div>
                </div>
                <div class="summary-card">
                    <div class="label">Annual Savings</div>
                    <div class="value">${{ "%.2f"|format(plan.executive_summary.annual_savings) }}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Total Actions</div>
                    <div class="value">{{ plan.executive_summary.total_actions }}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Implementation Timeline</div>
                    <div class="value">{{ plan.executive_summary.implementation_timeline }}</div>
                </div>
            </div>
            
            <div class="recommendations">
                <h3>🎯 Top 3 Recommendations</h3>
                <ol>
                {% for rec in plan.executive_summary.top_3_recommendations %}
                    <li>{{ rec }}</li>
                {% endfor %}
                </ol>
            </div>
        </div>

        <!-- Phases -->
        {% for phase in plan.phases %}
        <div class="phase">
            <div class="phase-header">
                <h2>Phase {{ phase.phase_number }}: {{ phase.phase_name }}</h2>
                <div class="phase-meta">
                    <span>💰 Savings: ${{ "%.2f"|format(phase.total_estimated_savings) }}/month</span>
                    <span>⏱️ Time: {{ phase.total_implementation_time }}</span>
                    <span>📋 Actions: {{ phase.actions|length }}</span>
                </div>
            </div>
            
            <div class="phase-content">
                <div style="padding: 20px 30px; background: var(--gray-50); border-bottom: 1px solid var(--gray-200);">
                    <p>{{ phase.description }}</p>
                </div>
                
                {% for action in phase.actions %}
                <div class="action {{ action.risk_level }}-risk">
                    <div class="action-header">
                        <div class="action-title">
                            <h3>{{ action.title }}</h3>
                            <div class="action-meta">
                                <span class="risk-badge {{ action.risk_level }}">{{ action.risk_level }} risk</span>
                                <span>💰 ${{ "%.2f"|format(action.estimated_monthly_savings) }}/month</span>
                                <span>⏱️ {{ action.estimated_implementation_time }}</span>
                                <span>🎯 {{ action.target.namespace }}/{{ action.target.name }}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="action-description">
                        {{ action.description }}
                    </div>
                    
                    <div class="action-details">
                        <div class="detail-group">
                            <h4>Financial Impact</h4>
                            <div class="detail-value">
                                Monthly: <span class="savings">${{ "%.2f"|format(action.estimated_monthly_savings) }}</span><br>
                                Annual: <span class="savings">${{ "%.2f"|format(action.estimated_annual_savings) }}</span><br>
                                ROI: {{ "%.1f"|format(action.roi_months) }} months
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <h4>Target Resource</h4>
                            <div class="detail-value">
                                Type: {{ action.target.resource_type }}<br>
                                Namespace: {{ action.target.namespace }}<br>
                                Name: {{ action.target.name }}
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <h4>Execution Details</h4>
                            <div class="detail-value">
                                Priority: {{ action.priority }}<br>
                                Downtime: {% if action.requires_downtime %}Required{% else %}Not required{% endif %}<br>
                                Dependencies: {{ action.dependencies|length or "None" }}
                            </div>
                        </div>
                    </div>

                    <div class="command-section">
                        <h4>🔧 Commands to Execute</h4>
                        {% for cmd in action.commands %}
                        {% if cmd.kubectl_command %}
                        <div class="command">{{ cmd.kubectl_command }}</div>
                        {% endif %}
                        {% if cmd.azure_cli_command %}
                        <div class="command">{{ cmd.azure_cli_command }}</div>
                        {% endif %}
                        <p style="margin-top: 5px; color: var(--gray-600); font-size: 0.9rem;">{{ cmd.description }}</p>
                        {% endfor %}
                    </div>

                    <details class="expandable">
                        <summary>🔍 Validation & Rollback</summary>
                        <div class="expandable-content">
                            <h4>Validation Check</h4>
                            <div class="command">{{ action.validation.command }}</div>
                            <p><strong>Expected Result:</strong> {{ action.validation.expected_result }}</p>
                            <p><strong>Wait Time:</strong> {{ action.validation.wait_time }}</p>
                            
                            <h4 style="margin-top: 20px;">Rollback Plan</h4>
                            <p><strong>Estimated Time:</strong> {{ action.rollback.estimated_time }}</p>
                            <ol>
                            {% for step in action.rollback.steps %}
                                <li>{{ step }}</li>
                            {% endfor %}
                            </ol>
                            
                            {% if action.rollback.kubectl_commands %}
                            <h5>Rollback Commands:</h5>
                            {% for cmd in action.rollback.kubectl_commands %}
                            <div class="command">{{ cmd }}</div>
                            {% endfor %}
                            {% endif %}
                        </div>
                    </details>

                    {% if action.risk_factors %}
                    <details class="expandable">
                        <summary>⚠️ Risk Assessment</summary>
                        <div class="expandable-content">
                            <h4>Risk Factors</h4>
                            <ul>
                            {% for risk in action.risk_factors %}
                                <li>{{ risk }}</li>
                            {% endfor %}
                            </ul>
                            
                            <h4>Mitigation Steps</h4>
                            <ul>
                            {% for step in action.mitigation_steps %}
                                <li>{{ step }}</li>
                            {% endfor %}
                            </ul>
                        </div>
                    </details>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}

        <!-- JSON Export -->
        <details class="json-export">
            <summary>📄 Export as JSON</summary>
            <pre class="json-content">{{ json_data }}</pre>
        </details>
    </div>

    <script>
        // Add click-to-copy functionality for commands
        document.querySelectorAll('.command').forEach(cmd => {
            cmd.style.cursor = 'pointer';
            cmd.title = 'Click to copy';
            cmd.addEventListener('click', () => {
                navigator.clipboard.writeText(cmd.textContent.replace('$ ', ''));
                
                // Visual feedback
                const original = cmd.style.background;
                cmd.style.background = 'var(--success-color)';
                setTimeout(() => {
                    cmd.style.background = original;
                }, 200);
            });
        });
    </script>
</body>
</html>
        """
    
    def _get_summary_template(self) -> str:
        """Condensed summary template"""
        return """
<div class="plan-summary">
    <h3>{{ plan.cluster_name }} - Implementation Plan</h3>
    <div class="summary-stats">
        <span class="stat">💰 ${{ "%.2f"|format(plan.estimated_total_savings_monthly) }}/month</span>
        <span class="stat">📋 {{ plan.total_actions }} actions</span>
        <span class="stat">📊 {{ plan.phases|length }} phases</span>
    </div>
    <div class="top-actions">
        <h4>Top 3 Recommendations:</h4>
        <ol>
        {% for rec in plan.executive_summary.top_3_recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ol>
    </div>
</div>
        """


def create_plan_renderer() -> PlanRenderer:
    """Factory function to create a plan renderer"""
    return PlanRenderer()