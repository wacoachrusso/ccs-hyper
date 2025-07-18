#!/usr/bin/env python3
"""
Build script for Netlify deployment.
This script prepares the project for deployment by:
1. Creating a 'dist' directory.
2. Copying static assets (HTML, CSS, JS, images) to 'dist'.
3. Injecting environment variables into the frontend JavaScript.
"""

import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SRC_DIR, 'dist')
STATIC_DIR = os.path.join(SRC_DIR, 'static')
TEMPLATES_DIR = os.path.join(SRC_DIR, 'templates')

def clean_dist():
    """Remove the existing dist directory if it exists."""
    if os.path.exists(DIST_DIR):
        logger.info(f"Removing existing dist directory: {DIST_DIR}")
        shutil.rmtree(DIST_DIR)

def create_dist():
    """Create a fresh dist directory."""
    logger.info(f"Creating new dist directory: {DIST_DIR}")
    os.makedirs(DIST_DIR)

def copy_static_assets():
    """Copy all files from the static directory to the dist directory."""
    logger.info(f"Copying static assets from {STATIC_DIR} to {DIST_DIR}")
    if os.path.exists(STATIC_DIR):
        shutil.copytree(STATIC_DIR, os.path.join(DIST_DIR, 'static'))
    else:
        logger.warning(f"Static directory not found at: {STATIC_DIR}")

def copy_html_templates():
    """Copy HTML files from the templates directory to the root of dist."""
    logger.info(f"Copying HTML templates from {TEMPLATES_DIR} to {DIST_DIR}")
    if os.path.exists(TEMPLATES_DIR):
        for item in os.listdir(TEMPLATES_DIR):
            if item.endswith('.html'):
                shutil.copy2(os.path.join(TEMPLATES_DIR, item), DIST_DIR)
    else:
        logger.warning(f"Templates directory not found at: {TEMPLATES_DIR}")

def inject_env_variables():
    """Inject Netlify environment variables into the Supabase config JS."""
    config_js_path = os.path.join(DIST_DIR, 'static', 'js', 'supabase-config.js')
    logger.info(f"Injecting environment variables into {config_js_path}")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        logger.error("Supabase environment variables not found!")
        logger.error("Make sure SUPABASE_URL and SUPABASE_ANON_KEY are set in Netlify.")
        # Create a placeholder file to avoid breaking the build
        if not os.path.exists(config_js_path):
            os.makedirs(os.path.dirname(config_js_path), exist_ok=True)
            with open(config_js_path, 'w') as f:
                f.write('// Environment variables not found during build.')
        return

    try:
        with open(config_js_path, 'r') as f:
            content = f.read()

        # Replace placeholder tokens in the config file with actual values
        # from the environment.
        content = content.replace('{{SUPABASE_URL}}', supabase_url)
        content = content.replace('{{SUPABASE_ANON_KEY}}', supabase_anon_key)
        
        with open(config_js_path, 'w') as f:
            f.write(content)
        
        logger.info("Successfully injected environment variables.")
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_js_path}")
    except Exception as e:
        logger.error(f"Failed to inject environment variables: {e}")

def main():
    """Run the full build process."""
    logger.info("Starting Netlify build process...")
    clean_dist()
    create_dist()
    copy_static_assets()
    copy_html_templates()
    inject_env_variables()
    logger.info("Build process completed successfully.")

if __name__ == "__main__":
    main()
