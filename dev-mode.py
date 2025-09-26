#!/usr/bin/env python3
"""
Development Mode Utility
========================
Easily switch between development and production license modes.
"""

import os
import sys
import argparse

def set_dev_mode(enabled=True):
    """Enable or disable development mode"""
    env_file = '.env.development'
    
    if enabled:
        # Create/update .env.development file
        env_content = """# Development Environment Configuration
# ====================================
# This file enables full Enterprise features for development

# Development License - Full Enterprise Access
KUBEVISTA_LICENSE_KEY=ENT-dev12345-NEVER
KUBEVISTA_DEV_MODE=true

# Optional: Override specific features for testing
# KUBEVISTA_FORCE_FREE_TIER=false
# KUBEVISTA_BYPASS_LICENSE=true"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("🔧 Development mode ENABLED")
        print("✅ Full Enterprise features available")
        print("📁 Created .env.development file")
        print("\n💡 To use: export $(cat .env.development | xargs)")
        
    else:
        # Remove development file
        if os.path.exists(env_file):
            os.remove(env_file)
            print("🔒 Development mode DISABLED")
            print("📁 Removed .env.development file")
        else:
            print("⚠️ Development mode was already disabled")

def set_specific_tier(tier):
    """Set a specific tier for testing"""
    tier_map = {
        'free': 'FREE-test1234-NEVER',
        'pro': 'PRO-test1234-NEVER', 
        'enterprise': 'ENT-test1234-NEVER'
    }
    
    if tier not in tier_map:
        print(f"❌ Invalid tier: {tier}")
        print("Available tiers: free, pro, enterprise")
        return
    
    env_content = f"""# Development Environment Configuration
# ====================================
# Testing {tier.upper()} tier

KUBEVISTA_LICENSE_KEY={tier_map[tier]}
KUBEVISTA_DEV_MODE=true"""
    
    with open('.env.development', 'w') as f:
        f.write(env_content)
    
    print(f"🎯 Set development tier to: {tier.upper()}")
    print("💡 To use: export $(cat .env.development | xargs)")

def show_current_status():
    """Show current license status"""
    try:
        # Load environment variables first
        env_file = '.env.development'
        if os.path.exists(env_file):
            print("🔧 Loading development environment...")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Development environment loaded")
        
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from infrastructure.services.license_manager import license_manager
        
        current_tier = license_manager.get_current_tier()
        enabled_features = license_manager.get_enabled_features()
        license_info = license_manager.get_license_info()
        
        print("📊 Current License Status:")
        print(f"   Tier: {current_tier.value.upper()}")
        print(f"   Valid: {license_info['is_valid']}")
        print(f"   Expires: {license_info['expires'] or 'Never'}")
        print(f"   Features: {len(enabled_features)}")
        
        if license_info.get('dev_mode'):
            print("   🔧 DEVELOPMENT MODE ACTIVE")
        
        print(f"\n✅ Enabled Features:")
        for feature in enabled_features:
            print(f"   - {feature.replace('_', ' ').title()}")
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")

def main():
    parser = argparse.ArgumentParser(description='KUBEVISTA Development Mode Utility')
    parser.add_argument('action', choices=['enable', 'disable', 'status', 'tier'], 
                       help='Action to perform')
    parser.add_argument('--tier', choices=['free', 'pro', 'enterprise'],
                       help='Specific tier to set (use with "tier" action)')
    
    args = parser.parse_args()
    
    print("🔧 KUBEVISTA Development Mode Utility")
    print("=" * 40)
    
    if args.action == 'enable':
        set_dev_mode(True)
    elif args.action == 'disable':
        set_dev_mode(False)
    elif args.action == 'status':
        show_current_status()
    elif args.action == 'tier':
        if args.tier:
            set_specific_tier(args.tier)
        else:
            print("❌ Please specify --tier (free, pro, enterprise)")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()