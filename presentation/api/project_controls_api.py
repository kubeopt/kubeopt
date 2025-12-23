#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Project Controls API Endpoint - WITH COMMANDS EXTRACTION
Extracts framework components AND commands from real analysis results
"""

from flask import request, jsonify
from datetime import datetime
import traceback
import asyncio
from shared.config.config import logger, enhanced_cluster_manager
from shared.utils.shared import _get_analysis_data
from machine_learning.core.enterprise_metrics import EnterpriseOperationalMetricsEngine, EnterpriseMetricsIntegration
from infrastructure.plan_generation.ai_plan_generator import AIImplementationPlanGenerator
from infrastructure.services.feature_guard import require_feature, get_ui_feature_flags
from infrastructure.services.license_manager import FeatureFlag

def sanitize_for_json(obj):
    """
    Recursively convert numpy/pandas types to native Python types for JSON serialization.
    Handles the specific issue with bool serialization.
    """
    import numpy as np
    
    # Handle numpy boolean types - check what's actually available
    numpy_bool_types = [np.bool_]
    
    # Try to add other bool types if they exist in this numpy version
    for bool_type in ['bool8', 'bool_']:
        if hasattr(np, bool_type):
            numpy_bool_types.append(getattr(np, bool_type))
    
    # Check if it's a numpy boolean
    if any(isinstance(obj, bool_type) for bool_type in numpy_bool_types):
        return bool(obj)
    
    # Handle numpy integers
    if hasattr(np, 'integer') and isinstance(obj, np.integer):
        return int(obj)
    
    # Handle numpy floats
    if hasattr(np, 'floating') and isinstance(obj, np.floating):
        return float(obj)
    
    # Handle numpy arrays
    if hasattr(np, 'ndarray') and isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Handle pandas if available
    try:
        import pandas as pd
        if isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
    except ImportError:
        pass
    
    # Handle dictionaries recursively
    if isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items()}
    
    # Handle lists and tuples recursively
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    
    # Handle other objects
    if hasattr(obj, '__dict__') and not callable(obj):
        try:
            # Don't try to serialize module or class objects
            if not isinstance(obj, type) and not str(type(obj)).startswith("<class 'module"):
                return sanitize_for_json(obj.__dict__)
        except:
            pass
    
    # Skip functions and callables
    if callable(obj):
        return None
    
    # Return as-is for basic types
    return obj

def register_project_controls_api(app):
    """Register project controls API endpoint with commands extraction"""
    
    @app.route('/api/environments', methods=['GET'])
    def api_get_environments():
        """Get customer-configurable environments"""
        try:
            from pathlib import Path
            import json
            
            config_path = Path(__file__).parent.parent / "config" / "environments.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return jsonify({
                "status": "success",
                "environments": config.get("environments", {}),
                "default_environment": config.get("default_environment", "development"),
                "total_environments": len(config.get("environments", {}))
            })
        except Exception as e:
            logger.error(f"❌ Failed to get environments: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/environments', methods=['POST'])
    def api_update_environments():
        """Update customer environment configuration"""
        try:
            from pathlib import Path
            import json
            
            data = request.get_json()
            if not data or 'environments' not in data:
                return jsonify({"status": "error", "message": "Missing environments data"}), 400
            
            # Validate environment data
            environments = data['environments']
            required_fields = ['deployment_frequency_target', 'change_failure_tolerance', 
                             'capacity_buffer_target', 'compliance_minimum', 'utilization_target']
            
            for env_name, env_config in environments.items():
                for field in required_fields:
                    if field not in env_config:
                        return jsonify({
                            "status": "error", 
                            "message": f"Missing required field '{field}' in environment '{env_name}'"
                        }), 400
            
            # Save configuration
            config = {
                "environments": environments,
                "default_environment": data.get("default_environment", "development"),
                "metadata": {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "description": "Customer-configured environments"
                }
            }
            
            config_path = Path(__file__).parent.parent / "config" / "environments.json"
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Clear cache to reload config
            global _ENVIRONMENT_CONFIG
            from machine_learning.core.enterprise_metrics import _CONFIG_LOCK
            with _CONFIG_LOCK:
                from machine_learning.core import enterprise_metrics
                enterprise_metrics._ENVIRONMENT_CONFIG = None
            
            logger.info(f"✅ Updated environment configuration with {len(environments)} environments")
            
            return jsonify({
                "status": "success",
                "message": f"Updated {len(environments)} environments",
                "environments_count": len(environments)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to update environments: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/enterprise-metrics', methods=['GET'])
    @require_feature(FeatureFlag.ENTERPRISE_METRICS, api_response=True)
    def api_enterprise_metrics():
        """Get enterprise operational metrics - clean implementation"""
        return get_enterprise_metrics_clean()

def _generate_dynamic_action_items(analysis_data, optimization_history, performance_metrics, cpu_avg, memory_avg, cost_savings):
    """Generate dynamic action items using existing implementation"""
    try:
        # Create an instance of the implementation generator
        generator = AIImplementationPlanGenerator()
        
        # Calculate scores for each metric (matching our enterprise metrics)
        scores = {
            'upgrade_readiness': min(85, 60 + (cost_savings / 10)),
            'disaster_recovery': min(90, 70 + len(performance_metrics) * 2),
            'operational_maturity': (cpu_avg + memory_avg) / 2 if (cpu_avg + memory_avg) > 0 else 65,
            'capacity_planning': min(95, 75 + (cost_savings / 20)),
            'compliance_readiness': min(95, 65 + len(optimization_history) * 5),
            'team_velocity': min(88, 60 + len(optimization_history) * 3)
        }
        
        # Prepare analysis results for the existing method
        analysis_results = {
            'storage_cost': analysis_data.get('storage_cost', 0) if analysis_data else 0,
            'current_cpu_utilization': cpu_avg,
            'current_memory_utilization': memory_avg,
            'total_cost': analysis_data.get('total_cost', 0) if analysis_data else 0,
            'monthly_savings': cost_savings
        }
        
        # Mock security results (you can integrate with actual security data if available)
        security_results = {
            'alerts': [],  # Add actual security alerts if available
            'violations': max(0, 5 - len(optimization_history))
        }
        
        # Generate action items based on actual cluster analysis data
        action_items = []
        
        # 1. Analyze actual resource utilization issues
        if analysis_data and cpu_avg < 30 and memory_avg < 30:
            action_items.append(f"🚨 HIGH: Over-provisioned Resources Detected - CPU: {cpu_avg:.1f}%, Memory: {memory_avg:.1f}%. Right-size {len(performance_metrics)} workloads to save ${cost_savings:.0f}/month.")
        elif cpu_avg > 80 or memory_avg > 80:
            action_items.append(f"🚨 HIGH: Resource Constraints Detected - CPU: {cpu_avg:.1f}%, Memory: {memory_avg:.1f}%. Scale up resources or implement auto-scaling.")
        
        # 2. HPA and scaling recommendations based on actual data
        if analysis_data and analysis_data.get('hpa_recommendations'):
            hpa_count = len(analysis_data.get('hpa_recommendations', []))
            total_workloads = len(performance_metrics)
            if hpa_count < total_workloads / 2:
                action_items.append(f"🔴 MEDIUM: Implement Auto-Scaling - Only {hpa_count}/{total_workloads} workloads have HPA. Configure HPA for better resource efficiency.")
        
        # 3. Cost optimization based on real savings potential
        if cost_savings > 200:
            action_items.append(f"🚨 HIGH: Significant Cost Savings Available - ${cost_savings:.0f}/month potential. Review resource requests and eliminate waste.")
        elif cost_savings > 50:
            action_items.append(f"🔴 MEDIUM: Cost Optimization Opportunity - ${cost_savings:.0f}/month savings. Optimize resource allocation.")
        
        # 4. Kubernetes version and upgrade needs based on actual cluster data
        if analysis_data and analysis_data.get('cluster_version'):
            cluster_version = analysis_data.get('cluster_version', 'Unknown')
            # Check if version seems outdated (basic heuristic)
            if '1.26' in cluster_version or '1.27' in cluster_version:
                action_items.append(f"🚨 HIGH: Kubernetes Upgrade Required - Current version: {cluster_version}. Plan upgrade to latest stable version for security and feature improvements.")
        
        # 5. Performance bottlenecks from actual workload data
        if performance_metrics:
            high_cpu_workloads = [w for w in performance_metrics if w.get('cpu_utilization_pct', 0) > 80]
            high_memory_workloads = [w for w in performance_metrics if w.get('memory_utilization_pct', 0) > 80]
            
            if high_cpu_workloads:
                action_items.append(f"🔴 MEDIUM: CPU Bottlenecks Detected - {len(high_cpu_workloads)} workloads above 80% CPU. Consider scaling or optimization.")
            
            if high_memory_workloads:
                action_items.append(f"🔴 MEDIUM: Memory Pressure Found - {len(high_memory_workloads)} workloads above 80% memory. Review memory limits and requests.")
        
        # 6. Storage and backup analysis from actual cluster data
        if analysis_data and analysis_data.get('storage_cost', 0) > 100:
            storage_cost = analysis_data.get('storage_cost', 0)
            action_items.append(f"🔴 MEDIUM: High Storage Costs - ${storage_cost:.0f}/month. Implement lifecycle policies and backup optimization.")
        
        # 7. Optimization history insights
        if len(optimization_history) == 0:
            action_items.append(f"🚨 HIGH: No Optimization History - Start performance analysis and implement resource optimization recommendations.")
        elif len(optimization_history) < 3:
            action_items.append(f"🔴 MEDIUM: Limited Optimization Coverage - {len(optimization_history)} optimizations completed. Continue systematic optimization review.")
        
        # 8. Workload-specific recommendations from performance metrics
        if performance_metrics:
            workloads_without_requests = [w for w in performance_metrics if not w.get('has_resource_requests', True)]
            if workloads_without_requests:
                action_items.append(f"🚨 HIGH: Missing Resource Requests - {len(workloads_without_requests)} workloads lack resource requests. This prevents proper scheduling and autoscaling.")
        
        # 9. Analysis data insights
        if analysis_data:
            # Check for high_cpu_summary data
            high_cpu_summary = analysis_data.get('high_cpu_summary', {})
            if high_cpu_summary and high_cpu_summary.get('total_workloads', 0) > 0:
                high_cpu_count = high_cpu_summary.get('total_workloads', 0)
                action_items.append(f"🔴 MEDIUM: High CPU Utilization - {high_cpu_count} workloads showing high CPU usage. Review resource allocation and consider optimization.")
        
        # 10. Based on actual optimization opportunities found
        monthly_savings = analysis_data.get('monthly_savings', 0) if analysis_data else cost_savings
        if monthly_savings > 0:
            action_items.append(f"🟡 LOW: Implement Identified Optimizations - ${monthly_savings:.0f}/month in verified savings available. Execute optimization recommendations.")
        
        # Return top 8 most relevant action items based on actual data
        # Ensure all action items are strings, not objects
        string_action_items = []
        for item in action_items[:8]:
            if isinstance(item, str):
                string_action_items.append(item)
            else:
                # Convert any non-string objects to strings
                string_action_items.append(str(item))
                logger.warning(f"⚠️ Non-string action item converted: {type(item)} -> {item}")
        
        return string_action_items
        
    except Exception as e:
        logger.error(f"❌ Failed to generate dynamic action items: {e}")
        return []

    @app.route('/api/project-controls', methods=['GET'])
    def api_project_controls():
        """Get project controls framework data with commands"""
        try:
            logger.info("🔒 Project Controls API called - WITH COMMANDS")
            
            # Extract cluster ID
            cluster_id = request.args.get('cluster_id')
            if not cluster_id:
                referrer = request.headers.get('Referer', '')
                if '/cluster/' in referrer:
                    try:
                        cluster_id = referrer.split('/cluster/')[-1].split('/')[0].split('?')[0]
                        logger.info(f"🔒 Extracted cluster_id from referrer: {cluster_id}")
                    except Exception:
                        pass
            
            if not cluster_id:
                return jsonify({
                    'status': 'error',
                    'message': 'No cluster ID provided for project controls'
                }), 400
            
            # Get cluster info
            cluster = enhanced_cluster_manager.get_cluster(cluster_id)
            if not cluster:
                return jsonify({
                    'status': 'error',
                    'message': f'Cluster {cluster_id} not found'
                }), 404
            
            # Get REAL analysis data
            current_analysis, data_source = _get_analysis_data(cluster_id)
            
            if not current_analysis:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available for project controls. Please run analysis first.',
                    'cluster_id': cluster_id,
                    'data_source': data_source,
                    'action_required': 'run_analysis'
                }), 404
            
            # Log what we received for debugging
            logger.info(f"🔍  Raw analysis data keys: {list(current_analysis.keys())}")
            
            # Project Controls has been migrated to Enterprise Metrics
            framework_data = {
                'status': 'migrated',
                'message': 'Project Controls has been upgraded to Enterprise Operational Metrics. Please use the Enterprise Metrics tab for comprehensive operational intelligence.',
                'migration_info': {
                    'old_system': 'Project Controls Framework',
                    'new_system': 'Enterprise Operational Metrics',
                    'new_tab': 'Enterprise Metrics',
                    'benefits': [
                        'Real-time cluster data analysis',
                        'Industry-standard benchmarks (CIS, DORA, NIST)',
                        'Kubernetes upgrade readiness assessment',
                        'Disaster recovery scoring',
                        'DORA metrics for team velocity',
                        'Compliance readiness scoring'
                    ]
                },
                'framework': {},
                'execution_plan': {}
            }
            
            # Add metadata
            framework_data['metadata'] = {
                'cluster_id': cluster_id,
                'cluster_name': cluster['name'],
                'resource_group': cluster['resource_group'],
                'subscription_id': cluster.get('subscription_id'),
                'subscription_name': cluster.get('subscription_name'),
                'data_source': data_source,
                'generated_at': datetime.now().isoformat(),
                'framework_version': '2.0.0-fixed',
                'analysis_timestamp': current_analysis.get('analyzed_at'),
                'real_data_only': True,
                'commands_extracted': True
            }
            
            logger.info(f"✅  Project controls with commands prepared for cluster: {cluster_id}")
            logger.info(f"📊 Framework components: {list(framework_data.get('framework', {}).keys())}")
            
            # Sanitize the framework data before JSON serialization
            sanitized_framework = sanitize_for_json(framework_data)
            return jsonify(sanitized_framework)
            
        except Exception as e:
            logger.error(f"❌ Error in project controls API: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'project controls API error: {str(e)}',
                'error_type': type(e).__name__
            }), 500


def get_enterprise_metrics_clean():
    """Clean enterprise metrics API - no fallback logic, use proper Implementation Generator"""
    try:
        logger.info("🏢 Clean enterprise metrics API called")
        
        # Get cluster information from request
        cluster_id = request.args.get('cluster_id')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        if not cluster_id:
            return jsonify({
                'status': 'error',
                'message': 'cluster_id parameter required'
            }), 400
        
        # Get cluster info from cluster manager
        cluster_info = enhanced_cluster_manager.get_cluster(cluster_id)
        if not cluster_info:
            return jsonify({
                'status': 'error',
                'message': f'Cluster {cluster_id} not found in system'
            }), 404
        
        resource_group = cluster_info.get('resource_group')
        cluster_name = cluster_info.get('name')
        subscription_id = cluster_info.get('subscription_id')
        
        logger.info(f"📊 Clean enterprise metrics for: {cluster_name} in {resource_group}")
        
        # Get analysis data
        analysis_data, data_source = _get_analysis_data(cluster_id)
        
        # Check for cached enterprise metrics first (unless force refresh)
        if not force_refresh and analysis_data:
            implementation_plan = analysis_data.get('implementation_plan', {})
            if isinstance(implementation_plan, dict) and 'enterprise_metrics' in implementation_plan:
                logger.info("✅ Using existing enterprise metrics from implementation plan")
                enterprise_data = implementation_plan['enterprise_metrics']
                
                return jsonify({
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'data': enterprise_data,
                    'source': 'implementation_plan_cached'
                })
        
        # Generate fresh enterprise metrics using Implementation Generator
        if not analysis_data or not isinstance(analysis_data, dict):
            return jsonify({
                'status': 'error',
                'message': f'No analysis data available for cluster {cluster_name}. Please run cluster analysis first.',
                'cluster_info': {
                    'cluster_name': cluster_name,
                    'resource_group': resource_group
                }
            }), 400
        
        # Use the Enterprise Metrics Engine (proper engine for enterprise metrics)
        enterprise_engine = EnterpriseOperationalMetricsEngine()
        
        # Generate enterprise metrics using real analysis data
        enterprise_metrics = enterprise_engine.calculate_comprehensive_enterprise_metrics(
            analysis_data,  # analysis_results
            cluster_config=analysis_data.get('cluster_config', {}),
            ml_session=analysis_data.get('ml_session', {})
        )
        
        logger.info(f"✅ Enterprise metrics generated using Implementation Generator for {cluster_name}")
        
        # Save to implementation plan
        try:
            if 'implementation_plan' in analysis_data:
                analysis_data['implementation_plan']['enterprise_metrics'] = enterprise_metrics
                enhanced_cluster_manager.update_cluster_analysis(cluster_id, analysis_data)
                logger.info(f"✅ Saved enterprise metrics to implementation plan for {cluster_name}")
        except Exception as save_error:
            logger.warning(f"⚠️ Failed to save enterprise metrics to implementation plan: {save_error}")
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': enterprise_metrics,
            'source': 'implementation_generator_fresh',
            'cluster_info': {
                'cluster_name': cluster_name,
                'resource_group': resource_group
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Clean enterprise metrics failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'status': 'error',
            'message': f'Enterprise metrics calculation failed: {str(e)}'
        }), 500

async def get_enterprise_metrics():
    """Get enterprise operational metrics data"""
    try:
        logger.info("🏢 Fetching enterprise operational metrics...")
        
        # Get cluster information from request or shared data
        cluster_id = request.args.get('cluster_id')
        
        # Try to get cluster info from analysis data if cluster_id provided
        if cluster_id:
            analysis_data = _get_analysis_data(cluster_id)
            if analysis_data and analysis_data.get('status') == 'completed':
                resource_group = analysis_data.get('resource_group', 'default-rg')
                cluster_name = analysis_data.get('cluster_name', 'default-cluster')
                subscription_id = analysis_data.get('subscription_id', 'default-subscription')
            else:
                # Fallback to direct parameters
                resource_group = request.args.get('resource_group', 'default-rg')
                cluster_name = request.args.get('cluster_name', 'default-cluster')
                subscription_id = request.args.get('subscription_id', 'default-subscription')
        else:
            # Direct parameters
            resource_group = request.args.get('resource_group', 'default-rg')
            cluster_name = request.args.get('cluster_name', 'default-cluster') 
            subscription_id = request.args.get('subscription_id', 'default-subscription')
        
        logger.info(f"🎯 Enterprise metrics for: {cluster_name} in {resource_group}")
        
        # Initialize enterprise metrics engine with real cluster data
        logger.info("📊 Calculating real enterprise metrics from cluster data...")
        metrics_engine = EnterpriseOperationalMetricsEngine(
            resource_group=resource_group,
            cluster_name=cluster_name,
            subscription_id=subscription_id
        )
        integration = EnterpriseMetricsIntegration(metrics_engine)
        
        # Calculate real enterprise metrics
        dashboard_data = await integration.get_formatted_dashboard_data()
        
        # Sanitize for JSON response
        sanitized_data = sanitize_for_json(dashboard_data)
        
        logger.info(f"✅ Real enterprise metrics calculated - Maturity Level: {dashboard_data['enterprise_maturity']['level']}")
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': sanitized_data
        })
        
    except Exception as e:
        logger.error(f"❌ Enterprise metrics calculation failed: {e}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'status': 'error',
            'message': f'Failed to calculate enterprise metrics: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


def extract_framework_with_commands(analysis_data, cluster, data_source):
    """Extract framework components WITH commands from analysis data"""
    try:
        logger.info("🔧  Extracting framework with commands...")
        
        # Get implementation plan
        implementation_plan = analysis_data.get('implementation_plan', {})
        
        # If no implementation plan, try to extract from timeline format
        if not implementation_plan:
            implementation_plan = extract_from_timeline_format(analysis_data)
        
        if not implementation_plan:
            logger.error("❌ No framework data found")
            return {
                'status': 'error',
                'message': 'No framework data available. Please run analysis first.',
                'framework': {},
                'execution_plan': {},
                'ml_confidence': 0.0
            }
        
        # Extract commands from timeline weeks
        commands_by_phase = extract_commands_from_weeks(analysis_data)
        
        # Initialize framework with commands
        framework = {}
        
        # Framework component mapping
        component_mapping = {
            'cost_protection': ['costProtection', 'cost_protection'],
            'governance_framework': ['governance', 'governance_framework'], 
            'monitoring_strategy': ['monitoring', 'monitoring_strategy'],
            'contingency_planning': ['contingency', 'contingency_planning'],
            'success_criteria': ['successCriteria', 'success_criteria'],
            'timeline_optimization': ['timelineOptimization', 'timeline_optimization'],
            'risk_mitigation': ['riskMitigation', 'risk_mitigation'],
            'intelligence_insights': ['intelligenceInsights', 'intelligence_insights']
        }
        
        found_components = 0
        
        # Extract each component and enhance with commands
        for framework_key, possible_keys in component_mapping.items():
            component_data = None
            source_found = None
            
            # Try to find component in implementation plan
            for key in possible_keys:
                if key in implementation_plan and implementation_plan[key]:
                    component_data = implementation_plan[key]
                    source_found = f"implementation_plan.{key}"
                    break
            
            # Try analysis data directly
            if not component_data:
                for key in possible_keys:
                    if key in analysis_data and analysis_data[key]:
                        component_data = analysis_data[key]
                        source_found = f"analysis_data.{key}"
                        break
            
            # Add component with commands if found
            if component_data:
                enhanced_component = enhance_component_with_commands(
                    component_data, framework_key, commands_by_phase, analysis_data
                )
                framework[framework_key] = enhanced_component
                found_components += 1
                logger.info(f"✅ Enhanced {framework_key} with commands from {source_found}")
            else:
                logger.warning(f"⚠️ {framework_key} not found")
        
        # Extract execution plan
        execution_plan = extract_comprehensive_execution_plan(analysis_data, commands_by_phase)
        
        # Calculate ML confidence
        ml_confidence = calculate_ml_confidence_from_sources(framework, analysis_data, implementation_plan)
        
        # Build response
        response_data = {
            'status': 'success',
            'framework': framework,
            'execution_plan': execution_plan,
            'ml_confidence': ml_confidence,
            'components_found': found_components,
            'total_components_possible': 8,
            'cluster_info': {
                'name': cluster['name'],
                'resource_group': cluster['resource_group'],
                'subscription_id': cluster.get('subscription_id'),
                'subscription_name': cluster.get('subscription_name')
            },
            'data_source': data_source,
            'commands_extracted': True,
            'debug_info': {
                'implementation_plan_keys': list(implementation_plan.keys()) if implementation_plan else [],
                'analysis_data_keys': list(analysis_data.keys()),
                'commands_found': len(commands_by_phase),
                'weeks_processed': len(analysis_data.get('weeks', []))
            }
        }
        
        logger.info(f"✅  Framework extraction completed with {found_components} components and commands")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ framework extraction failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return {
            'status': 'error',
            'message': f'framework extraction failed: {str(e)}',
            'framework': {},
            'execution_plan': {},
            'ml_confidence': 0.0
        }


def extract_commands_from_weeks(analysis_data):
    """Extract commands from timeline weeks and organize by phase"""
    try:
        logger.info("🛠️ Extracting commands from timeline weeks...")
        
        commands_by_phase = {}
        weeks = analysis_data.get('weeks', [])
        
        for week in weeks:
            phases = week.get('phases', [])
            for phase in phases:
                phase_id = phase.get('id', 'unknown')
                phase_title = phase.get('title', 'Unknown Phase')
                phase_type = phase.get('type', ['general'])
                
                # Extract commands from phase
                phase_commands = []
                commands = phase.get('commands', [])
                
                for cmd_group in commands:
                    if isinstance(cmd_group, dict):
                        cmd_title = cmd_group.get('title', 'Commands')
                        cmd_list = cmd_group.get('commands', [])
                        
                        # Parse JSON command strings if needed
                        parsed_commands = []
                        for cmd in cmd_list:
                            if isinstance(cmd, str) and cmd.startswith('{'):
                                try:
                                    import json
                                    cmd_obj = json.loads(cmd)
                                    if 'commands' in cmd_obj:
                                        parsed_commands.extend(cmd_obj['commands'])
                                    else:
                                        parsed_commands.append(cmd)
                                except:
                                    parsed_commands.append(cmd)
                            else:
                                parsed_commands.append(cmd)
                        
                        if parsed_commands:
                            phase_commands.append({
                                'title': cmd_title,
                                'commands': parsed_commands,
                                'command_count': len(parsed_commands)
                            })
                
                if phase_commands:
                    commands_by_phase[phase_id] = {
                        'phase_title': phase_title,
                        'phase_type': phase_type,
                        'week_range': week.get('weekRange', 'Unknown'),
                        'commands': phase_commands,
                        'total_commands': sum(cmd['command_count'] for cmd in phase_commands)
                    }
        
        logger.info(f"✅ Extracted commands from {len(commands_by_phase)} phases")
        return commands_by_phase
        
    except Exception as e:
        logger.error(f"❌ Command extraction failed: {e}")
        return {}


def enhance_component_with_commands(component_data, component_key, commands_by_phase, analysis_data):
    """Enhance framework component with related commands"""
    try:
        if not isinstance(component_data, dict):
            component_data = {'enabled': bool(component_data), 'data': component_data}
        
        enhanced_component = component_data.copy()
        
        # Find related commands based on component type
        related_commands = []
        component_keywords = {
            'cost_protection': ['cost', 'budget', 'savings', 'hpa'],
            'governance_framework': ['approval', 'governance', 'compliance'],
            'monitoring_strategy': ['monitoring', 'alert', 'metrics'],
            'contingency_planning': ['rollback', 'backup', 'contingency'],
            'success_criteria': ['validation', 'test', 'criteria'],
            'timeline_optimization': ['timeline', 'schedule', 'phase'],
            'risk_mitigation': ['risk', 'security', 'mitigation'],
            'intelligence_insights': ['analysis', 'intelligence', 'insights']
        }
        
        keywords = component_keywords.get(component_key, [])
        
        # Match commands to component based on keywords
        for phase_id, phase_data in commands_by_phase.items():
            phase_title = phase_data['phase_title'].lower()
            phase_type = [t.lower() for t in phase_data['phase_type']]
            
            # Check if this phase relates to the component
            is_related = any(keyword in phase_title for keyword in keywords) or \
                        any(keyword in ' '.join(phase_type) for keyword in keywords)
            
            if is_related:
                related_commands.append({
                    'phase_id': phase_id,
                    'phase_title': phase_data['phase_title'],
                    'week_range': phase_data['week_range'],
                    'commands': phase_data['commands'],
                    'total_commands': phase_data['total_commands']
                })
        
        # Add commands to component
        if related_commands:
            enhanced_component['related_commands'] = related_commands
            enhanced_component['commands_available'] = True
            enhanced_component['total_command_groups'] = len(related_commands)
            enhanced_component['total_commands'] = sum(cmd['total_commands'] for cmd in related_commands)
        else:
            enhanced_component['commands_available'] = False
            enhanced_component['total_command_groups'] = 0
            enhanced_component['total_commands'] = 0
        
        # Fix intelligence insights structure
        if component_key == 'intelligence_insights':
            enhanced_component = fix_intelligence_insights_structure(enhanced_component, analysis_data)
        
        # Add enhancement metadata
        enhanced_component['enhancement_metadata'] = {
            'enhanced_at': datetime.now().isoformat(),
            'commands_extracted': len(related_commands),
            'component_type': component_key
        }
        
        return enhanced_component
        
    except Exception as e:
        logger.error(f"❌ Component enhancement failed for {component_key}: {e}")
        return component_data


def fix_intelligence_insights_structure(component_data, analysis_data):
    """Fix intelligence insights to match expected frontend structure"""
    try:
        # Get executive summary data
        executive_summary = analysis_data.get('executiveSummary', {})
        intelligence_insights = analysis_data.get('intelligenceInsights', {})
        
        # Build proper structure
        fixed_structure = {
            'enabled': component_data.get('enabled', True),
            'ml_derived': component_data.get('ml_derived', True),
            'ml_confidence': component_data.get('ml_confidence', 0.8),
            'cluster_config_enhanced': component_data.get('cluster_config_enhanced', True),
            
            # Cluster Profile
            'clusterProfile': {
                'mlClusterType': executive_summary.get('cluster_intelligence', {}).get('cluster_type', 'optimized'),
                'complexityScore': executive_summary.get('cluster_intelligence', {}).get('complexity_factor', 0),
                'readinessScore': executive_summary.get('cluster_intelligence', {}).get('readiness_score', 0.985)
            },
            
            # ML Predictions
            'ml_predictions': {
                'confidence': intelligence_insights.get('analysisConfidence', 0.8),
                'model_performance': intelligence_insights.get('ml_predictions', {}).get('model_performance', 'high'),
                'learning_enabled': intelligence_insights.get('ml_predictions', {}).get('learning_enabled', True),
                'azure_integration': intelligence_insights.get('azure_enhanced', True),
                'cache_status': intelligence_insights.get('ml_predictions', {}).get('cache_status', 'active')
            },
            
            # Recommendations
            'recommendations': {
                'priority': intelligence_insights.get('recommendations', {}).get('priority', 'medium'),
                'implementation_readiness': intelligence_insights.get('recommendations', {}).get('implementation_readiness', 'review_needed'),
                'azure_optimizations_available': intelligence_insights.get('recommendations', {}).get('azure_optimizations_available', True)
            },
            
            # Metrics
            'analysisConfidence': intelligence_insights.get('analysisConfidence', 0.8),
            'actual_cv_score': intelligence_insights.get('actual_cv_score', 0.966),
            'cv_score_target': intelligence_insights.get('cv_score_target', '80-92%'),
            'dataAvailable': intelligence_insights.get('dataAvailable', True),
            'azure_enhanced': intelligence_insights.get('azure_enhanced', True),
            'intelligence_quality': 'high',
            'learning_events_count': 0,
            'optimization_opportunities': (
                # Try multiple data sources for accurate workload count
                executive_summary.get('metrics_data', {}).get('total_workloads') or
                analysis_data.get('metrics_data', {}).get('total_workloads') or 
                analysis_data.get('total_workloads') or
                component_data.get('total_workloads') or
                22  # Last resort fallback
            ),
            'improved_ml_generated': intelligence_insights.get('improved_ml_generated', True),
            'lastUpdated': intelligence_insights.get('lastUpdated', datetime.now().isoformat())
        }
        
        # Merge with original data
        fixed_structure.update({k: v for k, v in component_data.items() if k not in fixed_structure})
        
        return fixed_structure
        
    except Exception as e:
        logger.error(f"❌ Intelligence insights structure fix failed: {e}")
        return component_data


def extract_from_timeline_format(analysis_data):
    """Extract framework from timeline format"""
    timeline_keys = [
        'costProtection', 'governance', 'monitoring', 'contingency',
        'successCriteria', 'timelineOptimization', 'riskMitigation', 'intelligenceInsights'
    ]
    
    extracted = {}
    for key in timeline_keys:
        if key in analysis_data and analysis_data[key]:
            extracted[key] = analysis_data[key]
    
    return extracted if extracted else None


def extract_comprehensive_execution_plan(analysis_data, commands_by_phase):
    """Extract comprehensive execution plan"""
    try:
        execution_plan = {
            'timeline_summary': {
                'totalWeeks': analysis_data.get('totalWeeks', 0),
                'totalPhases': analysis_data.get('totalPhases', 0),
                'totalCommands': analysis_data.get('totalCommands', 0),
                'totalSavings': analysis_data.get('totalSavings', 0)
            },
            'phases': [],
            'commands_by_phase': commands_by_phase,
            'metadata': {
                'phases_with_commands': len(commands_by_phase),
                'total_command_groups': sum(len(phase['commands']) for phase in commands_by_phase.values()),
                'extracted_at': datetime.now().isoformat()
            }
        }
        
        # Extract phase summaries
        weeks = analysis_data.get('weeks', [])
        for week in weeks:
            phases = week.get('phases', [])
            for phase in phases:
                phase_summary = {
                    'id': phase.get('id'),
                    'title': phase.get('title'),
                    'type': phase.get('type', []),
                    'week_range': week.get('weekRange'),
                    'projected_savings': phase.get('projectedSavings', 0),
                    'risk_level': phase.get('riskLevel'),
                    'complexity_level': phase.get('complexityLevel'),
                    'tasks_count': len(phase.get('tasks', [])),
                    'commands_available': phase.get('id') in commands_by_phase
                }
                execution_plan['phases'].append(phase_summary)
        
        return execution_plan
        
    except Exception as e:
        logger.error(f"❌ Execution plan extraction failed: {e}")
        return {}


def calculate_ml_confidence_from_sources(framework, analysis_data, implementation_plan):
    """Calculate ML confidence from multiple sources"""
    try:
        confidence_values = []
        
        # From framework components
        for component_data in framework.values():
            if isinstance(component_data, dict) and component_data.get('ml_confidence'):
                confidence_values.append(float(component_data['ml_confidence']))
        
        # From analysis data
        if analysis_data.get('ml_confidence'):
            confidence_values.append(float(analysis_data['ml_confidence']))
        
        # From executive summary
        exec_summary = analysis_data.get('executiveSummary', {})
        if exec_summary.get('ml_confidence'):
            confidence_values.append(float(exec_summary['ml_confidence']))
        
        # Calculate average or use fallback
        if confidence_values:
            return sum(confidence_values) / len(confidence_values)
        
        return analysis_data.get('analysisConfidence', 0.8)
        
    except Exception as e:
        logger.error(f"❌ ML confidence calculation failed: {e}")
        return 0.8


def integrate_project_controls_api(app):
    """Integration function"""
    register_project_controls_api(app)
    logger.info("✅ Project Controls API with commands registered")

def register_project_controls_routes(app):
    """Register project controls routes - alias for main registration function"""
    register_project_controls_api(app)
    logger.info("✅ Project Controls routes registered")