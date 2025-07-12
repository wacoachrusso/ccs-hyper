#!/usr/bin/env python3
"""
Database Migration Script: SQLite to Supabase

This script reads data from a local SQLite database and inserts it into the
corresponding tables in a Supabase (PostgreSQL) database.

WARNING: This is a one-way migration. Run with caution.
"""

import os
import sys
import logging
import sqlite3
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
SQLITE_DB_PATH = 'instance/ccs_hyper.db'

def get_supabase_conn():
    """Get a connection to the Supabase database."""
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        logger.error("SUPABASE_DB_URL not found in environment variables.")
        sys.exit(1)
    return psycopg2.connect(db_url)

def get_sqlite_conn():
    """Get a connection to the local SQLite database."""
    if not os.path.exists(SQLITE_DB_PATH):
        logger.error(f"SQLite database not found at: {SQLITE_DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(SQLITE_DB_PATH)

def migrate_table(sqlite_cur, supabase_cur, table_name, column_map):
    """Migrates a single table from SQLite to Supabase."""
    logger.info(f"Starting migration for table: {table_name}")
    
    try:
        sqlite_cur.execute(f"SELECT {', '.join(column_map.keys())} FROM {table_name}")
        rows = sqlite_cur.fetchall()
        logger.info(f"Found {len(rows)} rows in SQLite table '{table_name}'.")

        if not rows:
            logger.info(f"No data to migrate for table '{table_name}'.")
            return

        # Prepare the INSERT statement for PostgreSQL
        pg_columns = ', '.join(column_map.values())
        placeholders = ', '.join(['%s'] * len(column_map.values()))
        insert_query = f"INSERT INTO public.{table_name} ({pg_columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        supabase_cur.executemany(insert_query, rows)
        logger.info(f"Successfully migrated {supabase_cur.rowcount} rows to Supabase table '{table_name}'.")
    
    except sqlite3.Error as e:
        logger.error(f"SQLite error during migration of '{table_name}': {e}")
        raise
    except psycopg2.Error as e:
        logger.error(f"Supabase/PostgreSQL error during migration of '{table_name}': {e}")
        raise

def main():
    """Main migration function."""
    sqlite_conn = None
    supabase_conn = None
    
    try:
        sqlite_conn = get_sqlite_conn()
        supabase_conn = get_supabase_conn()
        
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()
        supabase_cur = supabase_conn.cursor()

        logger.info("Starting data migration from SQLite to Supabase...")

        # --- Define Table Mappings ---
        # This is where you map SQLite columns to Supabase columns.
        # The keys are SQLite column names, values are Supabase column names.
        # Note: This example assumes a direct mapping. You may need to transform data.
        # This script does NOT handle user authentication data (auth.users).
        
        # Example for a 'pairings' table (adjust to your actual schema)
        # pairings_map = {
        #     'id': 'id', # Assuming you want to keep the same UUIDs if they exist
        #     'user_id': 'user_id',
        #     'pairing_code': 'pairing_code',
        #     'start_date': 'start_date',
        #     'end_date': 'end_date',
        # }
        # migrate_table(sqlite_cur, supabase_cur, 'pairings', pairings_map)

        # Add other tables here...

        supabase_conn.commit()
        logger.info("Data migration completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the migration process: {e}")
        if supabase_conn:
            supabase_conn.rollback()
            logger.info("Supabase transaction rolled back.")
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if supabase_conn:
            supabase_conn.close()

if __name__ == "__main__":
    main()
