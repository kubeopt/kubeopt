/**
 * ============================================================================
 * MODULE DEBUGGING SCRIPT
 * ============================================================================
 * Use this to identify which modules are failing to load
 * Run this temporarily instead of index.js
 * ============================================================================
 */

console.log('🔍 Starting module debugging...');

// Test each module individually
const modulesToTest = [
    './config.js',
    './notifications.js', 
    './utils.js',
    './copy-functionality.js',
    './forms.js',
    './cluster-management.js',
    './charts.js',
    './ui-navigation.js',
    './css-injection.js',
    './progress-animations.js',
    './dynamic-insights.js',
    './implementation-plan.js',
    './main.js'
];

async function testModule(modulePath) {
    try {
        console.log(`🧪 Testing ${modulePath}...`);
        const module = await import(modulePath);
        console.log(`✅ ${modulePath} loaded successfully`);
        console.log(`   Exports:`, Object.keys(module));
        return { success: true, module, exports: Object.keys(module) };
    } catch (error) {
        console.error(`❌ ${modulePath} failed:`, error.message);
        return { success: false, error: error.message };
    }
}

async function runDiagnostics() {
    console.log('📊 Running module diagnostics...');
    
    const results = {};
    
    for (const modulePath of modulesToTest) {
        results[modulePath] = await testModule(modulePath);
        // Small delay to see results clearly
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log('\n📋 DIAGNOSTIC RESULTS:');
    console.log('====================');
    
    let successCount = 0;
    let failureCount = 0;
    
    for (const [path, result] of Object.entries(results)) {
        if (result.success) {
            console.log(`✅ ${path} - OK (${result.exports.length} exports)`);
            successCount++;
        } else {
            console.log(`❌ ${path} - FAILED: ${result.error}`);
            failureCount++;
        }
    }
    
    console.log(`\n📊 Summary: ${successCount} passed, ${failureCount} failed`);
    
    if (failureCount === 0) {
        console.log('🎉 All modules loaded successfully! The issue might be with import order.');
    } else {
        console.log('🔧 Fix the failing modules first, then test again.');
    }
    
    // Test specific critical exports
    console.log('\n🎯 Testing critical exports...');
    
    const criticalTests = [
        { module: './config.js', exports: ['AppConfig', 'AppState'] },
        { module: './notifications.js', exports: ['showNotification'] },
        { module: './main.js', exports: ['initializeDashboard'] }
    ];
    
    for (const test of criticalTests) {
        if (results[test.module].success) {
            const module = results[test.module].module;
            for (const exportName of test.exports) {
                if (module[exportName]) {
                    console.log(`✅ ${test.module} exports ${exportName}`);
                } else {
                    console.log(`❌ ${test.module} missing export: ${exportName}`);
                }
            }
        }
    }
}

// Run diagnostics
runDiagnostics().catch(error => {
    console.error('💥 Diagnostic script failed:', error);
});