# 🔑 kubeopt License Management Guide

## 📋 **License Key Expiry System**

### 🕐 **Standard Expiry Periods:**

#### **🆓 Trial Licenses:**
- **7 days** - Quick evaluation
- **30 days** - Standard trial period  
- **90 days** - Extended evaluation for enterprise

#### **💼 Commercial Licenses:**
- **1 month** - Monthly subscription
- **3 months** - Quarterly subscription (5% discount)
- **6 months** - Semi-annual (10% discount)  
- **12 months** - Annual subscription (15% discount)

#### **🏢 Enterprise Licenses:**
- **1 year** - Standard enterprise contract
- **2 years** - Extended enterprise (10% discount)
- **3 years** - Long-term enterprise (20% discount)
- **Lifetime** - One-time purchase (no expiry)

## 🛠️ **License Generation Tools**

### **1. Trial License Generation**
```bash
# 30-day Pro trial
python3 generate_license.py --tier pro --days 30 --type trial

# 7-day Enterprise trial  
python3 generate_license.py --tier enterprise --days 7 --type trial
```

### **2. Commercial License Generation**
```bash
# 3-month Pro subscription
python3 generate_license.py --tier pro --months 3 --type commercial

# 6-month Pro subscription
python3 generate_license.py --tier pro --months 6 --type commercial

# 1-year Pro subscription
python3 generate_license.py --tier pro --years 1 --type commercial
```

### **3. Enterprise License Generation**
```bash
# 1-year Enterprise license
python3 generate_license.py --tier enterprise --years 1 --type enterprise

# 3-year Enterprise license  
python3 generate_license.py --tier enterprise --years 3 --type enterprise

# Lifetime Enterprise license
python3 generate_license.py --tier enterprise --type lifetime
```

### **4. Batch Generation**
```bash
# Generate 50 trial keys for marketing campaign
python3 generate_license.py --tier pro --days 30 --type trial --batch 50

# Generate 10 demo keys for sales team
python3 generate_license.py --tier enterprise --days 14 --type trial --batch 10
```

## 📊 **License Administration**

### **1. Customer License Creation**
```bash
# Create customer license with record
python3 license_admin.py record \
  --customer "john@acme.com" \
  --company "Acme Corp" \
  --tier pro \
  --months 12 \
  --type commercial
```

### **2. License Status Checking**
```bash
# Check specific license
python3 license_admin.py check PRO-a1b2c3d4-20241225

# List all active licenses
python3 license_admin.py list --status active

# List all Pro tier licenses
python3 license_admin.py list --tier pro

# Export license data as JSON
python3 license_admin.py list --format json > licenses.json
```

### **3. License Revocation**
```bash
# Revoke a license
python3 license_admin.py revoke PRO-a1b2c3d4-20241225 --reason "Payment failed"

# Emergency revocation
python3 license_admin.py revoke ENT-x1y2z3w4-20251225 --reason "Security breach"
```

### **4. License Statistics**
```bash
# View license statistics
python3 license_admin.py stats
```

## 🔐 **License Key Format**

### **Structure: `TIER-HASH-EXPIRY`**
```
PRO-a1b2c3d4-20241225
│   │        │
│   │        └── Expiry date (YYYYMMDD) or "NEVER"
│   └── Unique hash (8 characters)
└── Tier code (FREE/PRO/ENT)
```

### **Examples:**
```bash
PRO-a1b2c3d4-20241225    # Pro license expires Dec 25, 2024
ENT-x1y2z3w4-NEVER       # Enterprise lifetime license
PRO-trial123-20241101    # Pro trial expires Nov 1, 2024
```

## 📋 **Customer License Workflow**

### **1. Sales Process:**
```bash
# Step 1: Generate trial for prospect
python3 generate_license.py --tier pro --days 30 --type trial

# Step 2: Customer converts to paid
python3 license_admin.py record \
  --customer "customer@company.com" \
  --company "Customer Company" \
  --tier pro \
  --months 12 \
  --type commercial

# Step 3: Send license key to customer
# Step 4: Customer activates via Settings → Activate License
```

### **2. Support Process:**
```bash
# Check customer license status
python3 license_admin.py check PRO-customer-key

# Extend customer license (generate new key)
python3 license_admin.py record \
  --customer "existing@customer.com" \
  --tier pro \
  --months 12 \
  --type commercial

# Handle payment issues
python3 license_admin.py revoke OLD-KEY --reason "Replaced with new key"
```

## 🔄 **License Renewal Process**

### **Automatic Expiry Handling:**
1. **30 days before expiry** → Email reminder
2. **7 days before expiry** → Email + in-app notification  
3. **1 day before expiry** → Email + prominent in-app warning
4. **On expiry** → Features locked, downgrade to FREE tier
5. **Grace period (7 days)** → Allow reactivation
6. **After grace** → Require new license purchase

### **Renewal Commands:**
```bash
# Generate renewal license
python3 license_admin.py record \
  --customer "renewing@customer.com" \
  --tier pro \
  --years 1 \
  --type commercial

# Track renewal in database
# Old license expires automatically
```

## 🔒 **Security Features**

### **License Validation:**
- ✅ **Cryptographic hash** prevents tampering
- ✅ **Expiry date validation** prevents expired usage
- ✅ **Revocation checking** prevents misuse
- ✅ **Tier validation** prevents privilege escalation

### **Revocation System:**
```bash
# Immediate revocation (takes effect immediately)
python3 license_admin.py revoke LICENSE-KEY --reason "Security issue"

# Bulk revocation for security incident  
for key in $(cat compromised_keys.txt); do
  python3 license_admin.py revoke $key --reason "Security incident"
done
```

## 📈 **Pricing Strategy Examples**

### **SaaS Pricing Tiers:**
```bash
# Startup package (3 months)
python3 generate_license.py --tier pro --months 3 --type commercial
# Price: $49/month × 3 = $147 ($134 with 10% discount)

# Business package (12 months)  
python3 generate_license.py --tier pro --years 1 --type commercial
# Price: $49/month × 12 = $588 ($499 with 15% discount)

# Enterprise package (3 years)
python3 generate_license.py --tier enterprise --years 3 --type enterprise  
# Price: $199/month × 36 = $7,164 ($5,731 with 20% discount)
```

### **Campaign Licenses:**
```bash
# Black Friday campaign (50% off for 6 months)
python3 generate_license.py --tier pro --months 6 --type commercial --batch 100

# Partner demo licenses  
python3 generate_license.py --tier enterprise --days 60 --type trial --batch 20
```

## 📁 **Database Files**

### **Generated Files:**
- `license_database.json` - Customer license records
- `revoked_licenses.json` - Revoked license tracking
- `kubeopt_licenses_*.txt` - Batch generated keys

### **Backup Strategy:**
```bash
# Daily backup
cp license_database.json "backups/license_db_$(date +%Y%m%d).json"
cp revoked_licenses.json "backups/revoked_$(date +%Y%m%d).json"

# Weekly archive
tar -czf "weekly_license_backup_$(date +%Y%m%d).tar.gz" license_database.json revoked_licenses.json
```

## 🎯 **Best Practices**

### **License Distribution:**
1. **Never email license keys in plain text**
2. **Use secure customer portals**
3. **Log all license generation/revocation**
4. **Regular audit of active licenses**
5. **Monitor for license sharing/abuse**

### **Customer Support:**
1. **Always verify customer identity** before license operations
2. **Document reason for revocations**
3. **Provide clear expiry notifications**
4. **Offer easy renewal process**
5. **Track license usage patterns**

Perfect system for managing license lifecycles from trial to enterprise! 🚀