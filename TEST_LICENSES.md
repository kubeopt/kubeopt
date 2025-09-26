# Test Licenses for AKS Cost Optimizer

## 🎯 Three Test Licenses for All Tiers

### 🆓 FREE TIER LICENSE (3-month format):
```
F3M-KFV8FZA2-260326
```
- **Tier**: Free
- **Duration**: 3 months (expires March 26, 2026)
- **Features**: Dashboard, Manual Analysis only
- **Use Case**: Test basic functionality and upgrade prompts

### 💼 PRO TIER LICENSE (6-month format):
```
P6M-CGMFFHPLWGNK-260925-DIMAES
```
- **Tier**: Pro  
- **Duration**: 6 months (expires September 25, 2026)
- **Features**: Dashboard, Implementation Plan, Manual Analysis, Auto-Analysis, Email Alerts, Slack Alerts
- **Use Case**: Test Pro features and Enterprise upgrade prompts

### 🏢 ENTERPRISE TIER LICENSE (12-month format):
```
E12M-DCRHRF1AQOQCZKKX-270326-F-2F4F
```
- **Tier**: Enterprise
- **Duration**: 12 months (expires March 26, 2027)
- **Features**: All features (Full access)
- **Use Case**: Test all features with no restrictions

## 🧪 Testing Instructions

### 1. Test FREE License:
1. Go to Settings in your AKS Cost Optimizer
2. Enter: `F3M-KFV8FZA2-260326`
3. **Should see**: 
   - ✅ Dashboard access
   - ✅ Manual analysis
   - 🔒 Implementation Plan (locked with upgrade prompt)
   - 🔒 Auto-Analysis (locked with upgrade prompt)
   - 🔒 Email/Slack integration (locked with upgrade prompt)

### 2. Test PRO License:
1. Enter: `P6M-CGMFFHPLWGNK-260925-DIMAES`
2. **Should see**:
   - ✅ Dashboard access
   - ✅ Implementation Plans unlocked
   - ✅ Auto-Analysis scheduling unlocked
   - ✅ Email/Slack alerts unlocked
   - 🔒 Enterprise Metrics (locked with upgrade prompt)
   - 🔒 Security Posture (locked with upgrade prompt)

### 3. Test ENTERPRISE License:
1. Enter: `E12M-DCRHRF1AQOQCZKKX-270326-F-2F4F`
2. **Should see**:
   - ✅ All features unlocked
   - ✅ Enterprise Metrics
   - ✅ Security Posture Analysis
   - ✅ Advanced Alerts
   - ✅ Multi-Subscription Support
   - 🎉 No locked features or upgrade prompts

## 🔍 Validation Testing

Your enhanced license manager should automatically:
1. **Detect the algorithm** (3M, 6M, or 12M format)
2. **Validate the checksum** using HMAC
3. **Check expiry dates** (all these are valid until 2026/2027)
4. **Enable correct features** based on tier
5. **Show proper UI** (lock icons, upgrade prompts, etc.)

## 🎯 Expected Behavior

### Feature Lock JavaScript should:
- Hide locked features from FREE/PRO users
- Show upgrade prompts when clicking locked features  
- Display correct tier badge in navigation
- Enable/disable buttons based on license tier

### Settings Page should:
- Show all sections to all users
- Lock Slack/Email integration for FREE tier
- Show upgrade buttons pointing to kubevista.io
- Display current license info correctly

## 🚀 Perfect for Testing Your Business Model

These licenses test the complete user journey:
1. **FREE → PRO**: Users see value, want more features
2. **PRO → ENTERPRISE**: Teams need advanced capabilities  
3. **Trial to Paid**: Seamless upgrade experience

All licenses use the advanced algorithms with proper security validation!