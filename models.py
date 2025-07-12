from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and preferences"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    pairings = db.relationship('Pairing', backref='user', lazy='dynamic')
    crew_lists = db.relationship('UserCrewList', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Pairing(db.Model):
    """Model for trip pairings"""
    __tablename__ = 'pairings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pairing_code = db.Column(db.String(10), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    block_time = db.Column(db.Integer)  # In minutes
    credit_time = db.Column(db.Integer)  # In minutes
    trip_value = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    flights = db.relationship('Flight', backref='pairing', lazy='dynamic', cascade='all, delete-orphan')

class Flight(db.Model):
    """Model for individual flights"""
    __tablename__ = 'flights'
    
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('pairings.id'), nullable=False)
    flight_number = db.Column(db.String(10), nullable=False)
    departure_airport = db.Column(db.String(5), nullable=False)
    arrival_airport = db.Column(db.String(5), nullable=False)
    scheduled_departure = db.Column(db.DateTime, nullable=False)
    scheduled_arrival = db.Column(db.DateTime, nullable=False)
    aircraft_type = db.Column(db.String(10))
    actual_departure = db.Column(db.DateTime)  # Nullable for future flights
    actual_arrival = db.Column(db.DateTime)  # Nullable for future flights
    notes = db.Column(db.Text)
    
    # Relationships
    crew_assignments = db.relationship('FlightCrew', backref='flight', lazy='dynamic', cascade='all, delete-orphan')

class CrewMember(db.Model):
    """Model for crew members"""
    __tablename__ = 'crew_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(20), unique=True)
    base = db.Column(db.String(5))
    seniority = db.Column(db.String(20))
    
    # Relationships
    flight_assignments = db.relationship('FlightCrew', backref='crew_member', lazy='dynamic')
    user_lists = db.relationship('UserCrewList', backref='crew_member', lazy='dynamic')

class FlightCrew(db.Model):
    """Association model between flights and crew members"""
    __tablename__ = 'flight_crew'
    
    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    crew_member_id = db.Column(db.Integer, db.ForeignKey('crew_members.id'), nullable=False)
    position = db.Column(db.String(20), nullable=False)  # 'captain', 'first_officer', 'flight_attendant', etc.
    
    __table_args__ = (
        db.UniqueConstraint('flight_id', 'crew_member_id', name='uix_flight_crew'),
    )

class UserCrewList(db.Model):
    """Model for user's crew lists (Do Not Fly or Friends)"""
    __tablename__ = 'user_crew_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crew_member_id = db.Column(db.Integer, db.ForeignKey('crew_members.id'), nullable=False)
    list_type = db.Column(db.String(20), nullable=False)  # 'do_not_fly', 'friends'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'crew_member_id', 'list_type', name='uix_user_crew_list'),
    )

class Statistic(db.Model):
    """Model for storing aggregated statistics"""
    __tablename__ = 'statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_block = db.Column(db.Integer)  # In minutes
    total_credit = db.Column(db.Integer)  # In minutes
    flights_count = db.Column(db.Integer)
    miles_flown = db.Column(db.Integer)
    aircraft_types = db.Column(db.JSON)  # JSON field for storing aircraft type counts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', 'year', name='uix_user_month_year'),
    )
