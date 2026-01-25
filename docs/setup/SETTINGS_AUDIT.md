# Settings Audit Report - UI vs .env Mapping

## Settings Currently in .env but NOT in UI:
1. **APP_URL** - Application URL (default: http://localhost:5001)
2. **AUTO_ANALYSIS_ENABLED** - Enable/disable auto-analysis
3. **AUTO_ANALYSIS_INTERVAL** - Auto-analysis interval (e.g., 240m)
4. **PRODUCTION_MODE** - Production/Development mode toggle
5. **AI_ENABLE_COST_TRACKING** - AI cost tracking toggle
6. **AI_MAX_CONTEXT_TOKENS** - AI context token limit
7. **AI_MAX_OUTPUT_TOKENS** - AI output token limit
8. **AI_MAX_RETRIES** - AI retry count
9. **AI_MODEL** - Claude model selection
10. **AI_USE_SPLIT_MODE** - AI split mode toggle
11. **ANTHROPIC_API_KEY** - Anthropic API key
12. **LICENSE_API_URL** - License server URL
13. **LOCAL_DEV** - Local development mode
14. **PLAN_API_URL** - Plan generation API URL

## Settings in UI but NOT properly mapped to .env:
1. **Email Settings** - Missing proper .env mapping:
   - EMAIL_ENABLED (toggle missing in UI)
2. **Slack Settings** - Missing proper .env mapping:
   - SLACK_ENABLED (toggle missing in UI)

## Settings Present in Both (Working):
1. ANALYSIS_REFRESH_INTERVAL ✓
2. COST_ALERT_THRESHOLD ✓
3. LOG_LEVEL ✓
4. KUBEOPT_LICENSE_KEY ✓
5. AZURE_TENANT_ID ✓
6. AZURE_SUBSCRIPTION_ID ✓
7. AZURE_CLIENT_ID ✓
8. AZURE_CLIENT_SECRET ✓
9. SMTP_SERVER ✓
10. SMTP_PORT ✓
11. SMTP_USERNAME ✓
12. SMTP_PASSWORD ✓
13. FROM_EMAIL ✓
14. EMAIL_RECIPIENTS ✓
15. SLACK_WEBHOOK_URL ✓
16. SLACK_CHANNEL ✓
17. SLACK_COST_THRESHOLD ✓

## Required Actions:
1. Add "Advanced Settings" section to UI for AI/API configuration
2. Add "Auto-Analysis" section for scheduler settings
3. Add enable/disable toggles for Email and Slack
4. Ensure ALL .env variables are editable from UI
5. Fix SettingsManager to properly handle all updates