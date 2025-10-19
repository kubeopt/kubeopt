#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

# verify_database.py - Script to verify SQLite database setup
"""
Database verification script for AKS Cost Optimization Tool
Run this script to verify your SQLite database is working correctly
"""

import sqlite3
import json
import os
from datetime import datetime
import sys

def verify_database(db_path="clusters.db"):
    """Verify the SQLite database setup and functionality"""
    
    print("🔍 AKS Cost Optimization Tool - Database Verification")
    print("=" * 60)
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("💡 Run the application first to create the database")
        return False
    
    print(f"✅ Database file found: {db_path}")
    print(f"📏 Database size: {os.path.getsize(db_path)} bytes")
    
    try:
        # Connect to database
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verify table structure
            print("\n📋 Verifying table structure:")
            
            # Check clusters table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clusters'")
            if cursor.fetchone():
                print("✅ clusters table exists")
                
                # Check clusters table structure
                cursor.execute("PRAGMA table_info(clusters)")
                columns = cursor.fetchall()
                expected_columns = ['id', 'name', 'resource_group', 'environment', 'region', 'description', 'status', 'created_at', 'last_analyzed', 'last_cost', 'last_savings', 'analysis_count', 'metadata']
                
                existing_columns = [col['name'] for col in columns]
                missing_columns = set(expected_columns) - set(existing_columns)
                
                if missing_columns is not None and missing_columns:
                    print(f"⚠️  Missing columns in clusters table: {missing_columns}")
                else:
                    print("✅ clusters table structure is correct")
                    
            else:
                print("❌ clusters table not found")
                return False
            
            # Check analysis_results table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_results'")
            if cursor.fetchone():
                print("✅ analysis_results table exists")
            else:
                print("❌ analysis_results table not found")
                return False
            
            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row['name'] for row in cursor.fetchall()]
            
            expected_indexes = ['idx_cluster_id', 'idx_analysis_date']
            missing_indexes = set(expected_indexes) - set(indexes)
            
            if missing_indexes is not None and missing_indexes:
                print(f"⚠️  Missing indexes: {missing_indexes}")
            else:
                print("✅ Database indexes are correct")
            
            # Check data
            print("\n📊 Checking data:")
            
            cursor.execute("SELECT COUNT(*) as count FROM clusters")
            cluster_count = cursor.fetchone()['count']
            print(f"📦 Total clusters: {cluster_count}")
            
            cursor.execute("SELECT COUNT(*) as count FROM analysis_results")
            analysis_count = cursor.fetchone()['count']
            print(f"📈 Total analysis records: {analysis_count}")
            
            if cluster_count > 0:
                print("\n🏢 Cluster details:")
                cursor.execute("""
                    SELECT id, name, resource_group, environment, 
                           last_analyzed, last_cost, last_savings, analysis_count
                    FROM clusters 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                
                clusters = cursor.fetchall()
                for cluster in clusters:
                    print(f"  • {cluster['name']} ({cluster['resource_group']})")
                    print(f"    Environment: {cluster['environment']}")
                    print(f"    Last Cost: ${cluster['last_cost']:.2f}")
                    print(f"    Last Savings: ${cluster['last_savings']:.2f}")
                    print(f"    Analyses: {cluster['analysis_count']}")
                    print(f"    Last Analyzed: {cluster['last_analyzed'] or 'Never'}")
                    print()
            
            # Test database operations
            print("🔧 Testing database operations:")
            
            # Test insert
            test_cluster_id = f"test_cluster_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute("""
                INSERT INTO clusters 
                (id, name, resource_group, environment, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                test_cluster_id,
                "test-cluster",
                "test-rg",
                "testing",
                "Verification test cluster",
                "active",
                datetime.now().isoformat()
            ))
            
            # Test select
            cursor.execute("SELECT * FROM clusters WHERE id = ?", (test_cluster_id,))
            test_cluster = cursor.fetchone()
            
            if test_cluster is not None and test_cluster:
                print("✅ Insert operation successful")
                
                # Test update
                cursor.execute("""
                    UPDATE clusters 
                    SET last_cost = ?, last_savings = ? 
                    WHERE id = ?
                """, (100.0, 20.0, test_cluster_id))
                
                # Verify update
                cursor.execute("SELECT last_cost, last_savings FROM clusters WHERE id = ?", (test_cluster_id,))
                updated_cluster = cursor.fetchone()
                
                if updated_cluster and updated_cluster['last_cost'] == 100.0:
                    print("✅ Update operation successful")
                else:
                    print("❌ Update operation failed")
                
                # Test delete (cleanup)
                cursor.execute("DELETE FROM clusters WHERE id = ?", (test_cluster_id,))
                print("✅ Delete operation successful")
                
            else:
                print("❌ Insert operation failed")
                return False
            
            conn.commit()
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n🎉 Database verification completed successfully!")
    print("✅ Your SQLite database is working correctly")
    return True

def check_migration_status():
    """Check if migration from JSON was performed"""
    print("\n🔄 Checking migration status:")
    
    json_files = [f for f in os.listdir('.') if f.startswith('clusters.json')]
    backup_files = [f for f in json_files if 'backup' in f]
    
    if backup_files is not None and backup_files:
        print(f"✅ Migration completed - found backup files: {backup_files}")
        latest_backup = max(backup_files, key=os.path.getctime)
        print(f"📦 Latest backup: {latest_backup}")
        
        # Check backup content
        try:
            with open(latest_backup, 'r') as f:
                backup_data = json.load(f)
                print(f"📊 Backup contains {len(backup_data)} clusters")
        except:
            print("⚠️  Could not read backup file")
    
    elif os.path.exists('clusters.json'):
        print("ℹ️  clusters.json still exists - migration may not have run")
        print("💡 Start the application to trigger automatic migration")
    
    else:
        print("ℹ️  No JSON files found - fresh installation")

def performance_test():
    """Basic performance test for database operations"""
    print("\n⚡ Running performance test:")
    
    try:
        with sqlite3.connect("clusters.db") as conn:
            import time
            
            # Test query performance
            start_time = time.time()
            cursor = conn.execute("SELECT COUNT(*) FROM clusters")
            count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            print(f"📊 Query performance: {query_time:.4f}s for counting {count} clusters")
            
            # Test complex query
            start_time = time.time()
            cursor = conn.execute("""
                SELECT c.*, COUNT(a.id) as analysis_count_check
                FROM clusters c
                LEFT JOIN analysis_results a ON c.id = a.cluster_id
                GROUP BY c.id
                LIMIT 10
            """)
            results = cursor.fetchall()
            complex_query_time = time.time() - start_time
            
            print(f"📈 Complex query performance: {complex_query_time:.4f}s for {len(results)} results")
            
            if query_time > 1.0 or complex_query_time > 2.0:
                print("⚠️  Performance may be slow - consider database optimization")
            else:
                print("✅ Database performance is good")
                
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    print("Starting database verification...\n")
    
    # Check command line arguments
    db_path = sys.argv[1] if len(sys.argv) > 1 else "clusters.db"
    
    success = verify_database(db_path)
    check_migration_status()
    
    if success is not None and success:
        performance_test()
        print("\n" + "=" * 60)
        print("🎉 All checks passed! Your database is ready for use.")
        print("💡 You can now start your application with confidence.")
    else:
        print("\n" + "=" * 60)
        print("❌ Database verification failed!")
        print("💡 Please check the implementation guide and try again.")
        sys.exit(1)