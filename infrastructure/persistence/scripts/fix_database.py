#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_fix_existing_database():
    """Fix your existing database immediately"""
    db_path = 'clusters.db'  # Change to your actual database path if different
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check what columns exist
            cursor.execute("PRAGMA table_info(clusters)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            logger.info(f"📊 Current columns: {existing_columns}")
            
            # Add missing columns
            missing_columns = [
                ('analysis_data', 'TEXT'),
                ('last_confidence', 'REAL DEFAULT 0'),
            ]
            
            columns_added = 0
            for col_name, col_def in missing_columns:
                if col_name not in existing_columns:
                    try:
                        alter_sql = f'ALTER TABLE clusters ADD COLUMN {col_name} {col_def}'
                        cursor.execute(alter_sql)
                        logger.info(f"✅ Added {col_name} column")
                        columns_added += 1
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            logger.info(f"✅ {col_name} column already exists")
                        else:
                            logger.error(f"❌ Failed to add {col_name}: {e}")
                else:
                    logger.info(f"✅ {col_name} column already exists")
            
            conn.commit()
            logger.info(f"✅ Database fix completed - {columns_added} columns added")
            
            # Verify
            cursor.execute("PRAGMA table_info(clusters)")
            final_columns = [row[1] for row in cursor.fetchall()]
            
            if 'analysis_data' in final_columns:
                logger.info("✅ analysis_data column confirmed present")
                return True
            else:
                logger.error("❌ analysis_data column still missing")
                return False
                
    except Exception as e:
        logger.error(f"❌ Quick fix failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_fix_existing_database()
    if success:
        print("✅ Database fixed successfully!")
    else:
        print("❌ Database fix failed!")