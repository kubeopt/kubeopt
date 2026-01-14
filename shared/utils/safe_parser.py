"""
Safe Parsing Utilities
======================
Centralized parsing logic to handle real-world data formats safely.
Follows .clauderc principles: fail fast, no silent failures, no defaults.
"""

import re
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)


class SafeParser:
    """Safe parsing utilities that handle real-world data formats."""
    
    @staticmethod
    def parse_percentage(value: str) -> Optional[int]:
        """
        Parse percentage values that may have % suffix.
        
        Args:
            value: String value like "89%" or "89" or "N/A"
            
        Returns:
            Integer percentage value or None if invalid
            
        Raises:
            ValueError: If value format is invalid (per .clauderc - fail fast)
        """
        if not value or value in ['<none>', 'N/A', '-']:
            return None
            
        # Strip percentage sign if present
        clean_value = value.rstrip('%').strip()
        
        # Validate it's a number
        if not clean_value.replace('.', '', 1).isdigit():
            raise ValueError(f"Invalid percentage format: {value}")
            
        # Convert to int (rounding if float)
        try:
            return int(float(clean_value))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert percentage to integer: {value}") from e
    
    @staticmethod
    def parse_cpu(cpu_str: str) -> float:
        """
        Parse CPU values in various formats (m suffix, percentage, etc).
        
        Args:
            cpu_str: String like "100m", "0.1", "50%"
            
        Returns:
            Float CPU value in cores
            
        Raises:
            ValueError: If format is invalid (per .clauderc - fail fast)
        """
        if not cpu_str or cpu_str in ['<none>', 'N/A', '-']:
            raise ValueError(f"Missing or invalid CPU value: {cpu_str}")
        
        cpu_str = cpu_str.strip()
        
        # Handle millicores (e.g., "100m")
        if cpu_str.endswith('m'):
            try:
                return float(cpu_str[:-1]) / 1000
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid millicore format: {cpu_str}") from e
        
        # Handle percentage (e.g., "50%")
        if cpu_str.endswith('%'):
            try:
                return float(cpu_str[:-1]) / 100
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid CPU percentage format: {cpu_str}") from e
        
        # Handle plain number
        try:
            return float(cpu_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid CPU format: {cpu_str}") from e
    
    @staticmethod
    def parse_memory(mem_str: str) -> float:
        """
        Parse memory values in various formats (Ki, Mi, Gi, Ti suffixes).
        
        Args:
            mem_str: String like "1Gi", "512Mi", "1024Ki"
            
        Returns:
            Float memory value in bytes
            
        Raises:
            ValueError: If format is invalid (per .clauderc - fail fast)
        """
        if not mem_str or mem_str in ['<none>', 'N/A', '-']:
            raise ValueError(f"Missing or invalid memory value: {mem_str}")
        
        mem_str = mem_str.strip()
        
        # Units mapping
        units = {
            'Ki': 1024,
            'Mi': 1024 * 1024,
            'Gi': 1024 * 1024 * 1024,
            'Ti': 1024 * 1024 * 1024 * 1024,
            'K': 1000,
            'M': 1000 * 1000,
            'G': 1000 * 1000 * 1000,
            'T': 1000 * 1000 * 1000 * 1000
        }
        
        # Find unit suffix
        for unit, multiplier in units.items():
            if mem_str.endswith(unit):
                try:
                    value = float(mem_str[:-len(unit)])
                    return value * multiplier
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid memory format: {mem_str}") from e
        
        # No unit - assume bytes
        try:
            return float(mem_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid memory format: {mem_str}") from e
    
    @staticmethod
    def safe_array_access(array: list, index: int, field_name: str) -> Optional[str]:
        """
        Safely access array element with bounds checking.
        
        Args:
            array: List to access
            index: Index to access
            field_name: Name of field being accessed (for error messages)
            
        Returns:
            Value at index or None if out of bounds
            
        Raises:
            ValueError: If array access is invalid (per .clauderc - fail fast)
        """
        if not isinstance(array, list):
            raise ValueError(f"Expected list for {field_name}, got {type(array)}")
        
        if index < 0:
            raise ValueError(f"Negative index {index} for {field_name}")
        
        if index >= len(array):
            raise ValueError(f"Index {index} out of bounds for {field_name} (length {len(array)})")
        
        value = array[index]
        
        # Handle special markers
        if value in ['<none>', 'N/A', '-', '']:
            return None
            
        return value
    
    @staticmethod
    def parse_replica_count(value: str) -> int:
        """
        Parse replica count values.
        
        Args:
            value: String replica count
            
        Returns:
            Integer replica count
            
        Raises:
            ValueError: If format is invalid
        """
        if not value or value in ['<none>', 'N/A', '-']:
            raise ValueError(f"Missing replica count: {value}")
        
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid replica count format: {value}") from e