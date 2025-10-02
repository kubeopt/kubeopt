#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
CPU Analysis Report Exporter
============================
Exports comprehensive CPU analysis reports in multiple formats (PDF, Excel, JSON, CSV)
with detailed metrics, optimization recommendations, and executive summaries.
"""

import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import os
import base64
from io import BytesIO

# Optional dependencies - graceful fallbacks
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CPUReportMetrics:
    """CPU metrics for report generation"""
    cluster_id: str
    average_cpu_usage: float
    peak_cpu_usage: float
    cpu_efficiency: float
    high_cpu_workloads: int
    total_pods: int
    nodes_count: int
    monthly_cost: float
    optimization_potential_pct: float
    critical_alerts: int
    report_timestamp: datetime = None

@dataclass 
class CPUReportData:
    """Complete CPU report data structure"""
    metrics: CPUReportMetrics
    optimization_plan: Dict[str, Any]
    detailed_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Any]
    trend_data: List[Dict[str, Any]] = None
    node_analysis: List[Dict[str, Any]] = None
    pod_analysis: List[Dict[str, Any]] = None

class CPUReportExporter:
    """Exports CPU analysis reports in multiple formats"""
    
    def __init__(self, output_dir: str = "/tmp/cpu_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_comprehensive_report(self, 
                                  report_data: CPUReportData,
                                  format_type: str = "pdf") -> str:
        """Export comprehensive CPU report in specified format"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cluster_id = report_data.metrics.cluster_id
        
        try:
            if format_type.lower() == "pdf":
                return self._export_pdf_report(report_data, timestamp)
            elif format_type.lower() == "excel":
                return self._export_excel_report(report_data, timestamp)
            elif format_type.lower() == "json":
                return self._export_json_report(report_data, timestamp)
            elif format_type.lower() == "csv":
                return self._export_csv_report(report_data, timestamp)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to export {format_type} report: {e}")
            raise
    
    def _export_pdf_report(self, report_data: CPUReportData, timestamp: str) -> str:
        """Export detailed PDF report with charts and analysis"""
        
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available, falling back to JSON export")
            return self._export_json_report(report_data, timestamp)
        
        filename = f"cpu_analysis_report_{report_data.metrics.cluster_id}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E86C1'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1B4F72'),
            spaceBefore=20,
            spaceAfter=12
        )
        
        # Build document content
        content = []
        metrics = report_data.metrics
        
        # Title page
        content.append(Paragraph("AKS CPU Analysis Report", title_style))
        content.append(Spacer(1, 0.2*inch))
        
        # Executive summary
        content.append(Paragraph("Executive Summary", heading_style))
        
        exec_summary = f"""
        <b>Cluster:</b> {metrics.cluster_id}<br/>
        <b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
        <b>Analysis Period:</b> Last 24 hours<br/><br/>
        
        <b>Key Findings:</b><br/>
        • Average CPU Utilization: <font color="{'red' if metrics.average_cpu_usage > 80 else '#1E40AF'}">{metrics.average_cpu_usage:.1f}%</font><br/>
        • Peak CPU Usage: <font color="{'red' if metrics.peak_cpu_usage > 150 else 'orange' if metrics.peak_cpu_usage > 100 else '#1E40AF'}">{metrics.peak_cpu_usage:.1f}%</font><br/>
        • CPU Efficiency Score: <font color="{'red' if metrics.cpu_efficiency < 30 else 'orange' if metrics.cpu_efficiency < 70 else '#1E40AF'}">{metrics.cpu_efficiency:.1f}%</font><br/>
        • High CPU Workloads: {metrics.high_cpu_workloads} out of {metrics.total_pods} pods<br/>
        • Monthly Cost Impact: <b>${metrics.monthly_cost:,.2f}</b><br/>
        • Optimization Potential: <font color="#1E40AF">{metrics.optimization_potential_pct:.1f}%</font><br/>
        """
        
        if metrics.average_cpu_usage > 200:
            exec_summary += "<br/><font color='red'><b>🚨 CRITICAL:</b> CPU overutilization detected requiring immediate action.</font>"
        elif metrics.average_cpu_usage > 80:
            exec_summary += "<br/><font color='orange'><b>⚠️ WARNING:</b> High CPU usage detected.</font>"
        
        content.append(Paragraph(exec_summary, styles['Normal']))
        content.append(Spacer(1, 0.3*inch))
        
        # CPU Metrics Table
        content.append(Paragraph("Detailed CPU Metrics", heading_style))
        
        cpu_data = [
            ['Metric', 'Current Value', 'Status', 'Recommended'],
            ['Average CPU Usage', f'{metrics.average_cpu_usage:.1f}%', 
             'Critical' if metrics.average_cpu_usage > 200 else 'High' if metrics.average_cpu_usage > 80 else 'Normal',
             '60-80%'],
            ['Peak CPU Usage', f'{metrics.peak_cpu_usage:.1f}%',
             'Critical' if metrics.peak_cpu_usage > 400 else 'High' if metrics.peak_cpu_usage > 150 else 'Normal',
             '<150%'],
            ['CPU Efficiency', f'{metrics.cpu_efficiency:.1f}%',
             'Low' if metrics.cpu_efficiency < 50 else 'Medium' if metrics.cpu_efficiency < 80 else 'High',
             '>80%'],
            ['Nodes with High CPU', f'{metrics.nodes_count}', 'Variable', 'Monitor'],
            ['Critical Alerts', str(metrics.critical_alerts), 
             'High' if metrics.critical_alerts > 5 else 'Medium' if metrics.critical_alerts > 0 else 'Low',
             '0']
        ]
        
        cpu_table = Table(cpu_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
        cpu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(cpu_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Cost Analysis
        content.append(Paragraph("Cost Analysis", heading_style))
        
        cost_breakdown = report_data.cost_breakdown
        cost_text = f"""
        <b>Current Monthly Cost:</b> ${metrics.monthly_cost:,.2f}<br/>
        <b>Estimated Waste:</b> ${cost_breakdown.get('wasted_cost', 0):,.2f} 
        ({cost_breakdown.get('waste_percentage', 0):.1f}% of total)<br/>
        <b>Optimization Potential:</b> ${cost_breakdown.get('potential_savings', 0):,.2f}/month<br/>
        <b>Annual Savings Opportunity:</b> ${cost_breakdown.get('potential_savings', 0) * 12:,.2f}<br/>
        """
        
        content.append(Paragraph(cost_text, styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Optimization Recommendations
        content.append(PageBreak())
        content.append(Paragraph("Optimization Recommendations", heading_style))
        
        for i, rec in enumerate(report_data.recommendations[:10], 1):  # Top 10 recommendations
            rec_text = f"""
            <b>{i}. {rec.get('title', 'Optimization Action')}</b><br/>
            <i>Priority:</i> {rec.get('priority', 'Medium')} | 
            <i>Impact:</i> {rec.get('impact', 'TBD')} | 
            <i>Effort:</i> {rec.get('effort', 'Medium')}<br/>
            {rec.get('description', 'No description available')}<br/>
            <font color="blue"><i>Command:</i> {rec.get('command', 'See implementation guide')}</font><br/>
            """
            content.append(Paragraph(rec_text, styles['Normal']))
            content.append(Spacer(1, 0.1*inch))
        
        # Implementation Timeline
        content.append(Paragraph("Implementation Timeline", heading_style))
        
        timeline_text = f"""
        <b>Immediate Actions (0-24 hours):</b><br/>
        • Apply emergency CPU limits to runaway workloads<br/>
        • Scale critical node pools if needed<br/>
        • Review and adjust HPA configurations<br/><br/>
        
        <b>Short-term Actions (1-7 days):</b><br/>
        • Implement resource quotas and limits<br/>
        • Optimize workload resource requests<br/>
        • Configure vertical pod autoscaling<br/><br/>
        
        <b>Long-term Actions (1-4 weeks):</b><br/>
        • Review application architecture for efficiency<br/>
        • Implement advanced autoscaling policies<br/>
        • Establish ongoing monitoring and alerting<br/>
        """
        
        content.append(Paragraph(timeline_text, styles['Normal']))
        
        # Technical Details Section
        if report_data.detailed_analysis:
            content.append(PageBreak())
            content.append(Paragraph("Technical Analysis Details", heading_style))
            
            details = report_data.detailed_analysis
            detail_text = f"""
            <b>Node Analysis:</b><br/>
            • Total Nodes: {details.get('total_nodes', 'N/A')}<br/>
            • Nodes at High CPU: {details.get('high_cpu_nodes', 'N/A')}<br/>
            • Average Node Utilization: {details.get('avg_node_utilization', 'N/A')}%<br/><br/>
            
            <b>Pod Distribution:</b><br/>
            • Total Running Pods: {details.get('total_pods', 'N/A')}<br/>
            • Pods without CPU limits: {details.get('pods_no_limits', 'N/A')}<br/>
            • Pods with CPU requests: {details.get('pods_with_requests', 'N/A')}<br/><br/>
            
            <b>Workload Patterns:</b><br/>
            • Peak Usage Time: {details.get('peak_time', 'N/A')}<br/>
            • CPU Volatility Score: {details.get('volatility_score', 'N/A')}<br/>
            • Scaling Events (24h): {details.get('scaling_events', 'N/A')}<br/>
            """
            
            content.append(Paragraph(detail_text, styles['Normal']))
        
        # Footer
        content.append(PageBreak())
        footer_text = f"""
        <para align="center">
        <font size="10">
        Generated by AKS Cost Optimizer | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        For technical support: support@nivaya.ai<br/>
        Report Version: 1.0 | Cluster: {metrics.cluster_id}
        </font>
        </para>
        """
        content.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(content)
        
        logger.info(f"✅ PDF report exported: {filepath}")
        return filepath
    
    def _export_excel_report(self, report_data: CPUReportData, timestamp: str) -> str:
        """Export detailed Excel report with multiple sheets"""
        
        if not PANDAS_AVAILABLE:
            logger.warning("Pandas not available, falling back to JSON export")
            return self._export_json_report(report_data, timestamp)
        
        filename = f"cpu_analysis_report_{report_data.metrics.cluster_id}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Summary sheet
            summary_data = {
                'Metric': ['Cluster ID', 'Report Date', 'Average CPU Usage (%)', 'Peak CPU Usage (%)', 
                          'CPU Efficiency (%)', 'High CPU Workloads', 'Total Pods', 'Nodes Count',
                          'Monthly Cost ($)', 'Optimization Potential (%)', 'Critical Alerts'],
                'Value': [
                    report_data.metrics.cluster_id,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    report_data.metrics.average_cpu_usage,
                    report_data.metrics.peak_cpu_usage,
                    report_data.metrics.cpu_efficiency,
                    report_data.metrics.high_cpu_workloads,
                    report_data.metrics.total_pods,
                    report_data.metrics.nodes_count,
                    report_data.metrics.monthly_cost,
                    report_data.metrics.optimization_potential_pct,
                    report_data.metrics.critical_alerts
                ]
            }
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Recommendations sheet
            if report_data.recommendations:
                df_recommendations = pd.DataFrame(report_data.recommendations)
                df_recommendations.to_excel(writer, sheet_name='Recommendations', index=False)
            
            # Cost breakdown sheet
            if report_data.cost_breakdown:
                cost_data = []
                for key, value in report_data.cost_breakdown.items():
                    cost_data.append({'Category': key, 'Value': value})
                
                df_costs = pd.DataFrame(cost_data)
                df_costs.to_excel(writer, sheet_name='Cost_Analysis', index=False)
            
            # Node analysis sheet
            if report_data.node_analysis:
                df_nodes = pd.DataFrame(report_data.node_analysis)
                df_nodes.to_excel(writer, sheet_name='Node_Analysis', index=False)
            
            # Pod analysis sheet
            if report_data.pod_analysis:
                df_pods = pd.DataFrame(report_data.pod_analysis)
                df_pods.to_excel(writer, sheet_name='Pod_Analysis', index=False)
        
        logger.info(f"✅ Excel report exported: {filepath}")
        return filepath
    
    def _export_json_report(self, report_data: CPUReportData, timestamp: str) -> str:
        """Export complete report data as JSON"""
        
        filename = f"cpu_analysis_report_{report_data.metrics.cluster_id}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert dataclasses to dict
        report_dict = {
            'metadata': {
                'report_type': 'cpu_analysis',
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'cluster_id': report_data.metrics.cluster_id
            },
            'metrics': asdict(report_data.metrics),
            'optimization_plan': report_data.optimization_plan,
            'detailed_analysis': report_data.detailed_analysis,
            'recommendations': report_data.recommendations,
            'cost_breakdown': report_data.cost_breakdown,
            'trend_data': report_data.trend_data or [],
            'node_analysis': report_data.node_analysis or [],
            'pod_analysis': report_data.pod_analysis or []
        }
        
        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"✅ JSON report exported: {filepath}")
        return filepath
    
    def _export_csv_report(self, report_data: CPUReportData, timestamp: str) -> str:
        """Export summary data as CSV"""
        
        filename = f"cpu_analysis_summary_{report_data.metrics.cluster_id}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Metric', 'Value', 'Unit', 'Status'])
            
            # Write metrics
            metrics = report_data.metrics
            writer.writerow(['Cluster ID', metrics.cluster_id, '', ''])
            writer.writerow(['Report Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '', ''])
            writer.writerow(['Average CPU Usage', f'{metrics.average_cpu_usage:.1f}', '%', 
                           'Critical' if metrics.average_cpu_usage > 200 else 'High' if metrics.average_cpu_usage > 80 else 'Normal'])
            writer.writerow(['Peak CPU Usage', f'{metrics.peak_cpu_usage:.1f}', '%',
                           'Critical' if metrics.peak_cpu_usage > 400 else 'High' if metrics.peak_cpu_usage > 150 else 'Normal'])
            writer.writerow(['CPU Efficiency', f'{metrics.cpu_efficiency:.1f}', '%',
                           'Low' if metrics.cpu_efficiency < 50 else 'Medium' if metrics.cpu_efficiency < 80 else 'High'])
            writer.writerow(['High CPU Workloads', metrics.high_cpu_workloads, 'count', ''])
            writer.writerow(['Total Pods', metrics.total_pods, 'count', ''])
            writer.writerow(['Nodes Count', metrics.nodes_count, 'count', ''])
            writer.writerow(['Monthly Cost', f'{metrics.monthly_cost:.2f}', 'USD', ''])
            writer.writerow(['Optimization Potential', f'{metrics.optimization_potential_pct:.1f}', '%', ''])
            writer.writerow(['Critical Alerts', metrics.critical_alerts, 'count', ''])
            
            # Empty row
            writer.writerow([])
            
            # Write recommendations summary
            writer.writerow(['Top Recommendations'])
            writer.writerow(['Priority', 'Title', 'Impact', 'Effort'])
            
            for rec in report_data.recommendations[:5]:  # Top 5 recommendations
                writer.writerow([
                    rec.get('priority', 'Medium'),
                    rec.get('title', 'Optimization Action'),
                    rec.get('impact', 'TBD'),
                    rec.get('effort', 'Medium')
                ])
        
        logger.info(f"✅ CSV report exported: {filepath}")
        return filepath
    
    def generate_email_summary(self, report_data: CPUReportData) -> str:
        """Generate email-friendly HTML summary"""
        
        metrics = report_data.metrics
        
        # Determine overall status
        if metrics.average_cpu_usage > 200:
            status_color = "#e74c3c"
            status_text = "🚨 CRITICAL"
        elif metrics.average_cpu_usage > 80:
            status_color = "#f39c12"
            status_text = "⚠️ WARNING"
        else:
            status_color = "#1E40AF"
            status_text = "✅ NORMAL"
        
        html_summary = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    AKS CPU Analysis Report
                </h2>
                
                <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Cluster: {metrics.cluster_id}</h3>
                    <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_text}</span></p>
                    <p><strong>Report Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #3498db; color: white;">
                        <th style="padding: 10px; text-align: left;">Metric</th>
                        <th style="padding: 10px; text-align: right;">Value</th>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px;">Average CPU Usage</td>
                        <td style="padding: 8px; text-align: right; color: {status_color}; font-weight: bold;">
                            {metrics.average_cpu_usage:.1f}%
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Peak CPU Usage</td>
                        <td style="padding: 8px; text-align: right;">{metrics.peak_cpu_usage:.1f}%</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px;">CPU Efficiency</td>
                        <td style="padding: 8px; text-align: right;">{metrics.cpu_efficiency:.1f}%</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Monthly Cost</td>
                        <td style="padding: 8px; text-align: right;">${metrics.monthly_cost:,.2f}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px;">Optimization Potential</td>
                        <td style="padding: 8px; text-align: right; color: #1E40AF; font-weight: bold;">
                            {metrics.optimization_potential_pct:.1f}%
                        </td>
                    </tr>
                </table>
                
                <div style="background-color: #e8f5e8; border-left: 4px solid #1E40AF; padding: 15px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #1E40AF;">💰 Cost Savings Opportunity</h4>
                    <p>Potential monthly savings: <strong>${report_data.cost_breakdown.get('potential_savings', 0):,.2f}</strong></p>
                    <p>Annual savings opportunity: <strong>${report_data.cost_breakdown.get('potential_savings', 0) * 12:,.2f}</strong></p>
                </div>
                
                <div style="margin-top: 30px;">
                    <h4>🔧 Top Recommendations:</h4>
                    <ol>
        """
        
        # Add top 3 recommendations
        for rec in report_data.recommendations[:3]:
            html_summary += f"""
                        <li style="margin-bottom: 10px;">
                            <strong>{rec.get('title', 'Optimization Action')}</strong>
                            <br><small style="color: #666;">
                                Priority: {rec.get('priority', 'Medium')} | 
                                Impact: {rec.get('impact', 'TBD')}
                            </small>
                        </li>
            """
        
        html_summary += f"""
                    </ol>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                    <p style="margin: 0; color: #666; font-size: 12px;">
                        Generated by AKS Cost Optimizer<br>
                        For detailed analysis, download the complete report
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_summary

# Factory function
def create_cpu_report_exporter(output_dir: str = "/tmp/cpu_reports") -> CPUReportExporter:
    """Factory function to create CPU report exporter"""
    return CPUReportExporter(output_dir)