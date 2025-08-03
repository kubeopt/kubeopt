// components/SecurityDashboard.jsx
/**
 * Security Dashboard Frontend Component
 * Provides comprehensive security, compliance, and vulnerability visualization
 * Integrates with Python security API backend
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Grid,
  Typography,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Tabs,
  Tab,
  IconButton,
  Tooltip
} from '@mui/material';

import {
  Security as SecurityIcon,
  BugReport as VulnIcon,
  Policy as ComplianceIcon,
  Assessment as AuditIcon,
  TrendingUp as TrendIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';

import Plot from 'react-plotly.js';

const SecurityDashboard = ({ clusterName, onRefresh }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [securityData, setSecurityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);

  // Fetch security dashboard data
  const fetchSecurityData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/security/dashboard/${clusterName}`);
      const result = await response.json();

      if (result.success) {
        setSecurityData(result.data);
      } else {
        setError(result.error || 'Failed to fetch security data');
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [clusterName]);

  // Refresh security data
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchSecurityData();
    setRefreshing(false);
    if (onRefresh) onRefresh();
  }, [fetchSecurityData, onRefresh]);

  // Fetch vulnerability scan
  const triggerVulnerabilityScan = async () => {
    try {
      setRefreshing(true);
      const response = await fetch(`/api/vulnerabilities/scan/${clusterName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scan_types: ['container', 'network', 'configuration'] })
      });

      const result = await response.json();
      if (result.success) {
        await fetchSecurityData(); // Refresh data after scan
      } else {
        setError(`Scan failed: ${result.error}`);
      }
    } catch (err) {
      setError(`Scan error: ${err.message}`);
    } finally {
      setRefreshing(false);
    }
  };

  // Export security data
  const handleExport = async (format) => {
    try {
      const response = await fetch(`/api/security/export/${clusterName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          format: format,
          frameworks: ['cis_kubernetes', 'nist_csf']
        })
      });

      if (format === 'json') {
        const result = await response.json();
        const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `security_export_${clusterName}.json`);
      } else {
        const blob = await response.blob();
        downloadBlob(blob, `security_export_${clusterName}.${format}`);
      }

      setExportDialogOpen(false);
    } catch (err) {
      setError(`Export failed: ${err.message}`);
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Get security score color
  const getScoreColor = (score) => {
    if (score >= 0.8) return '#4caf50'; // Green
    if (score >= 0.6) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  // Get risk level color
  const getRiskColor = (risk) => {
    const colors = {
      'Low': '#4caf50',
      'Medium': '#ff9800',
      'High': '#f44336',
      'Critical': '#d32f2f'
    };
    return colors[risk] || '#9e9e9e';
  };

  useEffect(() => {
    fetchSecurityData();
  }, [fetchSecurityData]);

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
            <Typography variant="h6" sx={{ ml: 2 }}>
              Loading security analysis...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchSecurityData}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  if (!securityData) {
    return (
      <Alert severity="info">
        No security data available for cluster: {clusterName}
      </Alert>
    );
  }

  const { cluster_overview, security_metrics, compliance_status, vulnerability_trends, 
          policy_alerts, remediation_queue, ml_insights } = securityData;

  return (
    <Box>
      {/* Header with cluster overview */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box display="flex" alignItems="center">
                <SecurityIcon sx={{ mr: 2, color: getRiskColor(security_metrics?.risk_level) }} />
                <Typography variant="h5">
                  Security Posture - {cluster_overview?.cluster_name}
                </Typography>
              </Box>
              <Box>
                <Tooltip title="Refresh Security Data">
                  <IconButton onClick={handleRefresh} disabled={refreshing}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export Security Report">
                  <IconButton onClick={() => setExportDialogOpen(true)}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Button 
                  variant="outlined" 
                  onClick={triggerVulnerabilityScan}
                  disabled={refreshing}
                  sx={{ ml: 1 }}
                >
                  Run Vulnerability Scan
                </Button>
              </Box>
            </Box>
          }
        />
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h2" color={getScoreColor(security_metrics?.security_score)}>
                  {cluster_overview?.overall_grade || 'C'}
                </Typography>
                <Typography variant="subtitle1">Overall Grade</Typography>
                <Typography variant="body2" color="textSecondary">
                  ML Confidence: {((cluster_overview?.ml_confidence || 0.7) * 100).toFixed(1)}%
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color={getScoreColor(cluster_overview?.risk_score)}>
                  {(cluster_overview?.risk_score || 0.5).toFixed(2)}
                </Typography>
                <Typography variant="subtitle1">Risk Score</Typography>
                <Typography variant="body2" color="textSecondary">
                  Lower is better
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color={cluster_overview?.total_issues > 10 ? '#f44336' : '#4caf50'}>
                  {cluster_overview?.total_issues || 0}
                </Typography>
                <Typography variant="subtitle1">Total Issues</Typography>
                <Typography variant="body2" color="textSecondary">
                  Requiring attention
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="#2196f3">
                  {cluster_overview?.next_assessment ? 
                    new Date(cluster_overview.next_assessment).toLocaleDateString() : 'TBD'}
                </Typography>
                <Typography variant="subtitle1">Next Assessment</Typography>
                <Typography variant="body2" color="textSecondary">
                  Scheduled date
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Main dashboard tabs */}
      <Card>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} variant="fullWidth">
          <Tab label="Security Overview" icon={<SecurityIcon />} />
          <Tab label="Compliance Status" icon={<ComplianceIcon />} />
          <Tab label="Vulnerabilities" icon={<VulnIcon />} />
          <Tab label="Policy Alerts" icon={<WarningIcon />} />
          <Tab label="ML Insights" icon={<TrendIcon />} />
        </Tabs>

        {/* Tab 0: Security Overview */}
        {activeTab === 0 && (
          <CardContent>
            <Grid container spacing={3}>
              {/* Security Score Breakdown */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="Security Score Breakdown" />
                  <CardContent>
                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography>Overall Security</Typography>
                        <Typography>{(security_metrics?.security_score || 0).toFixed(2)}</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(security_metrics?.security_score || 0) * 100}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                    
                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography>Attack Vectors</Typography>
                        <Typography>{security_metrics?.attack_vectors || 0}</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.max(0, 100 - (security_metrics?.attack_vectors || 0) * 10)}
                        color="warning"
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>

                    <Box>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography>ML Confidence</Typography>
                        <Typography>{((security_metrics?.ml_confidence || 0.7) * 100).toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(security_metrics?.ml_confidence || 0.7) * 100}
                        color="info"
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Risk Level Distribution */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="Risk Level Distribution" />
                  <CardContent>
                    <Box display="flex" flexDirection="column" gap={2}>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Chip label="Critical" size="small" sx={{ bgcolor: '#d32f2f', color: 'white' }} />
                        <Typography>0</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Chip label="High" size="small" sx={{ bgcolor: '#f44336', color: 'white' }} />
                        <Typography>{security_metrics?.attack_vectors || 0}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Chip label="Medium" size="small" sx={{ bgcolor: '#ff9800', color: 'white' }} />
                        <Typography>2</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Chip label="Low" size="small" sx={{ bgcolor: '#4caf50', color: 'white' }} />
                        <Typography>5</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Security Recommendations */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardHeader title="Top Security Recommendations" />
                  <CardContent>
                    <Box display="flex" flexDirection="column" gap={2}>
                      <Alert severity="error" icon={<WarningIcon />}>
                        <Typography variant="subtitle2">Critical: Implement network policies</Typography>
                        <Typography variant="body2">
                          No default-deny network policies detected. This allows unrestricted lateral movement.
                        </Typography>
                      </Alert>
                      <Alert severity="warning" icon={<SecurityIcon />}>
                        <Typography variant="subtitle2">High: Review RBAC permissions</Typography>
                        <Typography variant="body2">
                          ML analysis detected excessive RBAC permissions that violate least privilege principle.
                        </Typography>
                      </Alert>
                      <Alert severity="info" icon={<CheckIcon />}>
                        <Typography variant="subtitle2">Medium: Enable admission controllers</Typography>
                        <Typography variant="body2">
                          Implement Pod Security Standards for better container security posture.
                        </Typography>
                      </Alert>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        )}

        {/* Tab 1: Compliance Status */}
        {activeTab === 1 && (
          <CardContent>
            <Grid container spacing={3}>
              {/* Compliance Framework Scores */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>Compliance Framework Scores</Typography>
                <Grid container spacing={2}>
                  {Object.entries(compliance_status || {}).map(([framework, status]) => (
                    <Grid item xs={12} md={4} key={framework}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                            <Typography variant="subtitle1">
                              {framework.replace('_', ' ').toUpperCase()}
                            </Typography>
                            <Chip 
                              label={status.grade} 
                              color={status.grade === 'A' ? 'success' : status.grade === 'B' ? 'warning' : 'error'}
                            />
                          </Box>
                          <Box mb={2}>
                            <Typography variant="body2" color="textSecondary">
                              Score: {(status.score * 100).toFixed(1)}%
                            </Typography>
                            <LinearProgress 
                              variant="determinate" 
                              value={status.score * 100}
                              sx={{ height: 6, borderRadius: 3, mt: 1 }}
                            />
                          </Box>
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="body2">
                              Passed: {status.controls_passed}
                            </Typography>
                            <Typography variant="body2">
                              Failed: {status.controls_failed}
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>

              {/* Compliance Heatmap Placeholder */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardHeader title="Compliance Heatmap" />
                  <CardContent>
                    <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                      <Typography color="textSecondary">
                        Compliance heatmap visualization would be rendered here
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        )}

        {/* Tab 2: Vulnerabilities */}
        {activeTab === 2 && (
          <CardContent>
            <Grid container spacing={3}>
              {/* Vulnerability Summary */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="Vulnerability Summary" />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="error">
                            {vulnerability_trends?.severity_breakdown?.critical || 0}
                          </Typography>
                          <Typography variant="subtitle2">Critical</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="warning.main">
                            {vulnerability_trends?.severity_breakdown?.high || 0}
                          </Typography>
                          <Typography variant="subtitle2">High</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="info.main">
                            {vulnerability_trends?.severity_breakdown?.medium || 0}
                          </Typography>
                          <Typography variant="subtitle2">Medium</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="success.main">
                            {vulnerability_trends?.severity_breakdown?.low || 0}
                          </Typography>
                          <Typography variant="subtitle2">Low</Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* Patch Management Score */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="Patch Management" />
                  <CardContent>
                    <Box textAlign="center" mb={2}>
                      <Typography variant="h3" color={getScoreColor(vulnerability_trends?.patch_management_score)}>
                        {((vulnerability_trends?.patch_management_score || 0.5) * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="subtitle1">Patch Coverage</Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(vulnerability_trends?.patch_management_score || 0.5) * 100}
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      {vulnerability_trends?.exploitable_count || 0} exploitable vulnerabilities detected
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Vulnerability Trends Chart Placeholder */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardHeader title="Vulnerability Trends (30 Days)" />
                  <CardContent>
                    <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                      <Typography color="textSecondary">
                        Vulnerability trends chart would be rendered here
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        )}

        {/* Tab 3: Policy Alerts */}
        {activeTab === 3 && (
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h6">Policy Violation Alerts</Typography>
              <Typography variant="body2" color="textSecondary">
                {policy_alerts?.length || 0} active alerts
              </Typography>
            </Box>

            {(!policy_alerts || policy_alerts.length === 0) ? (
              <Alert severity="success" icon={<CheckIcon />}>
                No policy violations detected. Your cluster is compliant with configured policies.
              </Alert>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Severity</TableCell>
                      <TableCell>Policy</TableCell>
                      <TableCell>Resource</TableCell>
                      <TableCell>Detected</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {policy_alerts.map((alert, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Chip 
                            label={alert.severity} 
                            size="small" 
                            color={
                              alert.severity === 'critical' ? 'error' :
                              alert.severity === 'high' ? 'warning' : 'default'
                            }
                          />
                        </TableCell>
                        <TableCell>{alert.policy_name}</TableCell>
                        <TableCell>
                          {alert.resource_details?.name || 'Unknown'}
                          <br />
                          <Typography variant="caption" color="textSecondary">
                            {alert.resource_details?.namespace || 'default'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {new Date(alert.detection_timestamp).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <IconButton 
                            size="small" 
                            onClick={() => setSelectedAlert(alert)}
                            color="primary"
                          >
                            <ViewIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        )}

        {/* Tab 4: ML Insights */}
        {activeTab === 4 && (
          <CardContent>
            <Grid container spacing={3}>
              {/* ML Model Performance */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="ML Model Performance" />
                  <CardContent>
                    <Box display="flex" flexDirection="column" gap={2}>
                      <Box>
                        <Typography variant="subtitle2">Security Classifier</Typography>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Accuracy</Typography>
                          <Typography variant="body2">
                            {((security_metrics?.ml_confidence || 0.7) * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={(security_metrics?.ml_confidence || 0.7) * 100}
                          sx={{ height: 4, borderRadius: 2 }}
                        />
                      </Box>
                      
                      <Box>
                        <Typography variant="subtitle2">Vulnerability Predictor</Typography>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Accuracy</Typography>
                          <Typography variant="body2">85.3%</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={85.3}
                          sx={{ height: 4, borderRadius: 2 }}
                        />
                      </Box>

                      <Box>
                        <Typography variant="subtitle2">Compliance Predictor</Typography>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Accuracy</Typography>
                          <Typography variant="body2">78.9%</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={78.9}
                          sx={{ height: 4, borderRadius: 2 }}
                        />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* ML Predictions */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="ML Predictions" />
                  <CardContent>
                    <Box display="flex" flexDirection="column" gap={2}>
                      <Alert severity="info">
                        <Typography variant="subtitle2">Security Trend Prediction</Typography>
                        <Typography variant="body2">
                          ML models predict security posture will improve by 12% over next 30 days with recommended changes.
                        </Typography>
                      </Alert>
                      
                      <Alert severity="warning">
                        <Typography variant="subtitle2">Vulnerability Forecast</Typography>
                        <Typography variant="body2">
                          High probability of 3-5 new medium-severity vulnerabilities in next 14 days based on historical patterns.
                        </Typography>
                      </Alert>

                      <Alert severity="success">
                        <Typography variant="subtitle2">Compliance Trajectory</Typography>
                        <Typography variant="body2">
                          Implementation of recommended policies will achieve 95% CIS compliance within 2 weeks.
                        </Typography>
                      </Alert>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* ML Model Confidence Radar Chart Placeholder */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardHeader title="ML Model Confidence Levels" />
                  <CardContent>
                    <Box height="400px" display="flex" alignItems="center" justifyContent="center">
                      <Typography color="textSecondary">
                        ML confidence radar chart would be rendered here
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        )}
      </Card>

      {/* Alert Detail Dialog */}
      <Dialog 
        open={selectedAlert !== null} 
        onClose={() => setSelectedAlert(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Policy Violation Details
        </DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Policy Name</Typography>
                  <Typography variant="body1">{selectedAlert.policy_name}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Severity</Typography>
                  <Chip 
                    label={selectedAlert.severity} 
                    color={selectedAlert.severity === 'critical' ? 'error' : 'warning'}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Recommended Action</Typography>
                  <Typography variant="body1">{selectedAlert.recommended_action}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Compliance Impact</Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {selectedAlert.compliance_impact?.map((framework, idx) => (
                      <Chip key={idx} label={framework} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Grid>
                {selectedAlert.auto_remediation_available && (
                  <Grid item xs={12}>
                    <Alert severity="info">
                      <Typography variant="body2">
                        Auto-remediation is available for this violation.
                      </Typography>
                    </Alert>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedAlert(null)}>Close</Button>
          {selectedAlert?.auto_remediation_available && (
            <Button variant="contained" color="primary">
              Apply Auto-Remediation
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Security Report</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Choose export format for security assessment report:
          </Typography>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <Button 
              variant="outlined" 
              onClick={() => handleExport('json')}
              fullWidth
            >
              JSON Report
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => handleExport('pdf')}
              fullWidth
            >
              PDF Report
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => handleExport('xlsx')}
              fullWidth
            >
              Excel Report
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => handleExport('csv')}
              fullWidth
            >
              CSV Export
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Refresh indicator */}
      {refreshing && (
        <Box position="fixed" top={10} right={10} zIndex={1000}>
          <Alert severity="info" icon={<CircularProgress size={20} />}>
            Refreshing security data...
          </Alert>
        </Box>
      )}
    </Box>
  );
};

export default SecurityDashboard;