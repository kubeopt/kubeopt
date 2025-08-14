"""
Security API Blueprint for Flask
=================================
Flask-compatible security API endpoints
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from typing import Optional

logger = logging.getLogger(__name__)

# Create Blueprint
security_api = Blueprint('security_api', __name__, url_prefix='/api/security')

# Import security components
try:
    from app.security.security_results_manager import security_results_manager
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
            if match:
                return match.group(1)
        except:
            pass
    
    # Don't return 'default_cluster' - return None if not found
    logger.warning("No valid cluster ID found in request")
    return None

@security_api.route('/overview', methods=['GET'])
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
            
            return jsonify({
                'overall_score': security_posture.get('overall_score', 0),
                'grade': security_posture.get('grade', 'N/A'),
                'last_updated': security_results['timestamp'],
                'trend': 'stable',  # Calculate from history
                'alerts_count': policy_compliance.get('violations_count', 0),
                'critical_vulnerabilities': vulnerability_assessment.get('critical_vulnerabilities', 0),
                'compliance_percentage': analysis.get('compliance_assessment', {}).get('overall_compliance', 0),
                'scan_status': 'COMPLETED',
                'data_source': 'stored_results'
            })
        
        # Return default data if no results
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
        return jsonify({'error': str(e)}), 500

@security_api.route('/results/<cluster_id>', methods=['GET'])
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
        
        # Return default structure
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
            return jsonify([])  # Return empty array
        
        security_results = security_results_manager.get_latest_results(cluster_id)
        
        if security_results and security_results.get('analysis'):
            policy_compliance = security_results['analysis'].get('policy_compliance', {})
            violations = policy_compliance.get('violations', [])
            
            # Filter by severity if specified
            if severity:
                violations = [v for v in violations if v.get('severity') == severity.upper()]
            
            # Limit results
            violations = violations[:limit]
            
            # Format violations for frontend
            formatted_violations = []
            for v in violations:
                formatted_violations.append({
                    'violation_id': v.get('id', 'unknown'),
                    'policy_name': v.get('policy_name', 'Unknown Policy'),
                    'severity': v.get('severity', 'MEDIUM'),
                    'resource_name': v.get('resource_name', 'Unknown Resource'),
                    'namespace': v.get('namespace', 'default'),
                    'description': v.get('description', 'Policy violation detected'),
                    'remediation_steps': v.get('remediation_steps', []),
                    'auto_remediable': v.get('auto_remediable', False),
                    'detected_at': v.get('detected_at', datetime.now().isoformat())
                })
            
            return jsonify(formatted_violations)
        
        return jsonify([])  # Return empty array if no results
        
    except Exception as e:
        logger.error(f"Failed to get policy violations: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/compliance/frameworks', methods=['GET'])
def get_compliance_frameworks():
    """Get available compliance frameworks"""
    return jsonify({
        'frameworks': [
            {'id': 'CIS', 'name': 'CIS Kubernetes Benchmark', 'version': '1.6.0'},
            {'id': 'NIST', 'name': 'NIST Cybersecurity Framework', 'version': '1.1'},
            {'id': 'SOC2', 'name': 'SOC 2 Type II', 'version': '2017'},
            {'id': 'ISO27001', 'name': 'ISO/IEC 27001', 'version': '2013'}
        ]
    })

@security_api.route('/compliance/<framework>', methods=['GET'])
def get_compliance_status(framework):
    """Get compliance status for a framework"""
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
            compliance_assessment = security_results['analysis'].get('compliance_assessment', {})
            framework_data = compliance_assessment.get('frameworks', {}).get(framework.upper(), {})
            
            return jsonify({
                'framework': framework.upper(),
                'overall_compliance': framework_data.get('compliance_percentage', 0),
                'grade': framework_data.get('grade', 'N/A'),
                'passed_controls': framework_data.get('passed_controls', 0),
                'failed_controls': framework_data.get('failed_controls', 0),
                'last_assessed': security_results['timestamp']
            })
        
        # Return default data
        return jsonify({
            'framework': framework.upper(),
            'overall_compliance': 0,
            'grade': 'N/A',
            'passed_controls': 0,
            'failed_controls': 0,
            'last_assessed': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get compliance status: {e}")
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
            if severity:
                vulnerabilities = [v for v in vulnerabilities if v.get('severity') == severity.upper()]
            
            # Limit results
            vulnerabilities = vulnerabilities[:limit]
            
            return jsonify(vulnerabilities)
        
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
    """Get security trends - returns mock data for now"""
    try:
        days = int(request.args.get('days', 30))
        
        # Generate mock trend data
        import random
        from datetime import timedelta
        
        data_points = []
        current_date = datetime.now()
        
        for i in range(days):
            date = current_date - timedelta(days=days-i)
            if trend_type == 'security_score':
                value = 70 + random.randint(-10, 10)
            elif trend_type == 'vulnerability_count':
                value = 15 + random.randint(-5, 5)
            else:
                value = 50 + random.randint(-20, 20)
            
            data_points.append({
                'date': date.isoformat(),
                'value': value
            })
        
        return jsonify({
            'trend_type': trend_type,
            'current_score': data_points[-1]['value'] if data_points else 0,
            'previous_score': data_points[-7]['value'] if len(data_points) >= 7 else 0,
            'change_percentage': 5.2,
            'trend_direction': 'improving',
            'data_points': data_points
        })
        
    except Exception as e:
        logger.error(f"Failed to get security trends: {e}")
        return jsonify({'error': str(e)}), 500

@security_api.route('/audit-trail', methods=['GET'])
def get_audit_trail():
    """Get audit trail - returns empty for now"""
    return jsonify([])

@security_api.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'security_manager_available': SECURITY_MANAGER_AVAILABLE
    })