"""
Security Standards for AKS
==========================

Comprehensive security standards covering authentication, authorization,
network security, data protection, compliance, and security monitoring.
"""

class AuthenticationStandards:
    """Authentication and identity management standards"""
    
    # =============================================
    # AUTHENTICATION METHODS
    # =============================================
    
    # Azure AD Integration
    ENABLE_AZURE_AD_INTEGRATION = True        # Enable Azure AD integration
    ENABLE_AZURE_AD_RBAC = True               # Enable Azure AD RBAC
    ENABLE_WORKLOAD_IDENTITY = True           # Enable Workload Identity
    DISABLE_LOCAL_ACCOUNTS = True             # Disable local accounts
    
    # Multi-Factor Authentication
    REQUIRE_MFA_FOR_ADMIN = True              # Require MFA for admin access
    REQUIRE_MFA_FOR_PRODUCTION = True         # Require MFA for production
    MFA_TOKEN_LIFETIME_HOURS = 8              # 8 hours MFA token lifetime
    
    # Service Account Standards
    DISABLE_SERVICE_ACCOUNT_TOKEN_AUTOMOUNT = True # Disable automount
    SERVICE_ACCOUNT_TOKEN_EXPIRATION_HOURS = 1     # 1 hour token expiration
    ENABLE_SERVICE_ACCOUNT_TOKEN_PROJECTION = True # Enable token projection
    
    # =============================================
    # PASSWORD POLICY STANDARDS
    # =============================================
    
    # Password Requirements
    PASSWORD_MIN_LENGTH = 12                  # Minimum 12 characters
    PASSWORD_REQUIRE_UPPERCASE = True         # Require uppercase letters
    PASSWORD_REQUIRE_LOWERCASE = True         # Require lowercase letters
    PASSWORD_REQUIRE_NUMBERS = True           # Require numbers
    PASSWORD_REQUIRE_SPECIAL_CHARS = True     # Require special characters
    
    # Password Rotation
    PASSWORD_MAX_AGE_DAYS = 90                # 90 days maximum age
    PASSWORD_HISTORY_COUNT = 12               # Remember 12 previous passwords
    PASSWORD_LOCKOUT_ATTEMPTS = 5             # Lock after 5 attempts
    PASSWORD_LOCKOUT_DURATION_MINUTES = 30    # 30 minutes lockout
    
    # =============================================
    # TOKEN SECURITY STANDARDS
    # =============================================
    
    # JWT Token Standards
    JWT_TOKEN_EXPIRATION_MINUTES = 60         # 60 minutes JWT expiration
    JWT_REFRESH_TOKEN_DAYS = 7                # 7 days refresh token
    JWT_SIGNING_ALGORITHM = "RS256"           # RS256 signing algorithm
    
    # API Key Security
    API_KEY_LENGTH_BITS = 256                 # 256-bit API keys
    API_KEY_ROTATION_DAYS = 30                # 30 days rotation
    API_KEY_RATE_LIMIT_PER_MINUTE = 1000     # 1000 requests per minute


class AuthorizationStandards:
    """Authorization and access control standards"""
    
    # =============================================
    # RBAC CONFIGURATION
    # =============================================
    
    # Role-Based Access Control
    ENABLE_RBAC = True                        # Enable RBAC
    USE_PRINCIPLE_OF_LEAST_PRIVILEGE = True   # Least privilege principle
    ENABLE_NAMESPACE_ISOLATION = True         # Namespace isolation
    
    # Default Roles and Permissions
    DEFAULT_USER_PERMISSIONS = "read-only"    # Default read-only access
    ADMIN_ROLE_SEPARATION = True              # Separate admin roles
    EMERGENCY_ACCESS_ROLE = "break-glass"     # Emergency access role
    
    # Permission Boundaries
    RESTRICT_CLUSTER_ADMIN_ROLE = True        # Restrict cluster-admin
    LIMIT_NODE_ACCESS = True                  # Limit node access
    RESTRICT_PRIVILEGED_CONTAINERS = True     # Restrict privileged containers
    
    # =============================================
    # ACCESS CONTROL POLICIES
    # =============================================
    
    # Resource Access Controls
    ENABLE_RESOURCE_QUOTAS = True             # Enable resource quotas
    ENABLE_LIMIT_RANGES = True                # Enable limit ranges
    ENFORCE_POD_SECURITY_STANDARDS = True     # Pod security standards
    
    # Network Access Controls
    ENABLE_NETWORK_POLICIES = True            # Enable network policies
    DEFAULT_DENY_ALL_TRAFFIC = True           # Default deny all
    ENABLE_INGRESS_CONTROLS = True            # Ingress controls
    ENABLE_EGRESS_CONTROLS = True             # Egress controls
    
    # =============================================
    # AUDIT AND COMPLIANCE
    # =============================================
    
    # Audit Logging
    ENABLE_AUDIT_LOGGING = True               # Enable audit logging
    AUDIT_LOG_RETENTION_DAYS = 365            # 1 year retention
    AUDIT_LOG_LEVEL = "RequestResponse"       # Full audit logging
    
    # Access Reviews
    ACCESS_REVIEW_FREQUENCY_DAYS = 90         # 90 days access review
    PRIVILEGED_ACCESS_REVIEW_DAYS = 30        # 30 days privileged review
    INACTIVE_USER_CLEANUP_DAYS = 90           # 90 days inactive cleanup


class NetworkSecurityStandards:
    """Network security configuration standards"""
    
    # =============================================
    # CLUSTER NETWORK SECURITY
    # =============================================
    
    # Private Cluster Configuration
    ENABLE_PRIVATE_CLUSTER = True             # Enable private cluster
    DISABLE_PUBLIC_FQDN = False               # Control public FQDN
    ENABLE_PRIVATE_ENDPOINT = True            # Enable private endpoint
    
    # Network Segmentation
    ENABLE_VNET_INTEGRATION = True            # Enable VNet integration
    USE_AZURE_CNI = True                      # Use Azure CNI
    ENABLE_NETWORK_POLICIES = True            # Enable network policies
    DEFAULT_NETWORK_POLICY_ENGINE = "Calico"  # Default policy engine
    
    # =============================================
    # FIREWALL AND TRAFFIC CONTROL
    # =============================================
    
    # Firewall Configuration
    ENABLE_AZURE_FIREWALL = True              # Enable Azure Firewall
    ENABLE_APPLICATION_GATEWAY = True         # Enable App Gateway
    ENABLE_WAF_PROTECTION = True              # Enable WAF
    
    # Traffic Filtering
    BLOCK_OUTBOUND_INTERNET_DEFAULT = True    # Block outbound by default
    ALLOW_SPECIFIC_OUTBOUND_PORTS = [80, 443, 53] # Allowed outbound ports
    ENABLE_INGRESS_WHITELIST = True           # Ingress IP whitelist
    
    # =============================================
    # TLS/SSL STANDARDS
    # =============================================
    
    # TLS Configuration
    MINIMUM_TLS_VERSION = "1.2"               # Minimum TLS 1.2
    PREFERRED_TLS_VERSION = "1.3"             # Prefer TLS 1.3
    DISABLE_INSECURE_PROTOCOLS = True         # Disable HTTP, etc.
    
    # Certificate Management
    CERTIFICATE_ROTATION_DAYS = 90            # 90 days rotation
    USE_CERT_MANAGER = True                   # Use cert-manager
    ENABLE_CERTIFICATE_TRANSPARENCY = True    # Certificate transparency
    
    # Cipher Suite Standards
    ALLOWED_CIPHER_SUITES = [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256"
    ]
    
    # =============================================
    # SERVICE MESH SECURITY
    # =============================================
    
    # Istio Security Configuration
    ENABLE_ISTIO_MUTUAL_TLS = True            # Enable mTLS
    ISTIO_TLS_MODE = "STRICT"                 # Strict TLS mode
    ENABLE_ISTIO_AUTHORIZATION = True         # Enable authorization
    
    # Service-to-Service Communication
    REQUIRE_SERVICE_MESH_TLS = True           # Require service mesh TLS
    ENABLE_ZERO_TRUST_NETWORKING = True       # Zero trust networking
    SERVICE_IDENTITY_TTL_HOURS = 24           # 24 hours identity TTL


class ContainerSecurityStandards:
    """Container and image security standards"""
    
    # =============================================
    # IMAGE SECURITY STANDARDS
    # =============================================
    
    # Image Scanning and Validation
    SCAN_IMAGES_FOR_VULNERABILITIES = True    # Scan for vulnerabilities
    BLOCK_HIGH_SEVERITY_VULNERABILITIES = True # Block high severity
    BLOCK_CRITICAL_VULNERABILITIES = True     # Block critical
    VULNERABILITY_SCAN_ON_PUSH = True         # Scan on push
    
    # Image Registry Security
    USE_PRIVATE_REGISTRY = True               # Use private registry
    REQUIRE_SIGNED_IMAGES = True              # Require signed images
    ENABLE_IMAGE_QUARANTINE = True            # Enable quarantine
    IMAGE_RETENTION_POLICY_DAYS = 30          # 30 days retention
    
    # Base Image Standards
    USE_MINIMAL_BASE_IMAGES = True            # Use minimal images
    PROHIBIT_PRIVILEGED_IMAGES = True         # No privileged images
    REQUIRE_NON_ROOT_IMAGES = True            # Require non-root
    SCAN_BASE_IMAGE_UPDATES = True            # Scan base updates
    
    # =============================================
    # RUNTIME SECURITY STANDARDS
    # =============================================
    
    # Pod Security Standards
    POD_SECURITY_STANDARD = "restricted"      # Restricted security
    ENABLE_POD_SECURITY_POLICY = True         # Enable PSP
    ENABLE_SECURITY_CONTEXT_CONSTRAINTS = True # Enable SCC
    
    # Container Runtime Security
    RUN_AS_NON_ROOT = True                    # Run as non-root
    READ_ONLY_ROOT_FILESYSTEM = True          # Read-only root FS
    DROP_ALL_CAPABILITIES = True              # Drop all capabilities
    DISALLOW_PRIVILEGE_ESCALATION = True      # No privilege escalation
    
    # Resource Constraints
    ENFORCE_RESOURCE_LIMITS = True            # Enforce limits
    ENFORCE_RESOURCE_REQUESTS = True          # Enforce requests
    LIMIT_MEMORY_USAGE = True                 # Limit memory
    LIMIT_CPU_USAGE = True                    # Limit CPU
    
    # =============================================
    # SECRETS MANAGEMENT
    # =============================================
    
    # Secret Storage and Access
    USE_AZURE_KEY_VAULT = True                # Use Azure Key Vault
    ENABLE_KEY_VAULT_CSI = True               # Enable Key Vault CSI
    ROTATE_SECRETS_REGULARLY = True           # Regular rotation
    SECRET_ROTATION_DAYS = 30                 # 30 days rotation
    
    # Secret Security Standards
    ENCRYPT_SECRETS_AT_REST = True            # Encrypt at rest
    ENCRYPT_SECRETS_IN_TRANSIT = True         # Encrypt in transit
    AUDIT_SECRET_ACCESS = True                # Audit access
    LIMIT_SECRET_SCOPE = True                 # Limit scope
    
    # Environment Variable Security
    PROHIBIT_SECRETS_IN_ENV_VARS = True       # No secrets in env vars
    SCAN_FOR_LEAKED_SECRETS = True            # Scan for leaks
    ALERT_ON_SECRET_EXPOSURE = True           # Alert on exposure


class DataProtectionStandards:
    """Data protection and encryption standards"""
    
    # =============================================
    # ENCRYPTION STANDARDS
    # =============================================
    
    # Encryption at Rest
    ENABLE_ENCRYPTION_AT_REST = True          # Enable encryption at rest
    ENCRYPTION_ALGORITHM = "AES-256"          # AES-256 encryption
    USE_CUSTOMER_MANAGED_KEYS = True          # Customer managed keys
    KEY_ROTATION_DAYS = 90                    # 90 days key rotation
    
    # Encryption in Transit
    ENABLE_ENCRYPTION_IN_TRANSIT = True       # Enable encryption in transit
    REQUIRE_TLS_ALL_COMMUNICATIONS = True     # Require TLS
    MINIMUM_TLS_VERSION = "1.2"               # Minimum TLS 1.2
    
    # Database Encryption
    ENABLE_DATABASE_TDE = True                # Transparent Data Encryption
    ENCRYPT_DATABASE_BACKUPS = True           # Encrypt backups
    USE_ENCRYPTED_STORAGE = True              # Use encrypted storage
    
    # =============================================
    # DATA CLASSIFICATION AND HANDLING
    # =============================================
    
    # Data Classification Levels
    DATA_CLASSIFICATION_LEVELS = [
        "Public", "Internal", "Confidential", "Restricted"
    ]
    DEFAULT_DATA_CLASSIFICATION = "Internal"   # Default classification
    REQUIRE_DATA_CLASSIFICATION = True         # Require classification
    
    # Data Handling Standards
    ENCRYPT_CONFIDENTIAL_DATA = True          # Encrypt confidential
    MASK_SENSITIVE_DATA_LOGS = True           # Mask in logs
    REDACT_PII_FROM_LOGS = True              # Redact PII
    
    # =============================================
    # BACKUP AND RECOVERY SECURITY
    # =============================================
    
    # Backup Security
    ENCRYPT_BACKUPS = True                    # Encrypt backups
    SECURE_BACKUP_STORAGE = True              # Secure storage
    BACKUP_ACCESS_CONTROL = True              # Access control
    BACKUP_INTEGRITY_VERIFICATION = True      # Verify integrity
    
    # Recovery Security
    SECURE_RECOVERY_PROCESS = True            # Secure recovery
    RECOVERY_AUTHENTICATION = True            # Authenticate recovery
    RECOVERY_AUDIT_LOGGING = True             # Audit recovery


class ComplianceStandards:
    """Regulatory compliance and governance standards"""
    
    # =============================================
    # REGULATORY COMPLIANCE
    # =============================================
    
    # Compliance Frameworks
    SOC2_COMPLIANCE = True                    # SOC 2 compliance
    ISO27001_COMPLIANCE = True                # ISO 27001 compliance
    GDPR_COMPLIANCE = True                    # GDPR compliance
    HIPAA_COMPLIANCE = False                  # HIPAA (when required)
    PCI_DSS_COMPLIANCE = False                # PCI DSS (when required)
    
    # Compliance Monitoring
    CONTINUOUS_COMPLIANCE_MONITORING = True   # Continuous monitoring
    COMPLIANCE_SCAN_FREQUENCY_HOURS = 24     # Daily scans
    COMPLIANCE_REPORT_GENERATION = True       # Generate reports
    
    # =============================================
    # GOVERNANCE STANDARDS
    # =============================================
    
    # Policy Enforcement
    ENABLE_AZURE_POLICY = True                # Enable Azure Policy
    ENFORCE_SECURITY_POLICIES = True          # Enforce policies
    SECURITY_POLICY_VIOLATIONS_BLOCK = True   # Block violations
    
    # Tagging and Classification
    REQUIRE_SECURITY_TAGS = True              # Require security tags
    SECURITY_TAG_COMPLIANCE = [
        "DataClassification", "SecurityContact", "Environment"
    ]
    
    # =============================================
    # AUDIT AND LOGGING COMPLIANCE
    # =============================================
    
    # Audit Requirements
    COMPREHENSIVE_AUDIT_LOGGING = True        # Comprehensive logging
    AUDIT_LOG_IMMUTABILITY = True             # Immutable logs
    AUDIT_LOG_ENCRYPTION = True               # Encrypt logs
    AUDIT_LOG_RETENTION_YEARS = 7             # 7 years retention
    
    # Log Monitoring
    REAL_TIME_LOG_MONITORING = True           # Real-time monitoring
    SECURITY_EVENT_CORRELATION = True         # Event correlation
    AUTOMATED_INCIDENT_RESPONSE = True        # Automated response


class SecurityMonitoringStandards:
    """Security monitoring and incident response standards"""
    
    # =============================================
    # THREAT DETECTION
    # =============================================
    
    # Security Monitoring Tools
    ENABLE_AZURE_DEFENDER = True              # Enable Azure Defender
    ENABLE_AZURE_SENTINEL = True              # Enable Sentinel
    ENABLE_THREAT_DETECTION = True            # Enable threat detection
    
    # Behavioral Analysis
    ENABLE_USER_BEHAVIOR_ANALYTICS = True     # User behavior analytics
    ENABLE_ANOMALY_DETECTION = True           # Anomaly detection
    MACHINE_LEARNING_THREAT_DETECTION = True  # ML threat detection
    
    # =============================================
    # INCIDENT RESPONSE
    # =============================================
    
    # Response Time Standards
    SECURITY_INCIDENT_RESPONSE_MINUTES = 30   # 30 minutes response
    CRITICAL_INCIDENT_RESPONSE_MINUTES = 15   # 15 minutes critical
    INCIDENT_ESCALATION_MINUTES = 60          # 60 minutes escalation
    
    # Incident Management
    AUTOMATED_INCIDENT_CREATION = True        # Automated creation
    INCIDENT_SEVERITY_CLASSIFICATION = True   # Severity classification
    INCIDENT_COMMUNICATION_PLAN = True        # Communication plan
    
    # =============================================
    # VULNERABILITY MANAGEMENT
    # =============================================
    
    # Vulnerability Scanning
    VULNERABILITY_SCAN_FREQUENCY_DAYS = 7     # Weekly scans
    CONTINUOUS_VULNERABILITY_MONITORING = True # Continuous monitoring
    VULNERABILITY_ASSESSMENT_AUTOMATION = True # Automated assessment
    
    # Remediation Standards
    CRITICAL_VULNERABILITY_REMEDIATION_DAYS = 1    # 1 day critical
    HIGH_VULNERABILITY_REMEDIATION_DAYS = 7        # 7 days high
    MEDIUM_VULNERABILITY_REMEDIATION_DAYS = 30     # 30 days medium
    LOW_VULNERABILITY_REMEDIATION_DAYS = 90        # 90 days low
    
    # =============================================
    # SECURITY METRICS AND REPORTING
    # =============================================
    
    # Security KPIs
    SECURITY_INCIDENT_MTTR_HOURS = 4          # 4 hours MTTR
    VULNERABILITY_REMEDIATION_RATE = 95       # 95% remediation rate
    SECURITY_TRAINING_COMPLETION_RATE = 100   # 100% training completion
    
    # Reporting Standards
    DAILY_SECURITY_DASHBOARD = True           # Daily dashboard
    WEEKLY_SECURITY_REPORTS = True            # Weekly reports
    MONTHLY_SECURITY_METRICS = True           # Monthly metrics
    ANNUAL_SECURITY_ASSESSMENT = True         # Annual assessment


class CyberSecurityFrameworkStandards:
    """NIST Cybersecurity Framework implementation standards"""
    
    # =============================================
    # IDENTIFY FUNCTION
    # =============================================
    
    # Asset Management
    MAINTAIN_ASSET_INVENTORY = True           # Maintain inventory
    CLASSIFY_ASSETS_BY_CRITICALITY = True     # Classify assets
    IDENTIFY_ASSET_DEPENDENCIES = True        # Identify dependencies
    
    # Risk Assessment
    CONDUCT_REGULAR_RISK_ASSESSMENTS = True   # Regular assessments
    RISK_ASSESSMENT_FREQUENCY_MONTHS = 6     # 6 months frequency
    MAINTAIN_RISK_REGISTER = True             # Risk register
    
    # =============================================
    # PROTECT FUNCTION
    # =============================================
    
    # Access Control
    IMPLEMENT_IDENTITY_MANAGEMENT = True      # Identity management
    ENFORCE_ACCESS_CONTROLS = True            # Access controls
    MANAGE_PRIVILEGED_ACCOUNTS = True         # Privileged accounts
    
    # Data Security
    IMPLEMENT_DATA_GOVERNANCE = True          # Data governance
    CLASSIFY_AND_LABEL_DATA = True            # Data classification
    SECURE_DATA_LIFECYCLE = True              # Data lifecycle security
    
    # =============================================
    # DETECT FUNCTION
    # =============================================
    
    # Continuous Monitoring
    IMPLEMENT_CONTINUOUS_MONITORING = True    # Continuous monitoring
    DEPLOY_DETECTION_TOOLS = True             # Detection tools
    MONITOR_SECURITY_EVENTS = True            # Security events
    
    # =============================================
    # RESPOND FUNCTION
    # =============================================
    
    # Incident Response
    MAINTAIN_INCIDENT_RESPONSE_PLAN = True    # Response plan
    CONDUCT_INCIDENT_RESPONSE_TRAINING = True # Response training
    TEST_INCIDENT_RESPONSE_PROCEDURES = True  # Test procedures
    
    # =============================================
    # RECOVER FUNCTION
    # =============================================
    
    # Recovery Planning
    MAINTAIN_BUSINESS_CONTINUITY_PLAN = True  # Continuity plan
    IMPLEMENT_DISASTER_RECOVERY = True        # Disaster recovery
    CONDUCT_RECOVERY_TESTING = True           # Recovery testing


# =============================================
# SECURITY AUTOMATION STANDARDS
# =============================================

class SecurityAutomationStandards:
    """Security automation and DevSecOps standards"""
    
    # CI/CD Security Integration
    SECURITY_SCANNING_IN_PIPELINE = True      # Pipeline scanning
    AUTOMATED_VULNERABILITY_SCANNING = True   # Automated scanning
    SECURITY_GATE_DEPLOYMENT = True           # Security gates
    
    # Infrastructure as Code Security
    SCAN_IAC_TEMPLATES = True                 # Scan IaC templates
    SECURITY_POLICY_AS_CODE = True            # Policy as code
    AUTOMATED_COMPLIANCE_CHECKS = True        # Compliance checks
    
    # Runtime Security Automation
    AUTOMATED_THREAT_RESPONSE = True          # Automated response
    SECURITY_ORCHESTRATION = True             # Security orchestration
    INCIDENT_AUTOMATION = True                # Incident automation


# =============================================
# USAGE EXAMPLES
# =============================================
"""
USAGE EXAMPLES:
===============

from standards.security_standards import AuthenticationStandards as AuthStds
from standards.security_standards import NetworkSecurityStandards as NetSecStds

# Check authentication configuration
if not AuthStds.ENABLE_AZURE_AD_INTEGRATION:
    logger.error("Azure AD integration not enabled")

# Validate TLS configuration
if tls_version < NetSecStds.MINIMUM_TLS_VERSION:
    logger.warning(f"TLS version {tls_version} below minimum {NetSecStds.MINIMUM_TLS_VERSION}")

# Container security validation
if container_runs_as_root:
    if ContainerSecurityStandards.RUN_AS_NON_ROOT:
        logger.error("Container running as root violates security standards")

SECURITY IMPLEMENTATION GUIDELINES:
==================================

1. Implement defense in depth strategy
2. Follow principle of least privilege
3. Enable comprehensive logging and monitoring
4. Regular security assessments and updates
5. Automate security controls where possible
6. Implement zero trust architecture
7. Regular security training for team members
8. Incident response plan testing and updates
"""