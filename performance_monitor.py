#!/usr/bin/env python3
"""
Railway Performance Monitor for KubeOpt
=======================================
Performance monitoring and optimization utilities for Railway deployment.
"""

import os
import time
import psutil
import threading
from datetime import datetime
from flask import Flask, jsonify, request

class RailwayPerformanceMonitor:
    """Monitor Railway deployment performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_times = []
        self.memory_stats = []
        self.cpu_stats = []
        
    def record_request(self, start_time, end_time):
        """Record request timing"""
        duration = end_time - start_time
        self.request_times.append({
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 requests
        if len(self.request_times) > 100:
            self.request_times = self.request_times[-100:]
    
    def get_system_stats(self):
        """Get current system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_used_mb': memory.used // 1024 // 1024,
                'memory_total_mb': memory.total // 1024 // 1024,
                'memory_percent': memory.percent,
                'disk_used_gb': disk.used // 1024 // 1024 // 1024,
                'disk_total_gb': disk.total // 1024 // 1024 // 1024,
                'disk_percent': (disk.used / disk.total) * 100,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_performance_summary(self):
        """Get performance summary for Railway dashboard"""
        uptime = time.time() - self.start_time
        
        # Calculate average request time
        avg_request_time = 0
        if self.request_times:
            avg_request_time = sum(r['duration'] for r in self.request_times) / len(self.request_times)
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m",
            'total_requests': len(self.request_times),
            'avg_request_time_ms': avg_request_time * 1000,
            'system_stats': self.get_system_stats(),
            'optimization_tips': self._get_optimization_tips()
        }
    
    def _get_optimization_tips(self):
        """Get performance optimization recommendations"""
        tips = []
        system_stats = self.get_system_stats()
        
        if 'memory_percent' in system_stats and system_stats['memory_percent'] > 80:
            tips.append("High memory usage detected. Consider upgrading Railway plan.")
        
        if 'cpu_percent' in system_stats and system_stats['cpu_percent'] > 90:
            tips.append("High CPU usage detected. Consider increasing worker count.")
        
        if self.request_times:
            avg_time = sum(r['duration'] for r in self.request_times) / len(self.request_times)
            if avg_time > 2.0:
                tips.append("Slow request times detected. Check database queries and Azure API calls.")
        
        return tips

# Global performance monitor instance
performance_monitor = RailwayPerformanceMonitor()

def add_performance_monitoring(app):
    """Add performance monitoring endpoints to Flask app"""
    
    @app.before_request
    def before_request():
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            end_time = time.time()
            performance_monitor.record_request(request.start_time, end_time)
        return response
    
    @app.route('/api/performance', methods=['GET'])
    def get_performance_stats():
        """Get current performance statistics - requires authentication"""
        # Import hybrid_auth here to avoid circular imports
        try:
            from presentation.api.api_routes import hybrid_auth
            # Apply authentication decorator manually
            from functools import wraps
            from flask import jsonify
            
            # Check authentication
            from infrastructure.services.api_security import api_security
            from infrastructure.services.auth_manager import auth_manager
            
            # Check for API key authentication first
            api_key = request.headers.get('X-API-Key')
            if api_key and api_security.verify_api_key(api_key):
                pass  # Authenticated via API key
            elif auth_manager.validate_session():
                pass  # Authenticated via session
            else:
                return jsonify({'error': 'Authentication required'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Authentication system unavailable', 'details': str(e)}), 503
        
        return jsonify(performance_monitor.get_performance_summary())
    
    @app.route('/api/performance/health', methods=['GET'])
    def performance_health():
        """Quick health check for Railway monitoring - PUBLIC for Railway health checks"""
        system_stats = performance_monitor.get_system_stats()
        
        # Determine health status
        health = "healthy"
        if 'memory_percent' in system_stats and system_stats['memory_percent'] > 90:
            health = "unhealthy"
        elif 'cpu_percent' in system_stats and system_stats['cpu_percent'] > 95:
            health = "unhealthy"
        
        return jsonify({
            'status': health,
            'timestamp': datetime.now().isoformat(),
            'quick_stats': {
                'memory_percent': system_stats.get('memory_percent', 0),
                'cpu_percent': system_stats.get('cpu_percent', 0)
            }
        })

if __name__ == "__main__":
    # Test the performance monitor
    print("Railway Performance Monitor Test")
    monitor = RailwayPerformanceMonitor()
    print(monitor.get_performance_summary())