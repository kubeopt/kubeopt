#!/usr/bin/env python3
"""
Kubernetes Dashboard Routes
============================
Route registration module for Kubernetes dashboard APIs.
Follows .clauderc principles: fail fast, no silent failures, explicit parameters.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

import logging
from flask import jsonify
from presentation.api.kubernetes_dashboard import (
    PodsDashboardAPI, 
    WorkloadsDashboardAPI, 
    ResourcesDashboardAPI
)


def register_kubernetes_routes(app, auth_decorator):
    """
    Register Kubernetes dashboard routes with the Flask application
    
    Args:
        app: Flask application instance
        auth_decorator: Authentication decorator to protect endpoints
    """
    logger = logging.getLogger(__name__)
    
    # Initialize API handlers
    pods_api = PodsDashboardAPI()
    workloads_api = WorkloadsDashboardAPI()
    resources_api = ResourcesDashboardAPI()
    
    # ============= Pods Dashboard Routes =============
    
    @app.route('/api/kubernetes/pods/<path:cluster_id>/<subscription_id>', methods=['GET'])
    @auth_decorator
    def get_pods_overview(cluster_id, subscription_id):
        """Get pods overview data for dashboard"""
        try:
            data = pods_api.get_pods_overview(cluster_id, subscription_id)
            return jsonify(data)
        except ValueError as e:
            logger.error(f"Validation error in pods overview: {e}")
            return jsonify({'error': str(e)}), 400
        except KeyError as e:
            logger.error(f"Data not found for pods overview: {e}")
            return jsonify({'error': 'Cluster data not found'}), 404
        except Exception as e:
            logger.error(f"Error getting pods overview: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    # ============= Workloads Dashboard Routes =============
    
    @app.route('/api/kubernetes/workloads/<path:cluster_id>/<subscription_id>', methods=['GET'])
    @auth_decorator
    def get_workloads_overview(cluster_id, subscription_id):
        """Get workloads overview data for dashboard"""
        try:
            data = workloads_api.get_workloads_overview(cluster_id, subscription_id)
            return jsonify(data)
        except ValueError as e:
            logger.error(f"Validation error in workloads overview: {e}")
            return jsonify({'error': str(e)}), 400
        except KeyError as e:
            logger.error(f"Data not found for workloads overview: {e}")
            return jsonify({'error': 'Cluster data not found'}), 404
        except Exception as e:
            logger.error(f"Error getting workloads overview: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    # ============= Resources Dashboard Routes =============
    
    @app.route('/api/kubernetes/resources/<path:cluster_id>/<subscription_id>', methods=['GET'])
    @auth_decorator
    def get_resources_overview(cluster_id, subscription_id):
        """Get resources overview data for dashboard"""
        try:
            data = resources_api.get_resources_overview(cluster_id, subscription_id)
            return jsonify(data)
        except ValueError as e:
            logger.error(f"Validation error in resources overview: {e}")
            return jsonify({'error': str(e)}), 400
        except KeyError as e:
            logger.error(f"Data not found for resources overview: {e}")
            return jsonify({'error': 'Cluster data not found'}), 404
        except Exception as e:
            logger.error(f"Error getting resources overview: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    # ============= Unified Dashboard Route =============
    
    @app.route('/api/kubernetes/dashboard/<path:cluster_id>/<subscription_id>', methods=['GET'])
    @auth_decorator
    def get_unified_dashboard(cluster_id, subscription_id):
        """Get all dashboard data in a single request"""
        response = {
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'data_availability': {
                'pods': False,
                'workloads': False,
                'resources': False
            },
            'errors': []
        }
        
        # Get pods data
        try:
            response['pods'] = pods_api.get_pods_overview(cluster_id, subscription_id)
            response['data_availability']['pods'] = True
        except Exception as e:
            logger.error(f"Error getting pods data: {e}")
            response['errors'].append({'component': 'pods', 'error': str(e)})
        
        # Get workloads data
        try:
            response['workloads'] = workloads_api.get_workloads_overview(cluster_id, subscription_id)
            response['data_availability']['workloads'] = True
        except Exception as e:
            logger.error(f"Error getting workloads data: {e}")
            response['errors'].append({'component': 'workloads', 'error': str(e)})
        
        # Get resources data
        try:
            response['resources'] = resources_api.get_resources_overview(cluster_id, subscription_id)
            response['data_availability']['resources'] = True
        except Exception as e:
            logger.error(f"Error getting resources data: {e}")
            response['errors'].append({'component': 'resources', 'error': str(e)})
        
        return jsonify(response)
    
    logger.info("✅ Kubernetes dashboard routes registered successfully")