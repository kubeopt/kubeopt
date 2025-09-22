#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Security Configuration & Setup
============================
Configuration management and setup utilities for the AKS Security Posture system.
Includes environment configuration, logging setup, and deployment utilities.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class SecurityConfig:
    """Security system configuration"""
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_cors_origins: List[str] = None
    
    # Database Configuration
    database_path: str = "app/security/data/security_posture.db"
    database_backup_enabled: bool = True
    database_backup_interval_hours: int = 24
    database_retention_days: int = 365
    
    # Security Analysis Configuration
    security_scan_interval_minutes: int = 60
    vulnerability_scan_interval_hours: int = 24
    policy_check_interval_minutes: int = 30
    compliance_assessment_interval_hours: int = 168  # Weekly
    
    # ML Configuration
    ml_models_enabled: bool = True
    ml_confidence_threshold: float = 0.7
    ml_training_data_retention_days: int = 90
    anomaly_detection_sensitivity: float = 0.5
    
    # Compliance Frameworks
    enabled_compliance_frameworks: List[str] = None
    compliance_evidence_retention_days: int = 2555  # 7 years
    audit_trail_retention_days: int = 2555  # 7 years
    
    # Alert Configuration
    alert_channels: Dict[str, Dict] = None
    critical_alert_immediate: bool = True
    high_alert_delay_minutes: int = 15
    medium_alert_delay_minutes: int = 60
    
    # Integration Configuration
    azure_integration_enabled: bool = True
    kubernetes_integration_enabled: bool = True
    external_scanners_enabled: bool = True
    
    # Performance Configuration
    max_concurrent_scans: int = 3
    scan_timeout_minutes: int = 30
    api_rate_limit_per_minute: int = 100
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file_path: str = "logs/security_posture.log"
    log_max_size_mb: int = 100
    log_backup_count: int = 5
    
    def __post_init__(self):
        """Initialize default values"""
        if self.api_cors_origins is None:
            self.api_cors_origins = ["*"]
        
        if self.enabled_compliance_frameworks is None:
            self.enabled_compliance_frameworks = ["CIS", "NIST", "SOC2"]
        
        if self.alert_channels is None:
            self.alert_channels = {
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#security-alerts"
                },
                "teams": {
                    "enabled": False,
                    "webhook_url": ""
                }
            }

class SecurityConfigManager:
    """Security configuration manager"""
    
    def __init__(self, config_path: str = "app/security/config.yaml"):
        """Initialize configuration manager"""
        self.config_path = Path(config_path)
        self.config: Optional[SecurityConfig] = None
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> SecurityConfig:
        """Load configuration from file or create default"""
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Convert to SecurityConfig object
                self.config = SecurityConfig(**config_data)
                logging.info(f"✅ Configuration loaded from {self.config_path}")
                
            else:
                # Create default configuration
                self.config = SecurityConfig()
                self.save_config()
                logging.info(f"📝 Default configuration created at {self.config_path}")
            
            return self.config
            
        except Exception as e:
            logging.error(f"❌ Failed to load configuration: {e}")
            self.config = SecurityConfig()
            return self.config
    
    def save_config(self):
        """Save configuration to file"""
        
        try:
            config_data = asdict(self.config)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logging.info(f"✅ Configuration saved to {self.config_path}")
            
        except Exception as e:
            logging.error(f"❌ Failed to save configuration: {e}")
            raise
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        
        try:
            if not self.config:
                self.load_config()
            
            # Update configuration attributes
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    logging.warning(f"⚠️ Unknown configuration key: {key}")
            
            # Save updated configuration
            self.save_config()
            
            logging.info(f"✅ Configuration updated with {len(updates)} changes")
            
        except Exception as e:
            logging.error(f"❌ Failed to update configuration: {e}")
            raise
    
    def get_config(self) -> SecurityConfig:
        """Get current configuration"""
        if not self.config:
            self.load_config()
        return self.config
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        
        issues = []
        
        try:
            config = self.get_config()
            
            # Validate API configuration
            if not (1 <= config.api_port <= 65535):
                issues.append("API port must be between 1 and 65535")
            
            # Validate database configuration
            if not config.database_path:
                issues.append("Database path cannot be empty")
            
            # Validate intervals
            if config.security_scan_interval_minutes < 1:
                issues.append("Security scan interval must be at least 1 minute")
            
            if config.vulnerability_scan_interval_hours < 1:
                issues.append("Vulnerability scan interval must be at least 1 hour")
            
            # Validate ML configuration
            if not (0.0 <= config.ml_confidence_threshold <= 1.0):
                issues.append("ML confidence threshold must be between 0.0 and 1.0")
            
            if not (0.0 <= config.anomaly_detection_sensitivity <= 1.0):
                issues.append("Anomaly detection sensitivity must be between 0.0 and 1.0")
            
            # Validate compliance frameworks
            valid_frameworks = {"CIS", "NIST", "SOC2", "ISO27001", "PCI-DSS", "HIPAA"}
            invalid_frameworks = set(config.enabled_compliance_frameworks) - valid_frameworks
            if invalid_frameworks:
                issues.append(f"Invalid compliance frameworks: {invalid_frameworks}")
            
            # Validate retention periods
            if config.database_retention_days < 1:
                issues.append("Database retention days must be at least 1")
            
            if config.compliance_evidence_retention_days < 365:
                issues.append("Compliance evidence retention should be at least 365 days")
            
            # Validate performance configuration
            if config.max_concurrent_scans < 1:
                issues.append("Max concurrent scans must be at least 1")
            
            if config.scan_timeout_minutes < 1:
                issues.append("Scan timeout must be at least 1 minute")
            
            # Validate logging configuration
            valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if config.log_level not in valid_log_levels:
                issues.append(f"Log level must be one of: {valid_log_levels}")
            
            logging.info(f"Configuration validation: {len(issues)} issues found")
            return issues
            
        except Exception as e:
            issues.append(f"Configuration validation failed: {e}")
            return issues

class SecuritySetupManager:
    """Security system setup and initialization manager"""
    
    def __init__(self, config_manager: SecurityConfigManager):
        """Initialize setup manager"""
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
    def setup_logging(self):
        """Setup logging configuration"""
        
        try:
            # Create logs directory
            log_path = Path(self.config.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.config.log_file_path),
                    logging.StreamHandler()
                ]
            )
            
            # Configure log rotation
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                self.config.log_file_path,
                maxBytes=self.config.log_max_size_mb * 1024 * 1024,
                backupCount=self.config.log_backup_count
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            
            # Get root logger and configure
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            root_logger.addHandler(file_handler)
            root_logger.addHandler(logging.StreamHandler())
            
            logging.info("✅ Logging configuration setup complete")
            
        except Exception as e:
            print(f"❌ Failed to setup logging: {e}")
            raise
    
    def setup_directories(self):
        """Setup required directories"""
        
        try:
            directories = [
                "app/security",
                "app/security/data",
                "app/security/reports",
                "app/security/backups",
                "logs",
                "temp"
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logging.info(f"📁 Directory created: {directory}")
            
            logging.info("✅ Directory setup complete")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup directories: {e}")
            raise
    
    def setup_database(self):
        """Setup database"""
        
        try:
            from .database_schema import initialize_security_database
            
            success = initialize_security_database(self.config.database_path)
            
            if success:
                logging.info("✅ Database setup complete")
            else:
                logging.error("❌ Database setup failed")
                raise RuntimeError("Database initialization failed")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup database: {e}")
            raise
    
    def setup_environment_variables(self):
        """Setup environment variables"""
        
        try:
            env_vars = {
                'SECURITY_API_HOST': self.config.api_host,
                'SECURITY_API_PORT': str(self.config.api_port),
                'SECURITY_DATABASE_PATH': self.config.database_path,
                'SECURITY_LOG_LEVEL': self.config.log_level,
                'SECURITY_ML_ENABLED': str(self.config.ml_models_enabled),
                'SECURITY_AZURE_INTEGRATION': str(self.config.azure_integration_enabled)
            }
            
            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value
                logging.info(f"🔧 Environment variable set: {key}")
            
            logging.info("✅ Environment variables setup complete")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup environment variables: {e}")
            raise
    
    def validate_dependencies(self) -> List[str]:
        """Validate system dependencies"""
        
        issues = []
        
        try:
            # Check Python version
            import sys
            if sys.version_info < (3, 8):
                issues.append("Python 3.8 or higher is required")
            
            # Check required packages
            required_packages = [
                'fastapi', 'uvicorn', 'sqlite3', 'pandas', 'numpy',
                'scikit-learn', 'asyncio', 'aiohttp', 'pydantic',
                'yaml', 'requests'
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    issues.append(f"Required package missing: {package}")
            
            # Check optional packages
            optional_packages = [
                'matplotlib', 'seaborn', 'plotly', 'reportlab'
            ]
            
            missing_optional = []
            for package in optional_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_optional.append(package)
            
            if missing_optional:
                issues.append(f"Optional packages missing (reduced functionality): {missing_optional}")
            
            # Check system resources
            import psutil
            
            # Check available memory
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            if available_memory_gb < 2:
                issues.append("Insufficient memory: at least 2GB recommended")
            
            # Check available disk space
            available_disk_gb = psutil.disk_usage('.').free / (1024**3)
            if available_disk_gb < 5:
                issues.append("Insufficient disk space: at least 5GB recommended")
            
            logging.info(f"Dependency validation: {len(issues)} issues found")
            return issues
            
        except Exception as e:
            issues.append(f"Dependency validation failed: {e}")
            return issues
    
    def create_sample_configuration(self):
        """Create sample configuration files"""
        
        try:
            # Create Docker Compose configuration
            docker_compose = {
                'version': '3.8',
                'services': {
                    'security-api': {
                        'build': '.',
                        'ports': [f'{self.config.api_port}:{self.config.api_port}'],
                        'environment': [
                            f'SECURITY_API_PORT={self.config.api_port}',
                            f'SECURITY_DATABASE_PATH={self.config.database_path}',
                            f'SECURITY_LOG_LEVEL={self.config.log_level}'
                        ],
                        'volumes': [
                            './app:/app',
                            './logs:/logs',
                            './data:/data'
                        ],
                        'restart': 'unless-stopped'
                    }
                }
            }
            
            # Save Docker Compose file
            with open('docker-compose.security.yml', 'w') as f:
                yaml.dump(docker_compose, f, default_flow_style=False, indent=2)
            
            # Create Dockerfile
            dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data temp

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "app.security.security_dashboard_api"]
"""
            
            with open('Dockerfile.security', 'w') as f:
                f.write(dockerfile_content)
            
            # Create requirements.txt
            requirements = [
                "fastapi>=0.68.0",
                "uvicorn>=0.15.0",
                "pydantic>=1.8.0",
                "pandas>=1.3.0",
                "numpy>=1.21.0",
                "scikit-learn>=1.0.0",
                "aiohttp>=3.8.0",
                "requests>=2.26.0",
                "PyYAML>=6.0",
                "python-multipart>=0.0.5",
                "psutil>=5.8.0",
                "networkx>=2.6.0",
                "cryptography>=3.4.0",
                "packaging>=21.0",
                "semver>=2.13.0",
                "reportlab>=3.6.0",
                "matplotlib>=3.4.0",
                "seaborn>=0.11.0"
            ]
            
            with open('requirements.security.txt', 'w') as f:
                f.write('\n'.join(requirements))
            
            # Create systemd service file
            service_content = f"""
[Unit]
Description=AKS Security Posture Service
After=network.target

[Service]
Type=simple
User=aks-security
WorkingDirectory=/opt/aks-security
Environment=PATH=/opt/aks-security/venv/bin
Environment=SECURITY_API_PORT={self.config.api_port}
Environment=SECURITY_DATABASE_PATH={self.config.database_path}
ExecStart=/opt/aks-security/venv/bin/python -m app.security.security_dashboard_api
Restart=always

[Install]
WantedBy=multi-user.target
"""
            
            with open('aks-security.service', 'w') as f:
                f.write(service_content)
            
            logging.info("✅ Sample configuration files created")
            
        except Exception as e:
            logging.error(f"❌ Failed to create sample configuration: {e}")
            raise
    
    def run_complete_setup(self) -> bool:
        """Run complete system setup"""
        
        try:
            logging.info("🚀 Starting complete security system setup...")
            
            # Validate configuration
            config_issues = self.config_manager.validate_config()
            if config_issues:
                logging.error(f"❌ Configuration issues found: {config_issues}")
                return False
            
            # Validate dependencies
            dependency_issues = self.validate_dependencies()
            if any("missing" in issue for issue in dependency_issues):
                logging.error(f"❌ Critical dependency issues: {dependency_issues}")
                return False
            
            if dependency_issues:
                logging.warning(f"⚠️ Non-critical dependency issues: {dependency_issues}")
            
            # Setup components
            self.setup_logging()
            self.setup_directories()
            self.setup_database()
            self.setup_environment_variables()
            self.create_sample_configuration()
            
            logging.info("✅ Complete security system setup finished successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Complete setup failed: {e}")
            return False

def create_config_manager(config_path: str = "app/security/config.yaml") -> SecurityConfigManager:
    """Create security configuration manager"""
    return SecurityConfigManager(config_path)

def create_setup_manager(config_manager: SecurityConfigManager) -> SecuritySetupManager:
    """Create security setup manager"""
    return SecuritySetupManager(config_manager)

def run_security_setup(config_path: str = "app/security/config.yaml") -> bool:
    """Run complete security system setup"""
    config_manager = create_config_manager(config_path)
    setup_manager = create_setup_manager(config_manager)
    return setup_manager.run_complete_setup()

# CLI interface
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="AKS Security Posture Setup")
    parser.add_argument("--config", default="app/security/config.yaml", help="Configuration file path")
    parser.add_argument("--validate", action="store_true", help="Validate configuration only")
    parser.add_argument("--setup", action="store_true", help="Run complete setup")
    parser.add_argument("--create-config", action="store_true", help="Create default configuration")
    
    args = parser.parse_args()
    
    try:
        config_manager = create_config_manager(args.config)
        
        if args.create_config:
            config_manager.save_config()
            print(f"✅ Default configuration created at {args.config}")
        
        elif args.validate:
            issues = config_manager.validate_config()
            if issues:
                print("❌ Configuration validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("✅ Configuration validation passed")
        
        elif args.setup:
            setup_manager = create_setup_manager(config_manager)
            success = setup_manager.run_complete_setup()
            if success:
                print("✅ Security system setup completed successfully")
                print("\nNext steps:")
                print("1. Review the configuration in app/security/config.yaml")
                print("2. Start the API server: python -m app.security.security_dashboard_api")
                print("3. Access the dashboard at http://localhost:8000")
            else:
                print("❌ Security system setup failed")
                sys.exit(1)
        
        else:
            print("Use --help for available options")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)