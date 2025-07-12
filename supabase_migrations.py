#!/usr/bin/env python3
"""
Supabase Migration Runner
This script automates the process of applying SQL migrations to a Supabase database.
It reads a .sql file and executes it against the Supabase project's database.
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("migration_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection_string():
    """Construct the database connection string from environment variables."""
    load_dotenv()
    
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        # Fallback for older .env files or different naming conventions
        project_id = os.getenv("SUPABASE_PROJECT_ID")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        region = os.getenv("SUPABASE_REGION", "us-east-1")
        
        if not project_id or not db_password:
            logger.error("Supabase connection details not found in environment variables.")
            logger.error("Please set SUPABASE_DB_URL or SUPABASE_PROJECT_ID and SUPABASE_DB_PASSWORD.")
            sys.exit(1)
        
        db_url = f"postgresql://postgres:{db_password}@{project_id}.{region}.supabase.io:5432/postgres"
        
    return db_url

def run_migrations(connection_string, sql_file_path):
    """Connect to the database and execute the SQL from the file."""
    conn = None
    try:
        logger.info("Connecting to the Supabase database...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        logger.info("Connection successful.")

        logger.info(f"Reading SQL migration file: {sql_file_path}")
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()

        # Split script into individual statements to execute one by one
        # This provides better error handling than executing the whole file at once
        sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]

        logger.info(f"Found {len(sql_commands)} SQL commands to execute.")

        for command in sql_commands:
            try:
                logger.info(f"Executing: {command[:80]}...") # Log first 80 chars
                cursor.execute(command)
            except psycopg2.Error as e:
                logger.error(f"Error executing command: {command}")
                logger.error(f"PostgreSQL Error: {e}")
                conn.rollback() # Rollback on error
                # Decide if you want to stop on first error or continue
                # For migrations, it's often best to stop.
                return False

        conn.commit()
        cursor.close()
        logger.info("All migrations applied successfully.")
        return True

    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to the database: {e}")
        return False
    except FileNotFoundError:
        logger.error(f"SQL migration file not found at: {sql_file_path}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    logger.info("Starting Supabase migration runner script.")
    
    # Define the path to the migration file
    MIGRATION_FILE = "supabase_migrations.sql"
    
    # Get the connection string
    db_conn_str = get_db_connection_string()
    
    # Run the migrations
    success = run_migrations(db_conn_str, MIGRATION_FILE)
    
    if success:
        logger.info("Migration script finished successfully.")
        sys.exit(0)
    else:
        logger.error("Migration script failed. Please check the logs.")
        sys.exit(1)
