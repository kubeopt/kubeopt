# Settings Update Plan

## Current .env Variables to Add to Settings UI:

### Missing Critical Settings:
1. **APP_URL** - Application base URL
2. **AUTO_ANALYSIS_ENABLED** - Toggle for auto-analysis 
3. **AUTO_ANALYSIS_INTERVAL** - Interval for auto-analysis (e.g., 240m)
4. **PRODUCTION_MODE** - Production/Development mode

### Missing AI Settings:
5. **AI_ENABLE_COST_TRACKING** - Track AI costs
6. **AI_MAX_CONTEXT_TOKENS** - Max context size
7. **AI_MAX_OUTPUT_TOKENS** - Max output size
8. **AI_MAX_RETRIES** - Retry attempts
9. **AI_MODEL** - Claude model selection
10. **AI_USE_SPLIT_MODE** - Split large requests
11. **ANTHROPIC_API_KEY** - API key for Claude

### Missing API Settings:
12. **LICENSE_API_URL** - License validation server
13. **LOCAL_DEV** - Local development mode
14. **PLAN_API_URL** - Plan generation server

### Missing Toggle Switches:
15. **EMAIL_ENABLED** - Enable/disable email
16. **SLACK_ENABLED** - Enable/disable Slack

## Settings to Remove (not in .env):
1. Debug Mode (use LOG_LEVEL instead)
2. API Rate Limit (not configurable via .env)
3. Cache Duration (hardcoded in app)
4. Data Encryption toggle (always enabled)
5. Audit Logging toggle (use LOG_LEVEL)

## Settings Sections to Update:
1. General Settings - Add APP_URL, PRODUCTION_MODE
2. Notifications - Add EMAIL_ENABLED, SLACK_ENABLED toggles
3. Advanced - Replace with: Auto-Analysis, AI Config, API Config, Developer Settings