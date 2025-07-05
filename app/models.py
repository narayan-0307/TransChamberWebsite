from app import db
from datetime import datetime


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Step 1 fields
    application_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    birth_place = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100))
    nationality = db.Column(db.String(100), nullable=False)
    passport_number = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    zipcode = db.Column(db.String(100), nullable=False)

    # Step 2 fields
    membership_type = db.Column(db.String(100), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    residence_phone = db.Column(db.String(20), nullable=False)
    spouse_name = db.Column(db.String(100))
    number_of_children = db.Column(db.Integer)
    spouse_birth_date = db.Column(db.Date)