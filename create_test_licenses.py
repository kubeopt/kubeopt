#!/usr/bin/env python3
"""
Create Test Licenses
===================
Generate test licenses for Free, Pro, and Enterprise tiers.
"""

import hashlib
import hmac
import base64
import secrets
from datetime import datetime, timedelta

class TestLicenseGenerator:
    """Generate test licenses for validation"""
    
    # Secret keys for different algorithms
    SECRETS = {
        '3M': 'kubeopt_3month_secret_2025_v1',
        '6M': 'kubeopt_6month_secret_2025_v2', 
        '12M': 'kubeopt_12month_secret_2025_v3'
    }
    
    @staticmethod
    def encode_date(date):
        """Encode date as YYMMDD"""
        return date.strftime('%y%m%d')
    
    @staticmethod
    def generate_checksum(data, secret, length=8):
        """Generate HMAC checksum"""
        signature = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        b64_sig = base64.b64encode(signature).decode('ascii')
        clean_sig = b64_sig.replace('+', '').replace('/', '').replace('=', '')
        return clean_sig[:length].upper()
    
    @classmethod
    def create_test_licenses(cls):
        """Create test licenses for all tiers"""
        
        licenses = {}
        
        # FREE TIER - 3 Month License
        tier_code = 'F'
        expiry_date = datetime.now() + timedelta(days=90)
        expiry_str = cls.encode_date(expiry_date)
        
        data = f"{tier_code}3M{expiry_str}test-free-user"
        checksum = cls.generate_checksum(data, cls.SECRETS['3M'], 8)
        free_license = f"{tier_code}3M-{checksum}-{expiry_str}"
        
        licenses['FREE'] = {
            'license_key': free_license,
            'tier': 'free',
            'duration': '3 months',
            'expires': expiry_date.strftime('%Y-%m-%d'),
            'features': ['dashboard', 'manual_analysis']
        }
        
        # PRO TIER - 6 Month License
        tier_code = 'P'
        expiry_date = datetime.now() + timedelta(days=180)
        expiry_str = cls.encode_date(expiry_date)
        features = 'DIMAES'  # Dashboard, Implementation, Manual, Auto, Email, Slack
        
        data = f"{tier_code}6M{expiry_str}{features}test-pro-user"
        checksum = cls.generate_checksum(data, cls.SECRETS['6M'], 12)
        pro_license = f"{tier_code}6M-{checksum}-{expiry_str}-{features}"
        
        licenses['PRO'] = {
            'license_key': pro_license,
            'tier': 'pro',
            'duration': '6 months',
            'expires': expiry_date.strftime('%Y-%m-%d'),
            'features': ['dashboard', 'manual_analysis', 'implementation_plan', 
                        'auto_analysis', 'email_alerts', 'slack_alerts']
        }
        
        # ENTERPRISE TIER - 12 Month License
        tier_code = 'E'
        expiry_date = datetime.now() + timedelta(days=365)
        expiry_str = cls.encode_date(expiry_date)
        features = 'F'  # Full features
        entropy = secrets.token_hex(2).upper()
        
        data = f"{tier_code}12M{expiry_str}{features}{entropy}test-enterprise-user"
        checksum = cls.generate_checksum(data, cls.SECRETS['12M'], 16)
        enterprise_license = f"{tier_code}12M-{checksum}-{expiry_str}-{features}-{entropy}"
        
        licenses['ENTERPRISE'] = {
            'license_key': enterprise_license,
            'tier': 'enterprise',
            'duration': '12 months',
            'expires': expiry_date.strftime('%Y-%m-%d'),
            'features': ['dashboard', 'manual_analysis', 'implementation_plan',
                        'auto_analysis', 'email_alerts', 'slack_alerts',
                        'enterprise_metrics', 'security_posture', 'advanced_alerts',
                        'multi_subscription']
        }
        
        return licenses

def main():
    """Generate and display test licenses"""
    
    print("🎯 kubeopt Test Licenses")
    print("=" * 60)
    print()
    
    licenses = TestLicenseGenerator.create_test_licenses()
    
    for tier, info in licenses.items():
        print(f"🔑 {tier} TIER LICENSE:")
        print(f"   License Key: {info['license_key']}")
        print(f"   Duration: {info['duration']}")
        print(f"   Expires: {info['expires']}")
        print(f"   Features: {len(info['features'])} features enabled")
        print()
    
    print("📋 COPY THESE LICENSES FOR TESTING:")
    print("-" * 60)
    print(f"FREE:       {licenses['FREE']['license_key']}")
    print(f"PRO:        {licenses['PRO']['license_key']}")
    print(f"ENTERPRISE: {licenses['ENTERPRISE']['license_key']}")
    print()
    
    print("🧪 TEST INSTRUCTIONS:")
    print("1. Go to Settings in your AKS Cost Optimizer")
    print("2. Paste any of the above license keys")
    print("3. Verify the correct tier and features are enabled")
    print("4. Check that locked features show upgrade prompts")
    print()
    
    return licenses

if __name__ == '__main__':
    licenses = main()