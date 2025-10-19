#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Security API Blueprint for Flask
=================================
Flask-compatible security API endpoints
"""

import json
import logging
from datetime import datetime
import traceback
from flask import Blueprint, jsonify, request, current_app
from typing import Optional

# Feature guards for security posture
from infrastructure.services.feature_guard import require_feature
from infrastructure.services.license_manager import FeatureFlag

logger = logging.getLogger(__name__)

# Create Blueprint
security_api = Blueprint('security_api', __name__, url_prefix='/api/security')

# Import security components
try:
    from infrastructure.security.security_results_manager import security_results_manager
    SECURITY_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("Security Results Manager not available")
    SECURITY_MANAGER_AVAILABLE = False
    security_results_manager = None

def get_cluster_id_from_request():
    """Extract cluster ID from request"""
    # Try from URL parameter
    cluster_id = request.args.get('cluster_id')
    
    if cluster_id and cluster_id != 'default_cluster' and cluster_id != 'null':
        return cluster_id
    
    # Try from referer URL
    referer = request.headers.get('Referer', '')
    if '/cluster/' in referer:
        try:
            # Extract cluster ID from URL path
            import re
            match = re.search(r'/cluster/([^/\?]+)', referer)
            if match is not None and match:
                return match.group(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    # Don't return 'default_cluster' - return None if not found
    logger.warning("No valid cluster ID found in request")
    return None

@security_api.route('/overview', methods=['GET'])
@require_feature(FeatureFlag.SECURITY_POSTURE, api_response=True)
def get_security_overview():
    """Get security overview"""
    try:
        cluster_id = get_cluster_id_from_request()
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({
                'error': 'Security system not available',
                'overall_score': 0,
                'grade': 'N/A',
                'last_updated': datetime.now().isoformat(),
                'trend': 'unknown',
                'alerts_count': 0,
                'critical_vulnerabilities': 0,
                'compliance_percentage': 0,
                'scan_status': 'UNAVAILABLE'
            }), 503
        
        # Get latest security results
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            analysis = security_results['analysis']
            security_posture = analysis.get('security_posture', {})
            vulnerability_assessment = analysis.get('vulnerability_assessment', {})
            policy_compliance = analysis.get('policy_compliance', {})
            
            # FIX: Properly calculate compliance from frameworks
            compliance_frameworks = analysis.get('compliance_frameworks', {})
            compliance_scores = []
            
            # Debug logging
            logger.info(f"📊 Compliance frameworks data: {compliance_frameworks}")
            
            for framework_name, framework_data in compliance_frameworks.items():
                if isinstance(framework_data, dict) and 'overall_compliance' in framework_data:
                    compliance_score = framework_data['overall_compliance']
                    compliance_scores.append(compliance_score)
                    logger.info(f"📊 {framework_name} compliance: {compliance_score}%")
            
            # Calculate average
            if compliance_scores is not None and compliance_scores:
                avg_compliance = sum(compliance_scores) / len(compliance_scores)
                logger.info(f"📊 Average compliance calculated: {avg_compliance}%")
            else:
                avg_compliance = analysis.get('compliance_assessment', {}).get('overall_compliance', 0)
                logger.warning(f"📊 No framework scores found, using fallback: {avg_compliance}%")
            
            return jsonify({
                'overall_score': security_posture.get('overall_score', 0),
                'grade': security_posture.get('grade', 'N/A'),
                'last_updated': security_results['timestamp'],
                'trend': security_posture.get('trends', {}).get('trend', 'stable'),
                'alerts_count': policy_compliance.get('violations_count', 0),
                'critical_vulnerabilities': vulnerability_assessment.get('critical_vulnerabilities', 0),
                'compliance_percentage': avg_compliance,  # This should now be ~100
                'scan_status': 'COMPLETED',
                'data_source': 'stored_results'
            })
        
        return jsonify({
            'overall_score': 0,
            'grade': 'N/A',
            'last_updated': datetime.now().isoformat(),
            'trend': 'unknown',
            'alerts_count': 0,
            'critical_vulnerabilities': 0,
            'compliance_percentage': 0,
            'scan_status': 'NO_DATA',
            'message': 'No security analysis results available. Run an analysis first.'
        })
        
    except Exception as e:
        logger.error(f"Failed to get security overview: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")  # Add traceback import at top
        return jsonify({'error': str(e)}), 500

@security_api.route('/results/<cluster_id>', methods=['GET'])
@require_feature(FeatureFlag.SECURITY_POSTURE, api_response=True)
def get_security_results(cluster_id):
    """Get stored security results for a cluster"""
    try:
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({'error': 'Security system not available'}), 503
        
        results = security_results_manager.get_latest_results(cluster_id)
        
        if not results:
            return jsonify({'error': 'No security results found for this cluster'}), 404
        
        return jsonify({
            'cluster_id': cluster_id,
            'cluster_name': results.get('cluster_name'),
            'timestamp': results.get('timestamp'),
            'analysis': results.get('analysis'),
            'metadata': results.get('metadata')
        })
        
    except Exception as e:
        logger.error(f"Failed to get security results: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/analyze/<cluster_id>', methods=['POST'])
@require_feature(FeatureFlag.SECURITY_POSTURE, api_response=True)
def trigger_security_analysis(cluster_id):
    """Trigger security analysis for a cluster"""
    try:
        # For now, return a message that analysis should be triggered through main analysis
        return jsonify({
            'message': 'Security analysis is triggered automatically with cluster analysis',
            'cluster_id': cluster_id,
            'status': 'INFO',
            'instruction': 'Run a full cluster analysis to get security results'
        })
        
    except Exception as e:
        logger.error(f"Failed to trigger security analysis: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/score/detailed', methods=['GET'])
def get_detailed_security_score():
    """Get detailed security score breakdown"""
    try:
        cluster_id = get_cluster_id_from_request()
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({'error': 'Security system not available'}), 503
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            analysis = security_results['analysis']
            security_posture = analysis.get('security_posture', {})
            
            return jsonify({
                'overall_score': security_posture.get('overall_score', 0),
                'grade': security_posture.get('grade', 'N/A'),
                'breakdown': security_posture.get('breakdown', {
                    'rbac_score': 0,
                    'network_score': 0,
                    'encryption_score': 0,
                    'vulnerability_score': 0,
                    'compliance_score': 0,
                    'drift_score': 0
                }),
                'trends': security_posture.get('trends', {}),
                'last_updated': security_results['timestamp']
            })
        
        return jsonify({
            'overall_score': 0,
            'grade': 'N/A',
            'breakdown': {
                'rbac_score': 0,
                'network_score': 0,
                'encryption_score': 0,
                'vulnerability_score': 0,
                'compliance_score': 0,
                'drift_score': 0
            },
            'trends': {},
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get detailed security score: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/policy-violations', methods=['GET'])
def get_policy_violations():
    """Get policy violations"""
    try:
        cluster_id = get_cluster_id_from_request()
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 100))
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify([])
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            policy_compliance = security_results['analysis'].get('policy_compliance', {})
            
            # Get the actual violations array
            violations = policy_compliance.get('violations', [])
            
            logger.info(f"Found {len(violations)} violations for cluster {cluster_id}")
            
            # Filter by severity if specified
            if severity is not None and severity:
                violations = [v for v in violations if v.get('severity') == severity.upper()]
            
            # Limit results
            violations = violations[:limit]
            
            # Format violations for better UI display
            formatted_violations = []
            for v in violations:
                formatted_violation = {
                    'violation_id': v.get('violation_id', 'unknown'),
                    'policy_name': v.get('policy_name', 'Unknown Policy'),
                    'severity': v.get('severity', 'UNKNOWN'),
                    'resource_name': v.get('resource_name', 'Unknown Resource'),
                    'namespace': v.get('namespace', 'default'),
                    'description': v.get('violation_description', v.get('description', 'No description available')),
                    'current_value': v.get('current_value', 'N/A'),
                    'expected_value': v.get('expected_value', 'N/A'),
                    'remediation_steps': v.get('remediation_steps', []),
                    'auto_remediable': v.get('auto_remediable', False),
                    'detected_at': v.get('detected_at', datetime.now().isoformat()),
                    'risk_score': v.get('risk_score', 0),
                    'compliance_frameworks': v.get('compliance_frameworks', []),
                    'category': v.get('policy_category', 'General'),
                    'resource_type': v.get('resource_type', 'Unknown')
                }
                formatted_violations.append(formatted_violation)
            
            return jsonify(formatted_violations)
        
        return jsonify([])
        
    except Exception as e:
        logger.error(f"Failed to get policy violations: {e}")
        return jsonify([]), 500

@security_api.route('/compliance/frameworks', methods=['GET'])
def get_compliance_frameworks():
    """Get available compliance frameworks from actual analysis"""
    try:
        cluster_id = get_cluster_id_from_request()
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({
                'frameworks': [
                    {'id': 'CIS', 'name': 'CIS Kubernetes Benchmark', 'version': '1.6.0'},
                    {'id': 'NIST', 'name': 'NIST Cybersecurity Framework', 'version': '1.1'}
                ]
            })
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            compliance_frameworks = security_results['analysis'].get('compliance_frameworks', {})
            
            # Build frameworks list from actual analyzed frameworks
            frameworks_list = []
            
            # Framework metadata mapping
            framework_metadata = {
                'CIS': {
                    'name': 'CIS Kubernetes Benchmark',
                    'version': '1.6.0',
                    'description': 'Center for Internet Security Kubernetes security benchmark'
                },
                'NIST': {
                    'name': 'NIST Cybersecurity Framework',
                    'version': '1.1',
                    'description': 'National Institute of Standards and Technology framework'
                },
                'SOC2': {
                    'name': 'SOC 2 Type II',
                    'version': '2017',
                    'description': 'Service Organization Control 2 audit standard'
                },
                'ISO27001': {
                    'name': 'ISO/IEC 27001',
                    'version': '2013',
                    'description': 'Information security management systems standard'
                },
                'PCI-DSS': {
                    'name': 'PCI Data Security Standard',
                    'version': '3.2.1',
                    'description': 'Payment Card Industry Data Security Standard'
                },
                'HIPAA': {
                    'name': 'HIPAA Security Rule',
                    'version': '2013',
                    'description': 'Health Insurance Portability and Accountability Act'
                }
            }
            
            # Get actual analyzed frameworks and their data
            for framework_id, framework_data in compliance_frameworks.items():
                framework_info = framework_metadata.get(framework_id, {
                    'name': framework_id,
                    'version': 'Unknown',
                    'description': f'{framework_id} compliance framework'
                })
                
                frameworks_list.append({
                    'id': framework_id,
                    'name': framework_info['name'],
                    'version': framework_info['version'],
                    'description': framework_info.get('description', ''),
                    'analyzed': True,
                    'compliance': framework_data.get('overall_compliance', 0),
                    'grade': framework_data.get('grade', 'N/A'),
                    'passed_controls': framework_data.get('passed_controls', 0),
                    'failed_controls': framework_data.get('failed_controls', 0),
                    'risk_level': framework_data.get('risk_level', 'UNKNOWN')
                })
            
            # Add other frameworks as "not analyzed" if you want to show them
            for framework_id, framework_info in framework_metadata.items():
                if framework_id not in compliance_frameworks:
                    frameworks_list.append({
                        'id': framework_id,
                        'name': framework_info['name'],
                        'version': framework_info['version'],
                        'description': framework_info.get('description', ''),
                        'analyzed': False,
                        'compliance': 0,
                        'grade': 'N/A',
                        'passed_controls': 0,
                        'failed_controls': 0,
                        'risk_level': 'NOT_ASSESSED'
                    })
            
            return jsonify({
                'frameworks': frameworks_list,
                'total_analyzed': len(compliance_frameworks),
                'frameworks_analyzed': list(compliance_frameworks.keys())
            })
        
        # No results found - return empty
        return jsonify({
            'frameworks': [],
            'total_analyzed': 0,
            'frameworks_analyzed': []
        })
        
    except Exception as e:
        logger.error(f"Failed to get compliance frameworks: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/compliance/<framework>', methods=['GET'])
def get_compliance_status(framework):
    """Get compliance status for a framework with full control details"""
    try:
        cluster_id = get_cluster_id_from_request()
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({
                'framework': framework.upper(),
                'overall_compliance': 0,
                'grade': 'N/A',
                'passed_controls': 0,
                'failed_controls': 0,
                'last_assessed': datetime.now().isoformat()
            })
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            compliance_frameworks = security_results['analysis'].get('compliance_frameworks', {})
            framework_data = compliance_frameworks.get(framework.upper(), {})
            
            if framework_data and isinstance(framework_data, dict) and framework_data:
                return jsonify({
                    'framework': framework.upper(),
                    'overall_compliance': framework_data.get('overall_compliance', 0),
                    'grade': framework_data.get('grade', 'N/A'),
                    'passed_controls': framework_data.get('passed_controls', 0),
                    'failed_controls': framework_data.get('failed_controls', 0),
                    'risk_level': framework_data.get('risk_level', 'UNKNOWN'),
                    'based_on_actual_controls': framework_data.get('based_on_actual_controls', False),
                    'control_details': framework_data.get('control_details', []),
                    'risk_details': framework_data.get('risk_details', {}),
                    'last_assessed': security_results['timestamp']
                })
        
        # Framework not found or not analyzed
        return jsonify({
            'framework': framework.upper(),
            'overall_compliance': 0,
            'grade': 'N/A',
            'passed_controls': 0,
            'failed_controls': 0,
            'analyzed': False,
            'last_assessed': None,
            'message': f'Framework {framework.upper()} has not been analyzed'
        })
        
    except Exception as e:
        logger.error(f"Failed to get compliance status for {framework}: {e}")
        return jsonify({'error': str(e)}), 500
    
@security_api.route('/alerts', methods=['GET'])
def get_security_alerts():
    """Get security alerts"""
    try:
        cluster_id = get_cluster_id_from_request()
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 100))
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify([])
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            security_posture = security_results['analysis'].get('security_posture', {})
            alerts = security_posture.get('alerts', [])
            
            logger.info(f"Found {len(alerts)} alerts for cluster {cluster_id}")
            
            # Filter by severity if specified
            if severity is not None and severity:
                alerts = [a for a in alerts if a.get('severity') == severity.upper()]
            
            # Limit results
            alerts = alerts[:limit]
            
            # Format alerts for better UI display
            formatted_alerts = []
            for a in alerts:
                formatted_alert = {
                    'alert_id': a.get('alert_id', 'unknown'),
                    'severity': a.get('severity', 'UNKNOWN'),
                    'category': a.get('category', 'General'),
                    'title': a.get('title', 'Security Alert'),
                    'description': a.get('description', 'No description available'),
                    'resource_type': a.get('resource_type', 'Unknown'),
                    'resource_name': a.get('resource_name', 'Unknown'),
                    'namespace': a.get('namespace', 'default'),
                    'remediation': a.get('remediation', 'No remediation guidance available'),
                    'risk_score': a.get('risk_score', 0),
                    'detected_at': a.get('detected_at', datetime.now().isoformat()),
                    'status': a.get('status', 'ACTIVE'),
                    'impact': a.get('impact', 'Unknown'),
                    'priority': a.get('priority', 'MEDIUM')
                }
                formatted_alerts.append(formatted_alert)
            
            return jsonify(formatted_alerts)
        
        return jsonify([])
        
    except Exception as e:
        logger.error(f"Failed to get security alerts: {e}")
        return jsonify([]), 500

@security_api.route('/alerts/summary', methods=['GET'])
def get_alerts_summary():
    """Get alerts summary"""
    try:
        cluster_id = get_cluster_id_from_request()
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({
                'total': 0,
                'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'by_category': {}
            })
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            security_posture = security_results['analysis'].get('security_posture', {})
            alerts = security_posture.get('alerts', [])
            
            # Calculate summary
            summary = {
                'total': len(alerts),
                'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'by_category': {}
            }
            
            for alert in alerts:
                sev = alert.get('severity', 'UNKNOWN')
                cat = alert.get('category', 'UNKNOWN')
                
                if sev in summary['by_severity']:
                    summary['by_severity'][sev] += 1
                
                if cat not in summary['by_category']:
                    summary['by_category'][cat] = 0
                summary['by_category'][cat] += 1
            
            return jsonify(summary)
        
        return jsonify({
            'total': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_category': {}
        })
        
    except Exception as e:
        logger.error(f"Failed to get alerts summary: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/vulnerabilities', methods=['GET'])
def get_vulnerabilities():
    """Get vulnerabilities"""
    try:
        cluster_id = get_cluster_id_from_request()
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 100))
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify([])
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            vulnerability_assessment = security_results['analysis'].get('vulnerability_assessment', {})
            vulnerabilities = vulnerability_assessment.get('vulnerabilities', [])
            
            # Filter by severity if specified
            if severity is not None and severity:
                vulnerabilities = [v for v in vulnerabilities if v.get('severity') == severity.upper()]
            
            # Limit results
            vulnerabilities = vulnerabilities[:limit]
            
            # Format vulnerabilities for better UI display
            formatted_vulnerabilities = []
            for v in vulnerabilities:
                formatted_vuln = {
                    'vuln_id': v.get('vuln_id', 'unknown'),
                    'cve_id': v.get('cve_id', None),
                    'title': v.get('title', 'Vulnerability'),
                    'description': v.get('description', 'No description available'),
                    'severity': v.get('severity', 'UNKNOWN'),
                    'cvss_score': v.get('cvss_score', 0.0),
                    'affected_component': v.get('affected_component', 'Unknown'),
                    'component_type': v.get('component_type', 'Unknown'),
                    'current_version': v.get('current_version', 'Unknown'),
                    'fixed_version': v.get('fixed_version', 'Not specified'),
                    'exploit_available': v.get('exploit_available', False),
                    'remediation_guidance': v.get('remediation_guidance', 'No guidance available'),
                    'detected_at': v.get('detected_at', datetime.now().isoformat()),
                    'priority_score': v.get('priority_score', 0.0),
                    'business_impact': v.get('business_impact', 'Unknown'),
                    'attack_vector': v.get('attack_vector', 'Unknown'),
                    'attack_complexity': v.get('attack_complexity', 'Unknown')
                }
                formatted_vulnerabilities.append(formatted_vuln)
            
            return jsonify(formatted_vulnerabilities)
        
        return jsonify([])
        
    except Exception as e:
        logger.error(f"Failed to get vulnerabilities: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/vulnerabilities/summary', methods=['GET'])
def get_vulnerabilities_summary():
    """Get vulnerability summary"""
    try:
        cluster_id = get_cluster_id_from_request()
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({
                'total': 0,
                'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'exploitable': 0,
                'with_cve': 0,
                'last_scan': None,
                'scan_status': 'UNAVAILABLE'
            })
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            vulnerability_assessment = security_results['analysis'].get('vulnerability_assessment', {})
            
            return jsonify({
                'total': vulnerability_assessment.get('total_vulnerabilities', 0),
                'by_severity': vulnerability_assessment.get('by_severity', {
                    'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0
                }),
                'exploitable': vulnerability_assessment.get('exploitable', 0),
                'with_cve': vulnerability_assessment.get('with_cve', 0),
                'last_scan': security_results['timestamp'],
                'scan_status': 'COMPLETED'
            })
        
        return jsonify({
            'total': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'exploitable': 0,
            'with_cve': 0,
            'last_scan': None,
            'scan_status': 'NO_DATA'
        })
        
    except Exception as e:
        logger.error(f"Failed to get vulnerability summary: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/trends/<trend_type>', methods=['GET'])
def get_security_trends(trend_type):
    """Get security trends from historical cluster analysis data"""
    try:
        cluster_id = get_cluster_id_from_request()
        days = int(request.args.get('days', 30))
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify({
                'trend_type': trend_type,
                'current_score': 0,
                'previous_score': 0,
                'change_percentage': 0,
                'trend_direction': 'unknown',
                'data_points': []
            })
        
        # Get historical security results
        history = security_results_manager.get_history(cluster_id, limit=days)
        
        data_points = []
        
        if history is not None and history:
            for result in history:
                analysis = result.get('analysis', {})
                timestamp = result.get('timestamp', datetime.now().isoformat())
                
                # Extract the requested trend value from analysis
                if trend_type == 'security_score':
                    value = analysis.get('security_posture', {}).get('overall_score', 0)
                elif trend_type == 'vulnerability_count':
                    value = analysis.get('vulnerability_assessment', {}).get('total_vulnerabilities', 0)
                elif trend_type == 'compliance_percentage':
                    # Calculate average compliance from frameworks
                    frameworks = analysis.get('compliance_frameworks', {})
                    if frameworks is not None and frameworks:
                        scores = [f.get('overall_compliance', 0) for f in frameworks.values()]
                        value = sum(scores) / len(scores) if scores else 0
                    else:
                        value = analysis.get('compliance_assessment', {}).get('overall_compliance', 0)
                elif trend_type == 'policy_violations':
                    value = analysis.get('policy_compliance', {}).get('violations_count', 0)
                elif trend_type == 'alerts_count':
                    value = len(analysis.get('security_posture', {}).get('alerts', []))
                else:
                    value = 0
                
                data_points.append({
                    'date': timestamp,
                    'value': value
                })
            
            # Sort by date
            data_points = sorted(data_points, key=lambda x: x['date'])
        
        # Calculate trend direction
        if len(data_points) >= 2:
            current_score = data_points[-1]['value']
            previous_score = data_points[-7]['value'] if len(data_points) >= 7 else data_points[0]['value']
            
            if previous_score > 0:
                change_percentage = ((current_score - previous_score) / previous_score) * 100
            else:
                change_percentage = 0
            
            # For security metrics, higher is better except for vulnerabilities and violations
            if trend_type in ['vulnerability_count', 'policy_violations', 'alerts_count']:
                # For these metrics, lower is better
                if change_percentage < -5:
                    trend_direction = 'improving'
                elif change_percentage > 5:
                    trend_direction = 'declining'
                else:
                    trend_direction = 'stable'
            else:
                # For security score and compliance, higher is better
                if change_percentage > 5:
                    trend_direction = 'improving'
                elif change_percentage < -5:
                    trend_direction = 'declining'
                else:
                    trend_direction = 'stable'
        else:
            current_score = data_points[0]['value'] if data_points else 0
            previous_score = 0
            change_percentage = 0
            trend_direction = 'stable'
        
        return jsonify({
            'trend_type': trend_type,
            'current_score': current_score,
            'previous_score': previous_score,
            'change_percentage': round(change_percentage, 1),
            'trend_direction': trend_direction,
            'data_points': data_points,
            'data_source': 'historical_analysis'
        })
        
    except Exception as e:
        logger.error(f"Failed to get security trends: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/audit-trail', methods=['GET'])
def get_audit_trail():
    """Get audit trail from actual cluster analysis"""
    try:
        cluster_id = get_cluster_id_from_request()
        event_type = request.args.get('event_type')
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 100))
        
        if not SECURITY_MANAGER_AVAILABLE:
            return jsonify([])
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            # Get audit trail from security analysis
            audit_trail = security_results['analysis'].get('audit_trail', [])
            
            # Also check for RBAC events in analysis
            rbac_analysis = security_results['analysis'].get('rbac_analysis', {})
            rbac_events = rbac_analysis.get('audit_events', [])
            
            # Get policy compliance events
            policy_compliance = security_results['analysis'].get('policy_compliance', {})
            policy_events = []
            for violation in policy_compliance.get('violations', []):
                policy_events.append({
                    'audit_id': f"POL-{violation.get('violation_id', 'unknown')}",
                    'timestamp': violation.get('detected_at', datetime.now().isoformat()),
                    'event_type': 'POLICY_VIOLATION',
                    'user': 'System',
                    'action': f"Policy violation detected: {violation.get('policy_name', 'Unknown')}",
                    'resource_name': violation.get('resource_name', 'Unknown'),
                    'resource_type': violation.get('resource_type', 'Unknown'),
                    'namespace': violation.get('namespace', 'default'),
                    'severity': violation.get('severity', 'UNKNOWN'),
                    'compliance_impact': f"Framework impact: {', '.join(violation.get('compliance_frameworks', []))}"
                })
            
            # Get vulnerability events
            vulnerability_assessment = security_results['analysis'].get('vulnerability_assessment', {})
            vuln_events = []
            for vuln in vulnerability_assessment.get('vulnerabilities', [])[:10]:  # Limit to 10 most recent
                vuln_events.append({
                    'audit_id': f"VULN-{vuln.get('vuln_id', 'unknown')}",
                    'timestamp': vuln.get('detected_at', datetime.now().isoformat()),
                    'event_type': 'VULNERABILITY_DETECTED',
                    'user': 'Security Scanner',
                    'action': f"Vulnerability detected: {vuln.get('title', 'Unknown')}",
                    'resource_name': vuln.get('affected_component', 'Unknown'),
                    'resource_type': 'Container Image',
                    'severity': vuln.get('severity', 'UNKNOWN'),
                    'cve_id': vuln.get('cve_id', 'N/A'),
                    'cvss_score': vuln.get('cvss_score', 0),
                    'compliance_impact': f"Risk Score: {vuln.get('priority_score', 0)}"
                })
            
            # Get compliance assessment events
            compliance_events = []
            for framework, data in security_results['analysis'].get('compliance_frameworks', {}).items():
                compliance_events.append({
                    'audit_id': f"COMP-{framework}",
                    'timestamp': security_results['timestamp'],
                    'event_type': 'COMPLIANCE_ASSESSMENT',
                    'user': 'Compliance Engine',
                    'action': f"{framework} compliance assessment completed",
                    'resource_name': f"{framework} Framework",
                    'resource_type': 'Compliance Framework',
                    'compliance_score': data.get('overall_compliance', 0),
                    'grade': data.get('grade', 'N/A'),
                    'passed_controls': data.get('passed_controls', 0),
                    'failed_controls': data.get('failed_controls', 0),
                    'compliance_impact': f"Overall compliance: {data.get('overall_compliance', 0)}%"
                })
            
            # Combine audit events from all sources
            all_events = audit_trail + rbac_events + policy_events + vuln_events + compliance_events
            
            # Filter by event type if specified
            if event_type is not None and event_type:
                all_events = [e for e in all_events if e.get('event_type') == event_type.upper()]
            
            # Sort by timestamp (newest first)
            all_events = sorted(all_events, key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Limit results
            all_events = all_events[:limit]
            
            logger.info(f"Found {len(all_events)} audit trail events for cluster {cluster_id}")
            
            return jsonify(all_events)
        
        return jsonify([])
        
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        return jsonify([]), 500

@security_api.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'security_manager_available': SECURITY_MANAGER_AVAILABLE
    })