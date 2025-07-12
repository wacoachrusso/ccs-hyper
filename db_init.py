import os
import logging
from flask import Flask
from models import db, User, Pairing, Flight, CrewMember, FlightCrew, UserCrewList, Statistic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask application for database initialization"""
    app = Flask(__name__)
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ccs_hyper.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database with app
    db.init_app(app)
    
    return app

def init_db():
    """Initialize database with tables"""
    app = create_app()
    
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully.")

if __name__ == '__main__':
    init_db()
