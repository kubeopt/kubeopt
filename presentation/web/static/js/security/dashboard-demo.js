/**
 * Security Dashboard Demo & Testing
 * ================================
 * Demo data and testing utilities for the unified security dashboard
 * Includes responsive design testing and sample data generation
 */

class SecurityDashboardDemo {
    constructor() {
        this.sampleData = this.generateSampleData();
        this.responsiveBreakpoints = {
            mobile: 480,
            tablet: 768,
            desktop: 1024,
            large: 1200
        };
    }

    generateSampleData() {
        const now = new Date();
        
        return {
            analysis: {
                security_posture: {
                    overall_score: 78,
                    grade: 'B+',
                    alerts_count: 12,
                    alerts: [
                        {
                            alert_id: 'SEC001',
                            severity: 'CRITICAL',
                            category: 'VULNERABILITY',
                            title: 'Unpatched Container Vulnerability',
                            description: 'Critical vulnerability CVE-2023-1234 found in nginx container',
                            resource_type: 'Pod',
                            resource_name: 'web-app-pod-123',
                            namespace: 'production',
                            remediation: 'Update nginx to version 1.21.6 or later',
                            risk_score: 9.1,
                            detected_at: new Date(now.getTime() - 3600000).toISOString()
                        },
                        {
                            alert_id: 'SEC002',
                            severity: 'HIGH',
                            category: 'RBAC',
                            title: 'Overprivileged Service Account',
                            description: 'Service account has cluster-admin privileges',
                            resource_type: 'ServiceAccount',
                            resource_name: 'api-service-account',
                            namespace: 'default',
                            remediation: 'Apply principle of least privilege to service account',
                            risk_score: 7.8,
                            detected_at: new Date(now.getTime() - 7200000).toISOString()
                        },
                        {
                            alert_id: 'SEC003',
                            severity: 'MEDIUM',
                            category: 'NETWORK',
                            title: 'Missing Network Policy',
                            description: 'Namespace lacks network segmentation policies',
                            resource_type: 'Namespace',
                            resource_name: 'staging',
                            namespace: 'staging',
                            remediation: 'Implement NetworkPolicy for traffic isolation',
                            risk_score: 5.2,
                            detected_at: new Date(now.getTime() - 10800000).toISOString()
                        },
                        {
                            alert_id: 'SEC004',
                            severity: 'LOW',
                            category: 'POLICY',
                            title: 'Resource Limits Not Set',
                            description: 'Pod running without resource limits',
                            resource_type: 'Pod',
                            resource_name: 'worker-pod-456',
                            namespace: 'development',
                            remediation: 'Set CPU and memory limits in pod spec',
                            risk_score: 3.1,
                            detected_at: new Date(now.getTime() - 14400000).toISOString()
                        }
                    ],
                    breakdown: {
                        rbac_score: 85,
                        network_score: 72,
                        encryption_score: 91,
                        vulnerability_score: 65,
                        compliance_score: 78,
                        drift_score: 88
                    },
                    trends: {
                        trend: 'improving',
                        change: 5.2,
                        data_points: 30,
                        component_trends: {
                            rbac: 'improving',
                            network: 'stable',
                            encryption: 'improving',
                            vulnerability: 'declining'
                        },
                        time_range: {
                            oldest: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(),
                            newest: now.toISOString()
                        }
                    }
                },
                policy_compliance: {
                    overall_compliance: 74,
                    violations_count: 8,
                    violations_by_severity: {
                        CRITICAL: 1,
                        HIGH: 2,
                        MEDIUM: 3,
                        LOW: 2
                    },
                    violations: [
                        {
                            violation_id: 'POL001',
                            policy_name: 'Pod Security Standard - Restricted',
                            severity: 'CRITICAL',
                            policy_category: 'Security Context',
                            violation_description: 'Pod running with privileged security context',
                            resource_type: 'Pod',
                            resource_name: 'admin-tool-pod',
                            namespace: 'kube-system',
                            auto_remediable: false,
                            risk_score: 8.9,
                            remediation_steps: [
                                'Remove privileged: true from security context',
                                'Set runAsNonRoot: true',
                                'Configure appropriate capabilities'
                            ],
                            compliance_frameworks: ['CIS', 'NIST'],
                            detected_at: new Date(now.getTime() - 5400000).toISOString()
                        },
                        {
                            violation_id: 'POL002',
                            policy_name: 'Network Segmentation Policy',
                            severity: 'HIGH',
                            policy_category: 'Network Security',
                            violation_description: 'Missing network policies for namespace isolation',
                            resource_type: 'Namespace',
                            resource_name: 'api-gateway',
                            namespace: 'api-gateway',
                            auto_remediable: true,
                            risk_score: 6.7,
                            remediation_steps: [
                                'Apply default deny NetworkPolicy',
                                'Create specific ingress/egress rules',
                                'Test connectivity after implementation'
                            ],
                            compliance_frameworks: ['CIS', 'SOC2'],
                            detected_at: new Date(now.getTime() - 7200000).toISOString()
                        }
                    ]
                },
                compliance_frameworks: {
                    'CIS': {
                        overall_compliance: 82,
                        grade: 'B+',
                        passed_controls: 45,
                        failed_controls: 10,
                        risk_level: 'MEDIUM',
                        based_on_actual_controls: true,
                        control_details: [
                            {
                                control_id: 'CIS-1.1.1',
                                title: 'Ensure API server pod specification file permissions',
                                description: 'API server pod specification should have appropriate permissions',
                                compliance_status: 'COMPLIANT',
                                severity: 'HIGH',
                                remediation_guidance: 'File permissions are correctly configured'
                            },
                            {
                                control_id: 'CIS-1.2.1',
                                title: 'Minimize access to secrets',
                                description: 'Secrets should not be accessible to unauthorized users',
                                compliance_status: 'NON_COMPLIANT',
                                severity: 'CRITICAL',
                                remediation_guidance: 'Implement RBAC restrictions for secret access'
                            }
                        ]
                    },
                    'NIST': {
                        overall_compliance: 75,
                        grade: 'B',
                        passed_controls: 38,
                        failed_controls: 12,
                        risk_level: 'MEDIUM',
                        based_on_actual_controls: true,
                        control_details: [
                            {
                                control_id: 'NIST-AC-2',
                                title: 'Account Management',
                                description: 'Manage system accounts and access controls',
                                compliance_status: 'COMPLIANT',
                                severity: 'HIGH'
                            },
                            {
                                control_id: 'NIST-SC-8',
                                title: 'Transmission Confidentiality',
                                description: 'Protect data in transit',
                                compliance_status: 'NON_COMPLIANT',
                                severity: 'HIGH',
                                remediation_guidance: 'Enable TLS for all internal communications'
                            }
                        ]
                    },
                    'SOC2': {
                        overall_compliance: 68,
                        grade: 'C+',
                        passed_controls: 25,
                        failed_controls: 12,
                        risk_level: 'HIGH',
                        based_on_actual_controls: true,
                        control_details: [
                            {
                                control_id: 'SOC2-CC6.1',
                                title: 'Logical and Physical Access Controls',
                                description: 'Implement access controls for system resources',
                                compliance_status: 'COMPLIANT',
                                severity: 'HIGH'
                            },
                            {
                                control_id: 'SOC2-CC6.7',
                                title: 'Data Transmission',
                                description: 'Encrypt data in transmission',
                                compliance_status: 'NON_COMPLIANT',
                                severity: 'MEDIUM',
                                remediation_guidance: 'Implement end-to-end encryption'
                            }
                        ]
                    }\n                },\n                vulnerability_assessment: {\n                    total_vulnerabilities: 15,\n                    critical_vulnerabilities: 2,\n                    high_vulnerabilities: 4,\n                    medium_vulnerabilities: 6,\n                    low_vulnerabilities: 3,\n                    last_scan: now.toISOString()\n                }\n            }\n        };\n    }"}, {"old_string": "    // Initialize the unified dashboard\nlet unifiedSecurity;\n\ndocument.addEventListener('DOMContentLoaded', () => {\n    // Initialize unified security dashboard\n    unifiedSecurity = new UnifiedSecurityDashboard();\n    window.unifiedSecurity = unifiedSecurity;\n    \n    // Global cleanup on page unload\n    window.addEventListener('beforeunload', () => {\n        if (unifiedSecurity) {\n            unifiedSecurity.destroy();\n        }\n    });\n});", "new_string": "    // Demo and testing methods\n    loadDemoData() {\n        console.log('\ud83c\udfad Loading demo security data...');\n        this.state.data = this.sampleData;\n        this.updateDashboard(this.sampleData);\n        document.getElementById('last-update-time').textContent = 'Demo Mode - ' + new Date().toLocaleTimeString();\n    }\n\n    testResponsiveDesign() {\n        console.log('\ud83d\udcf1 Testing responsive design...');\n        \n        const breakpoints = Object.entries(this.responsiveBreakpoints);\n        let currentIndex = 0;\n        \n        const testBreakpoint = () => {\n            if (currentIndex >= breakpoints.length) {\n                // Reset to original size\n                document.body.style.width = '';\n                console.log('\u2705 Responsive testing completed');\n                return;\n            }\n            \n            const [name, width] = breakpoints[currentIndex];\n            document.body.style.width = width + 'px';\n            console.log(`Testing ${name}: ${width}px`);\n            \n            setTimeout(() => {\n                currentIndex++;\n                testBreakpoint();\n            }, 2000);\n        };\n        \n        testBreakpoint();\n    }\n\n    validateChartInteractions() {\n        console.log('\ud83d\udd0d Validating chart interactions...');\n        \n        const charts = ['compliance', 'risk', 'trends', 'alerts', 'violations'];\n        const results = {};\n        \n        charts.forEach(chartType => {\n            const chart = this.charts.get(chartType);\n            if (chart) {\n                results[chartType] = {\n                    exists: true,\n                    clickable: chart.options?.onClick !== undefined,\n                    hoverable: chart.options?.onHover !== undefined,\n                    responsive: chart.options?.responsive === true\n                };\n            } else {\n                results[chartType] = { exists: false };\n            }\n        });\n        \n        console.log('Chart validation results:', results);\n        return results;\n    }\n}\n\n// Initialize the unified dashboard\nlet unifiedSecurity;\nlet dashboardDemo;\n\ndocument.addEventListener('DOMContentLoaded', () => {\n    // Initialize unified security dashboard\n    unifiedSecurity = new UnifiedSecurityDashboard();\n    window.unifiedSecurity = unifiedSecurity;\n    \n    // Initialize demo utilities\n    dashboardDemo = new SecurityDashboardDemo();\n    window.dashboardDemo = dashboardDemo;\n    \n    // Add demo methods to unified dashboard\n    unifiedSecurity.loadDemoData = () => dashboardDemo.loadDemoData.call(unifiedSecurity);\n    unifiedSecurity.testResponsive = () => dashboardDemo.testResponsiveDesign();\n    unifiedSecurity.validateCharts = () => dashboardDemo.validateChartInteractions.call(unifiedSecurity);\n    \n    // Global cleanup on page unload\n    window.addEventListener('beforeunload', () => {\n        if (unifiedSecurity) {\n            unifiedSecurity.destroy();\n        }\n    });\n    \n    // Console helpers for testing\n    window.securityDashboardHelpers = {\n        loadDemo: () => unifiedSecurity.loadDemoData(),\n        testResponsive: () => unifiedSecurity.testResponsive(),\n        validateCharts: () => unifiedSecurity.validateCharts(),\n        exportReport: () => unifiedSecurity.exportReport(),\n        resetFilters: () => unifiedSecurity.resetFilters(),\n        showPerformance: () => console.table(unifiedSecurity.dataManager.getPerformanceMetrics())\n    };\n    \n    console.log('🔧 Security Dashboard Helpers available:');\n    console.log('  - securityDashboardHelpers.loadDemo()');\n    console.log('  - securityDashboardHelpers.testResponsive()');\n    console.log('  - securityDashboardHelpers.validateCharts()');\n    console.log('  - securityDashboardHelpers.exportReport()');\n    console.log('  - securityDashboardHelpers.showPerformance()');\n});"}