#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Security Dashboard API for AKS Security Posture
==============================================
FastAPI endpoints providing real-time security data to the frontend.
Integrates with all security components for comprehensive dashboard.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import security components
from .security_posture_core import create_security_posture_engine, SecurityScore, SecurityAlert
from .policy_analyzer import create_policy_analyzer, PolicyViolation, GovernanceReport
from .compliance_framework import create_compliance_framework_engine, AuditReport, ComplianceHeatmap
from .vulnerability_scanner import create_vulnerability_scanner, Vulnerability, ScanResult
from infrastructure.security.security_results_manager import security_results_manager

logger = logging.getLogger(__name__)

# Pydantic models for API responses
class SecurityOverviewResponse(BaseModel):
    """Security overview response model"""
    overall_score: float
    grade: str
    last_updated: datetime
    trend: str
    alerts_count: int
    critical_vulnerabilities: int
    compliance_percentage: float
    scan_status: str

class PolicyViolationResponse(BaseModel):
    """Policy violation response model"""
    violation_id: str
    policy_name: str
    severity: str
    resource_name: str
    namespace: str
    description: str
    remediation_steps: List[str]
    auto_remediable: bool
    detected_at: datetime

class ComplianceStatusResponse(BaseModel):
    """Compliance status response model"""
    framework: str
    overall_compliance: float
    grade: str
    passed_controls: int
    failed_controls: int
    last_assessed: datetime

class VulnerabilityResponse(BaseModel):
    """Vulnerability response model"""
    vuln_id: str
    cve_id: Optional[str]
    title: str
    severity: str
    cvss_score: float
    affected_component: str
    exploit_available: bool
    remediation_guidance: str
    detected_at: datetime

class SecurityTrendsResponse(BaseModel):
    """Security trends response model"""
    trend_type: str
    current_score: float
    previous_score: float
    change_percentage: float
    trend_direction: str
    data_points: List[Dict[str, Any]]

class AuditTrailResponse(BaseModel):
    """Audit trail response model"""
    audit_id: str
    timestamp: datetime
    event_type: str
    user: str
    action: str
    resource_name: str
    compliance_impact: str

class SecurityDashboardAPI:
    """
    Security Dashboard API providing comprehensive security data
    """
    
    def __init__(self, cluster_config: Dict):
        """Initialize Security Dashboard API"""
        self.cluster_config = cluster_config
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="AKS Security Posture Dashboard API",
            description="Comprehensive security, compliance, and vulnerability management API",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize security components
        self._initialize_security_components()
        
        # Setup API routes
        self._setup_routes()
        
        # Background tasks
        self._setup_background_tasks()
        
        logger.info("🔐 Security Dashboard API initialized")
    
    def _initialize_security_components(self):
        """Initialize all security analysis components"""
        
        try:
            self.security_engine = create_security_posture_engine(self.cluster_config)
            self.policy_analyzer = create_policy_analyzer(self.cluster_config)
            self.compliance_engine = create_compliance_framework_engine(self.cluster_config)
            self.vulnerability_scanner = create_vulnerability_scanner(self.cluster_config)
            
            logger.info("✅ All security components initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize security components: {e}")
            raise
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Security Overview Routes
        @self.app.get("/api/security/overview", response_model=SecurityOverviewResponse)
        async def get_security_overview(self):
            """Get comprehensive security overview from latest analysis"""
            try:
                # Get cluster ID from request context or session
                cluster_id = self._get_current_cluster_id()
                
                # Get latest security results
                security_results = security_results_manager.get_latest_results(cluster_id)
                
                if security_results and security_results.get('analysis'):
                    analysis = security_results['analysis']
                    
                    # Extract real data from stored results
                    security_posture = analysis.get('security_posture', {})
                    vulnerability_assessment = analysis.get('vulnerability_assessment', {})
                    policy_compliance = analysis.get('policy_compliance', {})
                    
                    return SecurityOverviewResponse(
                        overall_score=security_posture.get('overall_score', 0),
                        grade=security_posture.get('grade', 'N/A'),
                        last_updated=datetime.fromisoformat(security_results['timestamp']),
                        trend=self._calculate_trend(cluster_id),
                        alerts_count=policy_compliance.get('violations_count', 0),
                        critical_vulnerabilities=vulnerability_assessment.get('critical_vulnerabilities', 0),
                        compliance_percentage=analysis.get('compliance_assessment', {}).get('overall_compliance', 0),
                        scan_status='COMPLETED'
                    )
                
                # Fallback to live analysis if no stored results
                return await self._perform_live_analysis()
                
            except Exception as e:
                logger.error(f"Failed to get security overview: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/security/score/detailed")
        async def get_detailed_security_score(self):
            """Get detailed security score breakdown from stored results"""
            try:
                cluster_id = self._get_current_cluster_id()
                security_results = security_results_manager.get_latest_results(cluster_id)
                
                if security_results and security_results.get('analysis'):
                    analysis = security_results['analysis']
                    security_posture = analysis.get('security_posture', {})
                    
                    return {
                        "overall_score": security_posture.get('overall_score', 0),
                        "grade": security_posture.get('grade', 'N/A'),
                        "breakdown": security_posture.get('breakdown', {}),
                        "trends": security_posture.get('trends', {}),
                        "last_updated": security_results['timestamp'],
                        "data_source": "stored_analysis",
                        "cluster_name": security_results.get('cluster_name', 'Unknown')
                    }
                
                # Fallback
                return await self._get_live_security_score()
                
            except Exception as e:
                logger.error(f"Failed to get detailed security score: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Policy Violations Routes
        @self.app.get("/api/security/policy-violations", response_model=List[PolicyViolationResponse])
        async def get_policy_violations(self, severity: Optional[str] = None, limit: int = 100):
            """Get policy violations from stored results"""
            try:
                cluster_id = self._get_current_cluster_id()
                security_results = security_results_manager.get_latest_results(cluster_id)
                
                if security_results and security_results.get('analysis'):
                    policy_compliance = security_results['analysis'].get('policy_compliance', {})
                    violations = policy_compliance.get('violations', [])
                    
                    # Filter by severity if specified
                    if severity:
                        violations = [v for v in violations if v.get('severity') == severity.upper()]
                    
                    # Limit results
                    violations = violations[:limit]
                    
                    return [self._format_violation(v) for v in violations]
                
                # Fallback
                return await self._get_live_policy_violations(severity, limit)
                
            except Exception as e:
                logger.error(f"Failed to get policy violations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        def _get_current_cluster_id(self) -> str:
            """Get current cluster ID from context"""
            # This should be passed from your request context
            # For now, you can get it from cluster_config
            if hasattr(self, 'cluster_config'):
                rg = self.cluster_config.get('resource_group', 'unknown')
                name = self.cluster_config.get('cluster_name', 'unknown')
                return f"{rg}_{name}"
            return None

        def _calculate_trend(self, cluster_id: str) -> str:
            """Calculate security trend from historical data"""
            history = security_results_manager.get_history(cluster_id, limit=2)
            
            if len(history) >= 2:
                current = history[0]['summary']['security_score']
                previous = history[1]['summary']['security_score']
                
                if current > previous + 5:
                    return 'improving'
                elif current < previous - 5:
                    return 'declining'
            
            return 'stable'
        
        @self.app.post("/api/security/analyze/{cluster_id}")
        async def trigger_security_analysis(cluster_id: str, background_tasks: BackgroundTasks):
            """Trigger security analysis for a specific cluster"""
            try:
                # Start analysis in background
                background_tasks.add_task(
                    self._perform_cluster_security_analysis,
                    cluster_id
                )
                
                return {
                    "message": "Security analysis started",
                    "cluster_id": cluster_id,
                    "status": "RUNNING"
                }
                
            except Exception as e:
                logger.error(f"Failed to trigger security analysis: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/security/results/{cluster_id}")
        async def get_security_results(cluster_id: str):
            """Get stored security results for a cluster"""
            try:
                results = security_results_manager.get_latest_results(cluster_id)
                
                if not results:
                    raise HTTPException(status_code=404, detail="No security results found for this cluster")
                
                return {
                    "cluster_id": cluster_id,
                    "cluster_name": results.get('cluster_name'),
                    "timestamp": results.get('timestamp'),
                    "analysis": results.get('analysis'),
                    "metadata": results.get('metadata')
                }
                
            except Exception as e:
                logger.error(f"Failed to get security results: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/security/history/{cluster_id}")
        async def get_security_history(cluster_id: str, limit: int = Query(10, description="Number of historical results")):
            """Get security analysis history for a cluster"""
            try:
                history = security_results_manager.get_history(cluster_id, limit=limit)
                
                return {
                    "cluster_id": cluster_id,
                    "history": history,
                    "count": len(history)
                }
                
            except Exception as e:
                logger.error(f"Failed to get security history: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            
            
        @self.app.get("/api/security/policy-violations/summary")
        async def get_policy_violations_summary():
            """Get policy violations summary statistics"""
            try:
                governance_report = await self.policy_analyzer.analyze_policy_compliance()
                violations = governance_report.policy_violations
                
                summary = {
                    "total": len(violations),
                    "by_severity": {},
                    "by_category": {},
                    "auto_remediable": len([v for v in violations if v.auto_remediable]),
                    "manual_review_required": len([v for v in violations if not v.auto_remediable])
                }
                
                # Count by severity
                for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                    summary["by_severity"][severity] = len([v for v in violations if v.severity == severity])
                
                # Count by category
                categories = set(v.policy_category for v in violations)
                for category in categories:
                    summary["by_category"][category] = len([v for v in violations if v.policy_category == category])
                
                return summary
                
            except Exception as e:
                logger.error(f"Failed to get policy violations summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Compliance Routes
        @self.app.get("/api/security/compliance/frameworks")
        async def get_compliance_frameworks():
            """Get available compliance frameworks"""
            return {
                "frameworks": [
                    {"id": "CIS", "name": "CIS Kubernetes Benchmark", "version": "1.6.0"},
                    {"id": "NIST", "name": "NIST Cybersecurity Framework", "version": "1.1"},
                    {"id": "SOC2", "name": "SOC 2 Type II", "version": "2017"},
                    {"id": "ISO27001", "name": "ISO/IEC 27001", "version": "2013"},
                    {"id": "PCI-DSS", "name": "PCI Data Security Standard", "version": "3.2.1"},
                    {"id": "HIPAA", "name": "HIPAA Security Rule", "version": "2013"}
                ]
            }
        
        @self.app.get("/api/security/compliance/{framework}", response_model=ComplianceStatusResponse)
        async def get_compliance_status(framework: str):
            """Get compliance status for specific framework"""
            try:
                report = await self.compliance_engine.assess_framework_compliance(framework.upper())
                
                return ComplianceStatusResponse(
                    framework=report.framework,
                    overall_compliance=report.overall_compliance,
                    grade=report.compliance_grade,
                    passed_controls=len([c for c in report.control_assessment if c.compliance_status == "COMPLIANT"]),
                    failed_controls=len([c for c in report.control_assessment if c.compliance_status == "NON_COMPLIANT"]),
                    last_assessed=report.generated_at
                )
                
            except Exception as e:
                logger.error(f"Failed to get compliance status for {framework}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/security/compliance/{framework}/detailed")
        async def get_detailed_compliance_report(framework: str):
            """Get detailed compliance report for framework"""
            try:
                report = await self.compliance_engine.assess_framework_compliance(framework.upper())
                
                return {
                    "report_id": report.report_id,
                    "framework": report.framework,
                    "overall_compliance": report.overall_compliance,
                    "compliance_grade": report.compliance_grade,
                    "executive_summary": report.executive_summary,
                    "detailed_findings": report.detailed_findings,
                    "risk_summary": report.risk_summary,
                    "recommendations": report.recommendations,
                    "generated_at": report.generated_at,
                    "control_breakdown": {
                        "total": len(report.control_assessment),
                        "compliant": len([c for c in report.control_assessment if c.compliance_status == "COMPLIANT"]),
                        "non_compliant": len([c for c in report.control_assessment if c.compliance_status == "NON_COMPLIANT"]),
                        "partial": len([c for c in report.control_assessment if c.compliance_status == "PARTIAL"]),
                        "not_tested": len([c for c in report.control_assessment if c.compliance_status == "NOT_TESTED"])
                    }
                }
                
            except Exception as e:
                logger.error(f"Failed to get detailed compliance report for {framework}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/security/compliance/{framework}/heatmap")
        async def get_compliance_heatmap(framework: str):
            """Get compliance heatmap for visualization"""
            try:
                heatmap = await self.compliance_engine.generate_compliance_heatmap(framework.upper())
                
                return {
                    "framework": heatmap.framework,
                    "categories": heatmap.categories,
                    "category_scores": heatmap.category_scores,
                    "control_matrix": heatmap.control_matrix,
                    "risk_areas": heatmap.risk_areas,
                    "improvement_areas": heatmap.improvement_areas,
                    "generated_at": heatmap.generated_at
                }
                
            except Exception as e:
                logger.error(f"Failed to get compliance heatmap for {framework}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Vulnerability Routes
        @self.app.get("/api/security/vulnerabilities", response_model=List[VulnerabilityResponse])
        async def get_vulnerabilities(
            severity: Optional[str] = Query(None, description="Filter by severity"),
            limit: int = Query(100, description="Maximum number of results")
        ):
            """Get vulnerabilities with optional filtering"""
            try:
                if severity:
                    vulnerabilities = await self.vulnerability_scanner.get_vulnerabilities_by_severity(
                        severity.upper(), limit
                    )
                else:
                    # Get latest scan results
                    latest_scan = await self.vulnerability_scanner.get_latest_scan_result()
                    if not latest_scan:
                        return []
                    
                    vulnerabilities = latest_scan.vulnerabilities_found[:limit]
                
                return [
                    VulnerabilityResponse(
                        vuln_id=v.vuln_id,
                        cve_id=v.cve_id,
                        title=v.title,
                        severity=v.severity,
                        cvss_score=v.cvss_score,
                        affected_component=v.affected_component,
                        exploit_available=v.exploit_available,
                        remediation_guidance=v.remediation_guidance,
                        detected_at=v.detected_at
                    )
                    for v in vulnerabilities
                ]
                
            except Exception as e:
                logger.error(f"Failed to get vulnerabilities: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/security/vulnerabilities/summary")
        async def get_vulnerabilities_summary():
            """Get vulnerability summary statistics"""
            try:
                latest_scan = await self.vulnerability_scanner.get_latest_scan_result()
                
                if not latest_scan:
                    return {
                        "total": 0,
                        "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                        "exploitable": 0,
                        "with_cve": 0,
                        "last_scan": None,
                        "scan_status": "NEVER_RUN"
                    }
                
                return {
                    "total": latest_scan.summary.get("total", 0),
                    "by_severity": {
                        "CRITICAL": latest_scan.summary.get("CRITICAL", 0),
                        "HIGH": latest_scan.summary.get("HIGH", 0),
                        "MEDIUM": latest_scan.summary.get("MEDIUM", 0),
                        "LOW": latest_scan.summary.get("LOW", 0)
                    },
                    "exploitable": latest_scan.summary.get("exploitable", 0),
                    "with_cve": latest_scan.summary.get("with_cve", 0),
                    "last_scan": latest_scan.completed_at,
                    "scan_status": latest_scan.scan_status,
                    "coverage_percentage": latest_scan.coverage_percentage
                }
                
            except Exception as e:
                logger.error(f"Failed to get vulnerability summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/security/vulnerabilities/scan")
        async def trigger_vulnerability_scan(background_tasks: BackgroundTasks):
            """Trigger new vulnerability scan"""
            try:
                # Start scan in background
                background_tasks.add_task(self._perform_background_scan)
                
                return {"message": "Vulnerability scan started", "status": "RUNNING"}
                
            except Exception as e:
                logger.error(f"Failed to trigger vulnerability scan: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Security Alert Routes
        @self.app.get("/api/security/alerts")
        async def get_security_alerts(
            severity: Optional[str] = Query(None, description="Filter by severity"),
            limit: int = Query(100, description="Maximum number of results")
        ):
            """Get security alerts with optional filtering"""
            try:
                alerts = await self.security_engine.get_security_alerts(severity, limit)
                
                return [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity,
                        "category": alert.category,
                        "title": alert.title,
                        "description": alert.description,
                        "resource_type": alert.resource_type,
                        "resource_name": alert.resource_name,
                        "namespace": alert.namespace,
                        "remediation": alert.remediation,
                        "risk_score": alert.risk_score,
                        "detected_at": alert.detected_at
                    }
                    for alert in alerts
                ]
                
            except Exception as e:
                logger.error(f"Failed to get security alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Security Trends Routes
        @self.app.get("/api/security/trends/{trend_type}")
        async def get_security_trends(trend_type: str, days: int = Query(30, description="Number of days")):
            """Get security trends over time"""
            try:
                # This would query historical data from database
                # For demo, return sample trend data
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Generate sample trend data
                data_points = []
                current_date = start_date
                
                while current_date <= end_date:
                    # Simulate trend data
                    if trend_type == "security_score":
                        score = 75 + (hash(str(current_date)) % 20)  # Random but deterministic
                    elif trend_type == "vulnerability_count":
                        score = 15 + (hash(str(current_date)) % 10)
                    elif trend_type == "compliance_percentage":
                        score = 80 + (hash(str(current_date)) % 15)
                    else:
                        score = 50 + (hash(str(current_date)) % 30)
                    
                    data_points.append({
                        "date": current_date.isoformat(),
                        "value": score
                    })
                    
                    current_date += timedelta(days=1)
                
                # Calculate trend direction
                if len(data_points) >= 2:
                    current_score = data_points[-1]["value"]
                    previous_score = data_points[-7]["value"] if len(data_points) >= 7 else data_points[0]["value"]
                    change_percentage = ((current_score - previous_score) / previous_score) * 100
                    
                    if change_percentage > 5:
                        trend_direction = "improving"
                    elif change_percentage < -5:
                        trend_direction = "declining"
                    else:
                        trend_direction = "stable"
                else:
                    current_score = 0
                    previous_score = 0
                    change_percentage = 0
                    trend_direction = "stable"
                
                return SecurityTrendsResponse(
                    trend_type=trend_type,
                    current_score=current_score,
                    previous_score=previous_score,
                    change_percentage=change_percentage,
                    trend_direction=trend_direction,
                    data_points=data_points
                )
                
            except Exception as e:
                logger.error(f"Failed to get security trends: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Audit Trail Routes
        @self.app.get("/api/security/audit-trail", response_model=List[AuditTrailResponse])
        async def get_audit_trail(
            event_type: Optional[str] = Query(None, description="Filter by event type"),
            days: int = Query(7, description="Number of days to look back"),
            limit: int = Query(100, description="Maximum number of results")
        ):
            """Get audit trail entries"""
            try:
                # Get recent audit trail from compliance engine
                audit_entries = await self.compliance_engine._get_recent_audit_trail("ALL", days)
                
                # Filter by event type if specified
                if event_type:
                    audit_entries = [e for e in audit_entries if e.event_type == event_type.upper()]
                
                # Limit results
                audit_entries = audit_entries[:limit]
                
                return [
                    AuditTrailResponse(
                        audit_id=entry.audit_id,
                        timestamp=entry.timestamp,
                        event_type=entry.event_type,
                        user=entry.user,
                        action=entry.action,
                        resource_name=entry.resource_name,
                        compliance_impact=entry.compliance_impact
                    )
                    for entry in audit_entries
                ]
                
            except Exception as e:
                logger.error(f"Failed to get audit trail: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Export Routes
        @self.app.get("/api/security/export/{report_type}")
        async def export_security_report(
            report_type: str,
            format: str = Query("pdf", description="Export format: pdf, csv, json"),
            framework: Optional[str] = Query(None, description="Compliance framework for compliance reports")
        ):
            """Export security reports in various formats"""
            try:
                if report_type == "compliance" and framework:
                    # Export compliance report
                    report = await self.compliance_engine.assess_framework_compliance(framework.upper())
                    file_path = await self.compliance_engine.export_audit_report(report, format)
                    
                    return FileResponse(
                        file_path,
                        media_type=f"application/{format}",
                        filename=Path(file_path).name
                    )
                    
                elif report_type == "vulnerability":
                    # Export vulnerability report
                    latest_scan = await self.vulnerability_scanner.get_latest_scan_result()
                    if not latest_scan:
                        raise HTTPException(status_code=404, detail="No scan results available")
                    
                    # Create temporary export file
                    file_path = await self._export_vulnerability_report(latest_scan, format)
                    
                    return FileResponse(
                        file_path,
                        media_type=f"application/{format}",
                        filename=Path(file_path).name
                    )
                    
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported report type: {report_type}")
                
            except Exception as e:
                logger.error(f"Failed to export {report_type} report: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Health Check Route
        @self.app.get("/api/security/health")
        async def health_check():
            """API health check"""
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "components": {
                    "security_engine": "operational",
                    "policy_analyzer": "operational", 
                    "compliance_engine": "operational",
                    "vulnerability_scanner": "operational"
                }
            }
        
        logger.info("✅ API routes configured")
    
    def _setup_background_tasks(self):
        """Setup background tasks for periodic updates"""
        
        async def periodic_security_analysis():
            """Periodic security analysis task"""
            while True:
                try:
                    logger.info("🔄 Running periodic security analysis...")
                    await self.security_engine.analyze_security_posture()
                    logger.info("✅ Periodic security analysis completed")
                    
                    # Sleep for 1 hour
                    await asyncio.sleep(3600)
                    
                except Exception as e:
                    logger.error(f"❌ Periodic security analysis failed: {e}")
                    await asyncio.sleep(600)  # Retry in 10 minutes
        
        # Start background task (in production, use proper task scheduler)
        asyncio.create_task(periodic_security_analysis())
        
        logger.info("⏰ Background tasks configured")
    
    async def _perform_background_scan(self):
        """Perform vulnerability scan in background"""
        try:
            logger.info("🔍 Starting background vulnerability scan...")
            await self.vulnerability_scanner.perform_comprehensive_scan("FULL")
            logger.info("✅ Background vulnerability scan completed")
        except Exception as e:
            logger.error(f"❌ Background vulnerability scan failed: {e}")
    
    async def _export_vulnerability_report(self, scan_result: ScanResult, format: str) -> str:
        """Export vulnerability report in specified format"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            file_path = f"reports/vulnerability_report_{timestamp}.json"
            Path("reports").mkdir(exist_ok=True)
            
            # Convert to dict for JSON serialization
            report_data = {
                "scan_id": scan_result.scan_id,
                "scan_type": scan_result.scan_type,
                "scan_status": scan_result.scan_status,
                "started_at": scan_result.started_at.isoformat(),
                "completed_at": scan_result.completed_at.isoformat() if scan_result.completed_at else None,
                "vulnerabilities": [
                    {
                        "vuln_id": v.vuln_id,
                        "cve_id": v.cve_id,
                        "title": v.title,
                        "severity": v.severity,
                        "cvss_score": v.cvss_score,
                        "affected_component": v.affected_component,
                        "remediation_guidance": v.remediation_guidance
                    }
                    for v in scan_result.vulnerabilities_found
                ],
                "summary": scan_result.summary
            }
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2)
                
        elif format == "csv":
            import csv
            
            file_path = f"reports/vulnerability_report_{timestamp}.csv"
            Path("reports").mkdir(exist_ok=True)
            
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Vulnerability ID', 'CVE ID', 'Title', 'Severity', 'CVSS Score', 
                               'Affected Component', 'Remediation'])
                
                for v in scan_result.vulnerabilities_found:
                    writer.writerow([
                        v.vuln_id, v.cve_id or 'N/A', v.title, v.severity,
                        v.cvss_score, v.affected_component, v.remediation_guidance
                    ])
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return file_path
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the API server"""
        
        logger.info(f"🚀 Starting Security Dashboard API on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            reload=debug
        )


# Factory function for integration
def create_security_dashboard_api(cluster_config: Dict) -> SecurityDashboardAPI:
    """Create Security Dashboard API instance"""
    return SecurityDashboardAPI(cluster_config)


# FastAPI app instance for direct usage
def create_fastapi_app(cluster_config: Dict) -> FastAPI:
    """Create FastAPI app instance"""
    dashboard_api = create_security_dashboard_api(cluster_config)
    return dashboard_api.app


# CLI entry point
if __name__ == "__main__":
    import sys
    
    # Mock cluster config for testing
    mock_cluster_config = {
        "workload_resources": {
            "deployments": {"items": []},
            "services": {"items": []},
            "pods": {"items": []}
        },
        "security_resources": {
            "roles": {"item_count": 5},
            "rolebindings": {"item_count": 8},
            "serviceaccounts": {"item_count": 10}
        },
        "networking_resources": {
            "networkpolicies": {"item_count": 2},
            "ingresses": {"items": []}
        }
    }
    
    # Create and run API
    api = create_security_dashboard_api(mock_cluster_config)
    api.run(debug=True)