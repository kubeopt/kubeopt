"""
Input Validation Layer - Security-focused input sanitization and validation
=========================================================================

Provides comprehensive input validation and sanitization for all user inputs
to prevent injection attacks, data corruption, and security vulnerabilities.
"""

import re
import logging
from typing import Any, Dict, Optional, List, Union
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    """Centralized input validation and sanitization"""
    
    # Security patterns - block dangerous content
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'on\w+\s*=',                 # Event handlers
        r'data:',                     # Data URLs
        r'vbscript:',                 # VBScript URLs
        r'eval\s*\(',                 # eval() calls
        r'expression\s*\(',           # CSS expressions
        r'\$\([^)]*\)',               # jQuery-like selectors
        r'union\s+select',            # SQL injection
        r'drop\s+table',              # SQL injection
        r'insert\s+into',             # SQL injection
        r'delete\s+from',             # SQL injection
        r'update\s+\w+\s+set',        # SQL injection
    ]
    
    # Azure resource naming patterns
    AZURE_PATTERNS = {
        'cluster_name': r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}[a-zA-Z0-9]$',
        'resource_group': r'^[a-zA-Z0-9._-]+$',
        'subscription_id': r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
        'cluster_id': r'^[a-zA-Z0-9_-]+$',
        'namespace': r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$',
    }
    
    # Pre-compile regex patterns for better performance
    _COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]
    _CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255, skip_dangerous_check: bool = False) -> str:
        """Sanitize string input - performance optimized"""
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")
        
        # Fast early return for empty strings
        if not value:
            return ""
        
        # Fast length check first
        if len(value) > max_length * 2:
            value = value[:max_length * 2]
        
        # Skip dangerous pattern check for trusted inputs to improve performance
        if not skip_dangerous_check:
            # Use a faster single combined regex check instead of multiple searches
            combined_dangerous = r'<script[^>]*>|javascript:|on\w+\s*=|eval\s*\(|union\s+select|drop\s+table'
            if re.search(combined_dangerous, value, re.IGNORECASE):
                raise ValidationError(f"Dangerous pattern detected in input")
        
        # Basic sanitization
        sanitized = value.strip()[:max_length]
        
        # Remove null bytes and control characters using pre-compiled pattern
        sanitized = InputValidator._CONTROL_CHAR_PATTERN.sub('', sanitized)
        
        return sanitized
    
    @staticmethod
    def validate_azure_resource_name(value: str, resource_type: str) -> str:
        """Validate Azure resource names according to Azure naming conventions"""
        if resource_type not in InputValidator.AZURE_PATTERNS:
            raise ValidationError(f"Unknown Azure resource type: {resource_type}")
        
        pattern = InputValidator.AZURE_PATTERNS[resource_type]
        
        if not re.match(pattern, value):
            raise ValidationError(f"Invalid {resource_type}: {value}")
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, min_val: int = None, max_val: int = None) -> int:
        """Validate and convert integer input"""
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid integer: {value}")
        
        if min_val is not None and int_val < min_val:
            raise ValidationError(f"Value {int_val} below minimum {min_val}")
        
        if max_val is not None and int_val > max_val:
            raise ValidationError(f"Value {int_val} above maximum {max_val}")
        
        return int_val
    
    @staticmethod
    def validate_float(value: Any, min_val: float = None, max_val: float = None) -> float:
        """Validate and convert float input"""
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid float: {value}")
        
        if min_val is not None and float_val < min_val:
            raise ValidationError(f"Value {float_val} below minimum {min_val}")
        
        if max_val is not None and float_val > max_val:
            raise ValidationError(f"Value {float_val} above maximum {max_val}")
        
        return float_val
    
    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """Validate and convert boolean input"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValidationError(f"Invalid boolean: {value}")
    
    @staticmethod
    def validate_list(value: Any, item_validator=None, max_items: int = 1000) -> List:
        """Validate list input"""
        if not isinstance(value, list):
            raise ValidationError(f"Expected list, got {type(value)}")
        
        if len(value) > max_items:
            raise ValidationError(f"List too long: {len(value)} > {max_items}")
        
        if item_validator:
            return [item_validator(item) for item in value]
        
        return value
    
    @staticmethod
    def validate_dict(value: Any, schema: Dict = None, max_keys: int = 100) -> Dict:
        """Validate dictionary input"""
        if not isinstance(value, dict):
            raise ValidationError(f"Expected dict, got {type(value)}")
        
        if len(value) > max_keys:
            raise ValidationError(f"Dictionary too large: {len(value)} > {max_keys}")
        
        if schema:
            validated = {}
            for key, validator in schema.items():
                if key in value:
                    try:
                        validated[key] = validator(value[key])
                    except ValidationError as e:
                        raise ValidationError(f"Invalid {key}: {e}")
                        
            return validated
        
        return value

def validate_request_args(*args_schema):
    """Decorator to validate Flask request arguments"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validated_args = {}
                
                for arg_name, validator_config in args_schema:
                    value = request.args.get(arg_name)
                    
                    if value is None:
                        if validator_config.get('required', False):
                            return jsonify({'error': f'Missing required parameter: {arg_name}'}), 400
                        
                        if 'default' in validator_config:
                            validated_args[arg_name] = validator_config['default']
                        continue
                    
                    try:
                        validator = validator_config['validator']
                        validated_args[arg_name] = validator(value)
                    except ValidationError as e:
                        return jsonify({'error': f'Invalid {arg_name}: {e}'}), 400
                
                # Add validated args to kwargs
                kwargs.update(validated_args)
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Request validation error: {e}")
                return jsonify({'error': 'Invalid request'}), 400
        
        return wrapper
    return decorator

def validate_request_json(schema: Dict):
    """Decorator to validate Flask request JSON"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                validated_data = InputValidator.validate_dict(data, schema)
                
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
                return func(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({'error': f'Invalid JSON data: {e}'}), 400
            except Exception as e:
                logger.error(f"JSON validation error: {e}")
                return jsonify({'error': 'Invalid JSON request'}), 400
        
        return wrapper
    return decorator

# Common validation schemas
CLUSTER_SCHEMA = {
    'cluster_name': lambda x: InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(x, 63), 'cluster_name'
    ),
    'resource_group': lambda x: InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(x, 90), 'resource_group'
    ),
    'subscription_id': lambda x: InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(x, 36), 'subscription_id'
    ),
}

ANALYSIS_PARAMS_SCHEMA = {
    'days': lambda x: InputValidator.validate_integer(x, 1, 365),
    'enable_pod_analysis': InputValidator.validate_boolean,
    'enable_cost_analysis': InputValidator.validate_boolean,
}

# Quick validation functions for common use cases
def validate_cluster_id(cluster_id: str) -> str:
    """Validate cluster ID"""
    return InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(cluster_id, 255), 'cluster_id'
    )

def validate_subscription_id(subscription_id: str) -> str:
    """Validate Azure subscription ID"""
    return InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(subscription_id, 36), 'subscription_id'
    )

def validate_days_parameter(days: Any) -> int:
    """Validate days parameter for analysis"""
    return InputValidator.validate_integer(days, 1, 365)

# Performance-optimized validation for internal/trusted inputs
def fast_validate_cluster_id(cluster_id: str) -> str:
    """Fast cluster ID validation for internal use - skips dangerous pattern check"""
    return InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(cluster_id, 255, skip_dangerous_check=True), 'cluster_id'
    )

def fast_validate_subscription_id(subscription_id: str) -> str:
    """Fast subscription ID validation for internal use"""
    return InputValidator.validate_azure_resource_name(
        InputValidator.sanitize_string(subscription_id, 36, skip_dangerous_check=True), 'subscription_id'
    )