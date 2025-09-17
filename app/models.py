
from app import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import uuid
import os


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'host' or 'member'
    is_verified = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def generate_reset_token(self):
        import secrets
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    def check_reset_token(self, token):
        return self.reset_token == token and self.reset_token_expiry and self.reset_token_expiry > datetime.utcnow()



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

# Model to log brochure download requests
class BrochureDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class ExportInquiry(db.Model):
    __tablename__ = 'export_inquiries'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    product_quantity = db.Column(db.String(50), nullable=False)
    product_details = db.Column(db.Text, nullable=False)
    sender_details = db.Column(db.Text, nullable=False)
    export_requirements = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consent fields
    terms_consent = db.Column(db.Boolean, default=False, nullable=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))  # Store IP for security tracking
    user_agent = db.Column(db.Text)  # Store user agent for security tracking

    def __repr__(self):
        return f"<ExportInquiry {self.id} - {self.full_name}>"
    

class ImportInquiry(db.Model):
    __tablename__ = 'import_inquiries'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    product_quantity = db.Column(db.String(50), nullable=False)
    product_details = db.Column(db.Text, nullable=False)
    sender_details = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consent fields
    terms_consent = db.Column(db.Boolean, default=False, nullable=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))  # Store IP for security tracking
    user_agent = db.Column(db.Text)  # Store user agent for security tracking

    def __repr__(self):
        return f"<ImportInquiry {self.id} - {self.full_name}>"
    

class BusinessOpportunity(db.Model):
    __tablename__ = 'business_opportunity'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    business_opportunity = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consent fields
    terms_consent = db.Column(db.Boolean, default=False, nullable=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))  # Store IP for security tracking
    user_agent = db.Column(db.Text)  # Store user agent for security tracking

    def __repr__(self):
        return f"<BusinessOpportunity {self.id} - {self.full_name}>"
    
class Suggestions(db.Model):
    __tablename__ = 'suggestions'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    suggestions = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consent fields
    terms_consent = db.Column(db.Boolean, default=False, nullable=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))  # Store IP for security tracking
    user_agent = db.Column(db.Text)  # Store user agent for security tracking

    def __repr__(self):
        return f"<BusinessSuggestionsOpportunity {self.id} - {self.full_name}>"
    
class Complaints(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    complaints = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consent fields
    terms_consent = db.Column(db.Boolean, default=False, nullable=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))  # Store IP for security tracking
    user_agent = db.Column(db.Text)  # Store user agent for security tracking

    def __repr__(self):
        return f"<Complaints {self.id} - {self.full_name}>"
        

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Event {self.title}>"
    
def generate_uuid():
    return str(uuid.uuid4())

class BrochureInquiry(db.Model):
    __tablename__ = 'brochure_inquiries'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    company = db.Column(db.String(120))
    job_title = db.Column(db.String(120))
    country = db.Column(db.String(100), nullable=False)
    interest = db.Column(db.String(100), nullable=False)
    consent = db.Column(db.Boolean, nullable=False, default=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BrochureInquiry {self.email}>"
    

class ContactForm(db.Model):
    __tablename__ = 'contact_page'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    website = db.Column(db.String(255))
    purpose = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(150), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactForm {self.id} - {self.name}>"


class VIP(db.Model):
    __tablename__ = 'vips'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    designation = db.Column(db.String(255), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<VIP {self.id} - {self.name}>"
    
    def delete_image_file(self):
        """Delete the image file from the filesystem"""
        if self.image_path:
            try:
                full_path = os.path.join(os.getcwd(), 'app', self.image_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"Error deleting image file: {e}") 

class BankToBankTransfer(db.Model):
    __tablename__ = "bank_to_bank_transfers"

    id = db.Column(db.Integer, primary_key=True)
    # Legacy name field kept for backward compatibility
    name = db.Column(db.String(150), nullable=False)
    # New structured fields captured from the modal form
    application_name = db.Column(db.String(150))
    phone_number = db.Column(db.String(30))
    email = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text)
    country = db.Column(db.String(100))
    nationality = db.Column(db.String(100))
    membership_type = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BankToBankTransfer {self.id} - {self.name} - {self.amount}>"


class PastEvent(db.Model):
    __tablename__ = 'past_events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.Date, nullable=True)
    banner_image_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship('PastEventImage', backref='past_event', cascade='all, delete-orphan', lazy=True, order_by='PastEventImage.display_order')

    def __repr__(self):
        return f"<PastEvent {self.id} - {self.title}>"


class PastEventImage(db.Model):
    __tablename__ = 'past_event_images'

    id = db.Column(db.Integer, primary_key=True)
    past_event_id = db.Column(db.Integer, db.ForeignKey('past_events.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PastEventImage {self.id} - Event {self.past_event_id}>"


# Budget Events (separate from PastEvent, mirrors the same structure)
class BudgetEvent(db.Model):
    __tablename__ = 'budget_events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.Date, nullable=True)
    banner_image_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship('BudgetEventImage', backref='budget_event', cascade='all, delete-orphan', lazy=True, order_by='BudgetEventImage.display_order')

    def __repr__(self):
        return f"<BudgetEvent {self.id} - {self.title}>"


class BudgetEventImage(db.Model):
    __tablename__ = 'budget_event_images'

    id = db.Column(db.Integer, primary_key=True)
    budget_event_id = db.Column(db.Integer, db.ForeignKey('budget_events.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BudgetEventImage {self.id} - Event {self.budget_event_id}>"
