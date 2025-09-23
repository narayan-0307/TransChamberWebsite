from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify, session, send_file, make_response
from app.utils import get_cookie, set_cookie_consent
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional
from app.models import User, Member, ExportInquiry, ImportInquiry, BusinessOpportunity, Suggestions, Complaints, Event, BrochureInquiry, ContactForm, VIP, BankToBankTransfer, PastEvent, PastEventImage, BudgetEvent, BudgetEventImage
from app import db, login_manager, mail
from app.api.events_details import get_events
from app.api.leadershipBoard_api import data
from app.api.team_api import team_members
from datetime import datetime, timedelta, date
import os
from werkzeug.utils import secure_filename
import json
from flask_mail import Message
import uuid
from functools import wraps
import shutil

bp = Blueprint('main', __name__)

# Allowed file extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    if not filename:
        return False
    result = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    print(f"allowed_file check for {filename}: {result}")
    return result

def save_uploaded_file(file, folder):
    """Save uploaded file to the specified folder"""
    print(f"save_uploaded_file called with file: {file.filename if file else 'None'}, folder: {folder}")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        # Create folder if it doesn't exist
        upload_folder = os.path.join('app', 'static', 'images', 'past_events', folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Return the relative path for database storage
        result_path = f"/static/images/past_events/{folder}/{filename}"
        print(f"File saved successfully: {result_path}")
        return result_path
    else:
        print(f"File validation failed: {file.filename if file else 'None'}")
    return None


def save_uploaded_budget_file(file, folder):
    """Save uploaded file for budget events to the specified folder"""
    print(f"save_uploaded_budget_file called with file: {file.filename if file else 'None'}, folder: {folder}")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"

        upload_folder = os.path.join('app', 'static', 'images', 'budget_events', folder)
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        result_path = f"/static/images/budget_events/{folder}/{filename}"
        print(f"Budget file saved successfully: {result_path}")
        return result_path
    else:
        print(f"Budget file validation failed: {file.filename if file else 'None'}")
    return None

class ContactFormWT(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    website = StringField('Website', validators=[Optional()])
    purpose = SelectField('Purpose', validators=[DataRequired()], choices=[
        ('', 'Purpose of Contact*'),
        ('general_inquiry', 'General Inquiry'),
        ('membership', 'Membership'),
        ('business_opportunity', 'Business Opportunity'),
        ('partnership', 'Partnership'),
        ('event_information', 'Event'),
        ('support', 'Technical Support'),
        ('feedback', 'Feedback'),
        ('other', 'Other')
    ])
    message = TextAreaField('Message', validators=[Optional()])

def validate_session(f):
    """Decorator to validate session for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to access this page.')
            return redirect(url_for('main.login'))
        
        # Check if session data exists
        if not session.get('session_id') or not session.get('user_id'):
            logout_user()
            flash('Session expired. Please log in again.')
            return redirect(url_for('main.login'))
        
        # Check if session user matches current user
        if current_user.id != session.get('user_id'):
            logout_user()
            flash('Session mismatch. Please log in again.')
            return redirect(url_for('main.login'))
        
        # Check if session role matches current user role
        if session.get('user_role') != current_user.role:
            logout_user()
            flash('Role mismatch. Please log in again.')
            return redirect(url_for('main.login'))
        
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            role = request.form.get('role', '')
            
            # Validate required fields
            if not username:
                flash('Username is required', 'error')
                return redirect(url_for('main.register'))
            
            if not email:
                flash('Email is required', 'error')
                return redirect(url_for('main.register'))
            
            if not password:
                flash('Password is required', 'error')
                return redirect(url_for('main.register'))
            
            if not confirm_password:
                flash('Please confirm your password', 'error')
                return redirect(url_for('main.register'))
            
            if not role:
                flash('Please select a role', 'error')
                return redirect(url_for('main.register'))
            
            # Validate password confirmation
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('main.register'))
            
            # Validate password length
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return redirect(url_for('main.register'))
            
            # Check if username or email already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    flash('Username already exists. Please choose a different username.', 'error')
                else:
                    flash('Email already exists. Please use a different email address.', 'error')
                return redirect(url_for('main.register'))
            
            # Create new user
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('main.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")  # For debugging
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('main.register'))
    
    return render_template('admin/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            selected_role = request.form.get('role', '')
            
            # Validate required fields
            if not username:
                flash('Username is required', 'error')
                return redirect(url_for('main.login'))
            
            if not password:
                flash('Password is required', 'error')
                return redirect(url_for('main.login'))
            
            if not selected_role:
                flash('Please select a role', 'error')
                return redirect(url_for('main.login'))
            
            # Find user by username
            user = User.query.filter_by(username=username).first()
            
            if not user:
                flash('Invalid username or password', 'error')
                return redirect(url_for('main.login'))
            
            # Check password
            if not user.check_password(password):
                flash('Invalid username or password', 'error')
                return redirect(url_for('main.login'))
            
            # Check if user's role matches selected role
            if user.role != selected_role:
                flash(f'Invalid role selected. Your account is registered as a {user.role}.', 'error')
                return redirect(url_for('main.login'))
            
            # Generate session data
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['login_time'] = datetime.utcnow().isoformat()
            
            # Log in user
            login_user(user)
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            print(f"Login error: {str(e)}")  # For debugging
            flash(f'Login failed: {str(e)}', 'error')
            return redirect(url_for('main.login'))
    
    return render_template('admin/login.html')

@bp.route('/dashboard')
@login_required
@validate_session
def dashboard():
    if current_user.role == 'host':
        # Fetch all data for the host dashboard
        complaints = Complaints.query.order_by(Complaints.submitted_at.desc()).all()
        export_inquiries = ExportInquiry.query.order_by(ExportInquiry.submitted_at.desc()).all()
        import_inquiries = ImportInquiry.query.order_by(ImportInquiry.submitted_at.desc()).all()
        business_opportunities = BusinessOpportunity.query.order_by(BusinessOpportunity.submitted_at.desc()).all()
        suggestions = Suggestions.query.order_by(Suggestions.submitted_at.desc()).all()
        brochure_inquiries = BrochureInquiry.query.order_by(BrochureInquiry.submitted_at.desc()).all()
        return render_template('admin/dashboard_host.html', 
                             complaints=complaints,
                             export_inquiries=export_inquiries,
                             import_inquiries=import_inquiries,
                             business_opportunities=business_opportunities,
                             suggestions=suggestions,
                             brochure_inquiries=brochure_inquiries)
    elif current_user.role == 'member':
        # Fetch all data for the member dashboard
        complaints = Complaints.query.order_by(Complaints.submitted_at.desc()).all()
        export_inquiries = ExportInquiry.query.order_by(ExportInquiry.submitted_at.desc()).all()
        import_inquiries = ImportInquiry.query.order_by(ImportInquiry.submitted_at.desc()).all()
        business_opportunities = BusinessOpportunity.query.order_by(BusinessOpportunity.submitted_at.desc()).all()
        suggestions = Suggestions.query.order_by(Suggestions.submitted_at.desc()).all()
        brochure_inquiries = BrochureInquiry.query.order_by(BrochureInquiry.submitted_at.desc()).all()
        return render_template('admin/dashboard_member.html', 
                             complaints=complaints,
                             export_inquiries=export_inquiries,
                             import_inquiries=import_inquiries,
                             business_opportunities=business_opportunities,
                             suggestions=suggestions,
                             brochure_inquiries=brochure_inquiries)
    else:
        return "Unknown role", 403


@bp.route('/logout', methods=['GET', 'POST'])
@login_required
@validate_session
def logout():
    # Clear session data
    session.clear()
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('main.login'))

@bp.route('/logout-all', methods=['GET', 'POST'])
@login_required
def logout_all():
    """Logout from all sessions"""
    session.clear()
    logout_user()
    flash('You have been logged out from all sessions.')
    return redirect(url_for('main.login'))

@bp.route('/session-info')
@login_required
@validate_session
def session_info():
    """Display current session information"""
    session_data = {
        'session_id': session.get('session_id'),
        'user_id': session.get('user_id'),
        'user_role': session.get('user_role'),
        'login_time': session.get('login_time'),
        'current_user_id': current_user.id,
        'current_user_role': current_user.role,
        'current_user_username': current_user.username
    }
    return jsonify(session_data)

def send_reset_email(user):
    try:
        # Check if mail configuration is set up
        from flask import current_app
        if not current_app.config.get('MAIL_SERVER') or not current_app.config.get('MAIL_USERNAME'):
            return False
        
        token = user.generate_reset_token()
        db.session.commit()
        
        reset_url = url_for('main.reset_password', token=token, _external=True)
        
        msg = Message(
            subject='Password Reset Request - TransChamber',
            recipients=[user.email],
            body=f'''To reset your password, visit the following link:

{reset_url}

If you did not make this request, simply ignore this email.

This link will expire in 1 hour.

Best regards,
TransChamber Team'''
        )
        
        mail.send(msg)
        print(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending reset email: {str(e)}")
        db.session.rollback()
        return False

def send_form_confirmation_email(form_type, user_data, inquiry_id=None):
    """
    Send confirmation email for form submissions
    form_type: 'export', 'import', 'business_opportunity', 'suggestions', 'complaints'
    user_data: dictionary containing user information
    inquiry_id: ID of the submitted inquiry (optional)
    """
    try:
        from flask import current_app
        if not current_app.config.get('MAIL_SERVER') or not current_app.config.get('MAIL_USERNAME'):
            return False
        
        # Load email templates from JSON file
        import json
        import os
        
        # Get the path to the email templates JSON file
        template_path = os.path.join(current_app.root_path, 'static', 'data', 'email_templates.json')
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
        except FileNotFoundError:
            return False
        except json.JSONDecodeError as e:
            return False
        
        # Get subject and template for the form type
        subjects = email_data.get('subjects', {})
        templates = email_data.get('templates', {})
        
        if form_type not in subjects or form_type not in templates:
            return False
        
        subject = subjects[form_type]
        template = templates[form_type]
        
        # Build email body from template
        body_parts = []
        
        # Add greeting
        greeting = template.get('greeting', 'Dear {name},')
        body_parts.append(greeting.format(name=user_data.get('name', 'Valued Customer')))
        body_parts.append('')  # Empty line
        
        # Add intro
        intro = template.get('intro', '')
        body_parts.append(intro)
        body_parts.append('')  # Empty line
        
        # Add details section
        details_section = template.get('details_section', '')
        if details_section:
            body_parts.append(details_section)
            details = template.get('details', [])
            for detail in details:
                formatted_detail = detail.format(
                    inquiry_id=inquiry_id if inquiry_id else 'N/A',
                    companyName=user_data.get('companyName', 'N/A'),
                    productQuantity=user_data.get('productQuantity', 'N/A'),
                    country=user_data.get('country', 'N/A'),
                    email=user_data.get('email', 'N/A'),
                    phoneNumber=user_data.get('phoneNumber', 'N/A')
                )
                body_parts.append(formatted_detail)
            body_parts.append('')  # Empty line
        
        # Add next steps section
        next_steps_section = template.get('next_steps_section', '')
        if next_steps_section:
            body_parts.append(next_steps_section)
            next_steps = template.get('next_steps', [])
            for i, step in enumerate(next_steps, 1):
                body_parts.append(f"{i}. {step}")
            body_parts.append('')  # Empty line
        
        # Add about section
        about_section = template.get('about_section', '')
        if about_section:
            body_parts.append(about_section)
            about_intro = template.get('about_intro', '')
            if about_intro:
                body_parts.append(about_intro)
            about_services = template.get('about_services', [])
            for service in about_services:
                body_parts.append(f"- {service}")
            body_parts.append('')  # Empty line
        
        # Add contact section
        contact_section = template.get('contact_section', '')
        if contact_section:
            body_parts.append(contact_section)
            contact_info = template.get('contact_info', [])
            for contact in contact_info:
                body_parts.append(contact)
            body_parts.append('')  # Empty line
        
        # Add resources section
        resources_section = template.get('resources_section', '')
        if resources_section:
            body_parts.append(resources_section)
            resources = template.get('resources', [])
            for resource in resources:
                body_parts.append(resource)
            body_parts.append('')  # Empty line
        
        # Add closing
        closing = template.get('closing', '')
        if closing:
            body_parts.append(closing)
            body_parts.append('')  # Empty line
        
        # Add signature
        signature = template.get('signature', '')
        if signature:
            body_parts.append(signature)
        
        # Join all parts to create the email body
        email_body = '\n'.join(body_parts)
        
        msg = Message(
            subject=subject,
            recipients=[user_data.get('email')],
            body=email_body
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        return False

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            if send_reset_email(user):
                flash('Password reset email sent! Please check your email.', 'success')
            else:
                flash('Failed to send reset email. Please configure your email settings in the .env file.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        
        return redirect(url_for('main.login'))
    
    return render_template('admin/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.check_reset_token(token):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('admin/reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('admin/reset_password.html', token=token)
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('admin/reset_password.html', token=token)

@bp.route('/')
def action_page():
    return render_template('action-page.html')

@bp.route('/home')
def home():
    # events = Event.query.order_by(Event.date.asc()).all()
    # Fetch active VIPs ordered by display_order
    vips = VIP.query.filter_by(is_active=True).order_by(VIP.display_order.asc(), VIP.created_at.desc()).all()
    return render_template('home.html', vips=vips)

@bp.route('/about')
def about():
    breadcrumbs = [("Home", "/"), ("About", None)]
    return render_template('about.html', crumbs=breadcrumbs)

@bp.route('/policy-documents')
def policy_documents():
    breadcrumbs = [("Home", "/"), ("Policy Documents", None)]
    return render_template('policy-documents.html', crumbs=breadcrumbs)

@bp.route('/white-paper')
def white_paper():
    breadcrumbs = [("Home", "/"), ("White Paper", None)]
    return render_template('white-paper.html', crumbs=breadcrumbs)

@bp.route('/business-laws')
def business_laws():
    breadcrumbs = [("Home", "/"), ("Business Laws", None)]
    return render_template('business-laws.html', crumbs=breadcrumbs)

@bp.route('/publication')
def publications():
    breadcrumbs = [("Home", "/"), ("Publications", None)]
    return render_template('publications.html', crumbs=breadcrumbs)

@bp.route('/add-event', methods=['POST'])
@login_required
@validate_session
def add_event():
    title = request.form.get('title')
    date = request.form.get('date')
    location = request.form.get('location')

    try:
        event_date = datetime.strptime(date, "%Y-%m-%dT%H:%M")  # from datetime-local input
        new_event = Event(title=title, date=event_date, location=location)
        db.session.add(new_event)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        print("Error:", e)
        return jsonify({'status': 'error', 'message': str(e)})

@bp.route('/get-events')
@login_required
@validate_session
def get_events_data():
    try:
        events = Event.query.order_by(Event.date.asc()).all()
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'date': event.date.strftime('%Y-%m-%d %H:%M'),
                'location': event.location
            })
        return jsonify({'status': 'success', 'events': events_data})
    except Exception as e:
        print("Error fetching events:", e)
        return jsonify({'status': 'error', 'message': str(e)})

@bp.route('/get-event/<int:event_id>')
@login_required
@validate_session
def get_single_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        event_data = {
            'id': event.id,
            'title': event.title,
            'date': event.date.strftime('%Y-%m-%d %H:%M'),
            'date_input': event.date.strftime('%Y-%m-%dT%H:%M'),  # For datetime-local input
            'location': event.location
        }
        return jsonify({'status': 'success', 'event': event_data})
    except Exception as e:
        print("Error fetching event:", e)
        return jsonify({'status': 'error', 'message': str(e)})

@bp.route('/delete-event/<int:event_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Event deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print("Error deleting event:", e)
        return jsonify({'status': 'error', 'message': str(e)})

@bp.route('/update-event/<int:event_id>', methods=['PUT'])
@login_required
@validate_session
def update_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        
        title = request.form.get('title')
        date = request.form.get('date')
        location = request.form.get('location')
        
        if title:
            event.title = title
        if date:
            event_date = datetime.strptime(date, "%Y-%m-%dT%H:%M")
            event.date = event_date
        if location:
            event.location = location
            
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Event updated successfully'})
    except Exception as e:
        db.session.rollback()
        print("Error updating event:", e)
        return jsonify({'status': 'error', 'message': str(e)})



@bp.route('/misssion-vision-history')
def mvh():
    breadcrumbs = [("Home", "/"), ("Mission-Vission-Code Of Conduct", None)]
    return render_template('misssion-vision-history.html', crumbs=breadcrumbs)

@bp.route('/our-news')
def news():
    breadcrumbs = [("Home", "/"), ("Our News", None)]
    return render_template('all-news.html', crumbs=breadcrumbs)

@bp.route('/about-me')
def about_me():
    breadcrumbs = [("Home", "/"), ("About", "/about"), ("about-me", None)]
    return render_template('about-me.html', crumbs=breadcrumbs)


@bp.route('/export-inqury', methods=['GET', 'POST'])
def export_enqury():
    if request.method == 'POST':
        try:
            # Security checks
            # 1. Check honeypot field
            honeypot_value = request.form.get('website', '').strip()
            if honeypot_value:
                print(f"Bot detected via honeypot: {honeypot_value}")
                return render_template('export-inqury.html', show_modal=True, 
                                   message="Form submission blocked due to suspicious activity.")
            
            # 2. Check consent
            terms_consent = request.form.get('terms_consent') == 'on'
            if not terms_consent:
                return render_template('export-inqury.html', show_modal=True, 
                                   message="You must agree to the Terms and Conditions to submit this form.")
            
            # 3. Rate limiting (basic implementation)
            client_ip = request.remote_addr
            recent_submissions = ExportInquiry.query.filter(
                ExportInquiry.ip_address == client_ip,
                ExportInquiry.submitted_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_submissions >= 5:  # Max 5 submissions per hour per IP
                return render_template('export-inqury.html', show_modal=True, 
                                   message="Too many submissions from this IP. Please try again later.")
            
            # Create export inquiry with security tracking
            export_enqury = ExportInquiry(
                full_name=request.form.get('name'),
                company_name=request.form.get('companyName'),
                email=request.form.get('email'),
                phone_number=request.form.get('phoneNumber'),
                country=request.form.get('select'),
                product_quantity=request.form.get('productQuantity'),
                product_details=request.form.get('productDetails'),
                sender_details=request.form.get('senderDetails'),
                export_requirements=request.form.get('exportRequirements'),
                terms_consent=terms_consent,
                marketing_consent=request.form.get('marketing_consent') == 'on',
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(export_enqury)
            db.session.commit()
            
            # Send confirmation email
            user_data = {
                'name': export_enqury.full_name,
                'companyName': export_enqury.company_name,
                'productQuantity': export_enqury.product_quantity,
                'country': export_enqury.country,
                'email': export_enqury.email
            }
            send_form_confirmation_email('export', user_data, export_enqury.id)

            return render_template('export-inqury.html', show_modal=True, 
                               message="Thank you for your submission. We've sent a confirmation email to the address you provided. A member of our team will contact you soon.")
                               
        except Exception as e:
            db.session.rollback()
            return render_template('export-inqury.html', show_modal=True, 
                               message="An error occurred while submitting the form. Please try again.")

    breadcrumbs = [("Home", "/"), ("Trade", ""), ("Export Inquiry", None)]
    return render_template('export-inqury.html', crumbs=breadcrumbs)


@bp.route('/import-inqury', methods=['GET', 'POST'])
def import_enqury():
    if request.method == 'POST':
        try:
            # Security checks
            # 1. Check honeypot field
            honeypot_value = request.form.get('website', '').strip()
            if honeypot_value:
                print(f"Bot detected via honeypot: {honeypot_value}")
                return render_template('import-inqury.html', show_modal=True, 
                                   message="Form submission blocked due to suspicious activity.")
            
            # 2. Check consent
            terms_consent = request.form.get('terms_consent') == 'on'
            if not terms_consent:
                return render_template('import-inqury.html', show_modal=True, 
                                   message="You must agree to the Terms and Conditions to submit this form.")
            
            # 3. Rate limiting (basic implementation)
            client_ip = request.remote_addr
            recent_submissions = ImportInquiry.query.filter(
                ImportInquiry.ip_address == client_ip,
                ImportInquiry.submitted_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_submissions >= 5:  # Max 5 submissions per hour per IP
                return render_template('import-inqury.html', show_modal=True, 
                                   message="Too many submissions from this IP. Please try again later.")
            
            # Create import inquiry with security tracking
            import_inquiry = ImportInquiry(
                full_name=request.form.get('name'),
                company_name=request.form.get('companyName'),
                email=request.form.get('email'),
                phone_number=request.form.get('phoneNumber'),
                country=request.form.get('select'),
                product_quantity=request.form.get('productQuantity'),
                product_details=request.form.get('productDetails'),
                sender_details=request.form.get('senderDetails'),
                terms_consent=terms_consent,
                marketing_consent=request.form.get('marketing_consent') == 'on',
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(import_inquiry)
            db.session.commit()
            
            # Send confirmation email
            user_data = {
                'name': import_inquiry.full_name,
                'companyName': import_inquiry.company_name,
                'productQuantity': import_inquiry.product_quantity,
                'country': import_inquiry.country,
                'email': import_inquiry.email
            }
            send_form_confirmation_email('import', user_data, import_inquiry.id)

            return render_template('import-inqury.html', show_modal=True, 
                               message="Thank you for your submission. We've sent a confirmation email to the address you provided. A member of our team will contact you soon.")
                               
        except Exception as e:
            db.session.rollback()
            print(f"Import inquiry error: {str(e)}")
            return render_template('import-inqury.html', show_modal=True, 
                               message="An error occurred while submitting the form. Please try again.")
        
    breadcrumbs = [("Home", "/"), ("Trade", "/Trade"), ("Import Enquiry", None)]
    return render_template("import-inqury.html", crumbs=breadcrumbs)


@bp.route('/business-opportunity', methods=['GET', 'POST'])
def business_opportunity():
    if request.method == 'POST':
        try:
            # Security checks
            # 1. Check honeypot field
            honeypot_value = request.form.get('website', '').strip()
            if honeypot_value:
                print(f"Bot detected via honeypot: {honeypot_value}")
                return render_template('business-opportunity.html', show_modal=True, 
                                   message="Form submission blocked due to suspicious activity.")
            
            # 2. Check consent
            terms_consent = request.form.get('terms_consent') == 'on'
            if not terms_consent:
                return render_template('business-opportunity.html', show_modal=True, 
                                   message="You must agree to the Terms and Conditions to submit this form.")
            
            # 3. Rate limiting (basic implementation)
            client_ip = request.remote_addr
            recent_submissions = BusinessOpportunity.query.filter(
                BusinessOpportunity.ip_address == client_ip,
                BusinessOpportunity.submitted_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_submissions >= 5:  # Max 5 submissions per hour per IP
                return render_template('business-opportunity.html', show_modal=True, 
                                   message="Too many submissions from this IP. Please try again later.")
            
            # Create business opportunity with security tracking
            business_opportunity = BusinessOpportunity(
                full_name=request.form.get('name'),
                email=request.form.get('email'),
                phone_number=request.form.get('phoneNumber'),
                business_opportunity=request.form.get('businessOpportunity'),
                terms_consent=terms_consent,
                marketing_consent=request.form.get('marketing_consent') == 'on',
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(business_opportunity)
            db.session.commit()
            
            # Send confirmation email
            user_data = {
                'name': business_opportunity.full_name,
                'email': business_opportunity.email,
                'phoneNumber': business_opportunity.phone_number,
                'businessOpportunity': business_opportunity.business_opportunity
            }
            send_form_confirmation_email('business_opportunity', user_data, business_opportunity.id)

            return render_template('business-opportunity.html', show_modal=True, 
                               message="Thank you for your submission. We've sent a confirmation email to the address you provided. A member of our team will contact you soon.")
                               
        except Exception as e:
            db.session.rollback()
            print(f"Business opportunity error: {str(e)}")
            return render_template('business-opportunity.html', show_modal=True, 
                               message="An error occurred while submitting the form. Please try again.")
    breadcrumbs = [("Home", "/"), ("Trade", "/Trade"), ("Business Opportunity", None)]
    return render_template('business-opportunity.html', crumbs=breadcrumbs)

@bp.route('/suggestions', methods=['GET', 'POST'])
def suggestions():
    if request.method == 'POST':
        try:
            # Security checks
            # 1. Check honeypot field
            honeypot_value = request.form.get('website', '').strip()
            if honeypot_value:
                print(f"Bot detected via honeypot: {honeypot_value}")
                return render_template('suggestions.html', show_modal=True, 
                                   message="Form submission blocked due to suspicious activity.")
            
            # 2. Check consent
            terms_consent = request.form.get('terms_consent') == 'on'
            if not terms_consent:
                return render_template('suggestions.html', show_modal=True, 
                                   message="You must agree to the Terms and Conditions to submit this form.")
            
            # 3. Rate limiting (basic implementation)
            client_ip = request.remote_addr
            recent_submissions = Suggestions.query.filter(
                Suggestions.ip_address == client_ip,
                Suggestions.submitted_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_submissions >= 5:  # Max 5 submissions per hour per IP
                return render_template('suggestions.html', show_modal=True, 
                                   message="Too many submissions from this IP. Please try again later.")
            
            # Create suggestion with security tracking
            suggestion = Suggestions(
                full_name=request.form.get('name'),
                email=request.form.get('email'),
                phone_number=request.form.get('phoneNumber'),
                suggestions=request.form.get('suggestions'),
                terms_consent=terms_consent,
                marketing_consent=request.form.get('marketing_consent') == 'on',
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(suggestion)
            db.session.commit()
            
            # Send confirmation email
            user_data = {
                'name': suggestion.full_name,
                'email': suggestion.email,
                'phoneNumber': suggestion.phone_number,
                'suggestions': suggestion.suggestions
            }
            send_form_confirmation_email('suggestions', user_data, suggestion.id)

            return render_template('suggestions.html', show_modal=True, 
                               message="Thank you for your submission. We've sent a confirmation email to the address you provided. A member of our team will contact you soon.")
                               
        except Exception as e:
            db.session.rollback()
            print(f"Suggestion error: {str(e)}")
            return render_template('suggestions.html', show_modal=True, 
                               message="An error occurred while submitting the form. Please try again.")
    breadcrumbs = [("Home", "/"), ("Trade", "/Trade"), ("Suggestions", None)]
    return render_template('suggestions.html', crumbs=breadcrumbs)


@bp.route('/complaints', methods=["GET", "POST"])
def complaints():
    if request.method == 'POST':
        try:
            honeypot_value = request.form.get('website', '').strip()
            if honeypot_value:
                return render_template('complaints.html', show_modal=True,
                                       message="Form submission blocked due to suspicious activity.")

            terms_consent = request.form.get('terms_consent') == 'on'
            if not terms_consent:
                return render_template('complaints.html', show_modal=True,
                                       message="You must agree to the Terms and Conditions to submit this form.")

            client_ip = request.remote_addr
            recent_submissions = Complaints.query.filter(
                Complaints.ip_address == client_ip,
                Complaints.submitted_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()

            if recent_submissions >= 5:
                return render_template('complaints.html', show_modal=True,
                                       message="Too many submissions from this IP. Please try again later.")

            complaint = Complaints(
                full_name=request.form.get('name'),
                email=request.form.get('email'),
                phone_number=request.form.get('phoneNumber'),
                complaints=request.form.get('complaints'),
                terms_consent=terms_consent,
                marketing_consent=request.form.get('marketing_consent') == 'on',
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', '')
            )

            db.session.add(complaint)
            db.session.commit()
            
            # Send confirmation email
            user_data = {
                'name': complaint.full_name,
                'email': complaint.email,
                'phoneNumber': complaint.phone_number,
                'complaints': complaint.complaints
            }
            send_form_confirmation_email('complaints', user_data, complaint.id)

            return render_template('complaints.html', show_modal=True,
                                   message="Thank you for your submission. We've sent a confirmation email to the address you provided. A member of our team will contact you soon.")

        except Exception as e:
            db.session.rollback()
            print(f"Complaint form error: {str(e)}")
            return render_template('complaints.html', show_modal=True,
                                   message="An error occurred while submitting the form. Please try again.")

    breadcrumbs = [("Home", "/"), ("Trade", "/Trade"), ("Complaints", None)]
    return render_template('complaints.html', crumbs=breadcrumbs)



@bp.route('/my-gallery')
def myGallery():
    # return render_template('myGallery.html')
    breadcrumbs = [("Home", "/"), ("About", "/about"), ("MyGallery", None)]
    base_folder = os.path.join('app', 'static', 'media')
    folders = [name for name in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, name))]
    return render_template('myGallery.html', folders=folders, crumbs=breadcrumbs)


@bp.route('/my-gallery/<folder_name>')
def show_folder(folder_name):
    folder_path = os.path.join(current_app.static_folder, 'media', folder_name)
    if not os.path.exists(folder_path):
        return "Folder not found", 404

    files = os.listdir(folder_path)
    images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    videos = [f for f in files if f.lower().endswith(('.mp4', '.webm', '.ogg'))]

    return render_template('gallery_images.html', folder=folder_name, images=images, videos=videos)



# @bp.route('/leadership-board')
# def leadership_board():
#     return render_template('leadership_board.html')

@bp.route('/download-brochure', methods=['POST'])
def download_brochure():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company = request.form.get('company')
        job_title = request.form.get('job_title')
        country = request.form.get('country')
        interest = request.form.get('interest')
        consent = request.form.get('consent') == 'on'

        # Server-side validation
        missing_fields = []
        if not name: missing_fields.append('name')
        if not email: missing_fields.append('email')
        if not phone: missing_fields.append('phone')
        if not country: missing_fields.append('country')
        if not interest: missing_fields.append('interest')
        if not consent: missing_fields.append('consent')

        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Save to DB
        try:
            print(f"Attempting to save brochure inquiry for {email}")  # Debug log
            new_inquiry = BrochureInquiry(
                name=name,
                email=email,
                phone=phone,
                company=company,
                job_title=job_title,
                country=country,
                interest=interest,
                consent=consent
            )
            db.session.add(new_inquiry)
            print("Added to session, attempting commit...")  # Debug log
            db.session.commit()
            print(f"Successfully saved brochure inquiry for {email}")  # Add success logging
        except Exception as db_error:
            db.session.rollback()
            print(f"Database error: {db_error}")  # Add logging for debugging
            print(f"Error type: {type(db_error)}")  # Debug log
            import traceback
            print(f"Traceback: {traceback.format_exc()}")  # Debug log
            return jsonify({'error': 'Database error occurred.'}), 500

        # Send brochure
        brochure_path = os.path.join(current_app.root_path, 'static', 'brochures', 'TACCI_Brochure.pdf')
        if not os.path.exists(brochure_path):
            return jsonify({'error': 'Brochure file not found.'}), 404

        return send_file(brochure_path, as_attachment=True, download_name='TACCI_Brochure.pdf')

    except Exception as e:
        db.session.rollback()
        print(f"General error in download_brochure: {e}")  # Add general error logging
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


@bp.route('/get-brochure')
@login_required
@validate_session
def get_brochure_data():
    try:
        # Get all brochure inquiries
        brochure_inquiries = BrochureInquiry.query.order_by(BrochureInquiry.submitted_at.desc()).all()
        
        brochure_data = []
        for inquiry in brochure_inquiries:
            brochure_data.append({
                'id': inquiry.id,
                'name': inquiry.name,
                'email': inquiry.email,
                'phone': inquiry.phone,
                'company': inquiry.company,
                'job_title': inquiry.job_title,
                'country': inquiry.country,
                'interest': inquiry.interest,
                'submitted_at': inquiry.submitted_at.strftime('%d-%m-%Y'),
                'status': 'Active'  # You can add a status field to the model if needed
            })
        
        return jsonify({
            'status': 'success',
            'brochure': brochure_data
        })
    except Exception as e:
        print(f"Error fetching brochure data: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch brochure data'
        }), 500



@bp.route('/delete-brochure/<brochure_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_brochure(brochure_id):
    try:
        inquiry = BrochureInquiry.query.get_or_404(brochure_id)
        db.session.delete(inquiry)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Brochure inquiry deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting brochure inquiry: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to delete brochure inquiry'
        }), 500


@bp.route('/leadership-board')
def leadership_board():
    breadcrumbs = [("Home", "/"), ("About", "/about"), ("Governing Councils", None)]
    return render_template('leadership_board.html', members=data, crumbs=breadcrumbs)

@bp.route('/our-team')
def our_team():
    return render_template('our-team.html', team_members=team_members)

@bp.route('/membership-types')
def membership_types():
    breadcrumbs = [("Home", "/"), ("Membership", ""), ("Membership Type", None)]
    return render_template('membership-types.html', crumbs=breadcrumbs)

@bp.route('/membership-benefit')
def membership_benefit():
    breadcrumbs = [("Home", "/"), ("Membership", ""), ("Membership Benefit", None)]
    return render_template('membership-benefit.html', crumbs=breadcrumbs)

@bp.route("/bank-transfer", methods=["GET"])
def payment():
    # We now always display the bank details directly without requiring form submission
    return render_template("membership-form.html")

@bp.route('/membership-form', methods=['GET', 'POST'])
def membership_form():
    step = int(request.args.get('step', 0))
    member_id = request.args.get('member_id')
    is_edit = bool(member_id)

    # Clear session data on GET and not editing
    if request.method == 'GET' and not is_edit and step == 0:
        session.pop('personalData', None)
        session.pop('membershipDetails', None)
        session.pop('editing_member_id', None)
        session.pop('terms_accepted', None)

    

    if request.method == 'GET' and is_edit and step == 0:
        member = Member.query.get_or_404(member_id)
        session['personalData'] = {
            "application_name": member.application_name,
            "qualification": member.qualification,
            "birth_place": member.birth_place,
            "date_of_birth": member.date_of_birth.strftime('%Y-%m-%d') if member.date_of_birth else "",
            "email": member.email,
            "website": member.website,
            "nationality": member.nationality,
            "passport_number": member.passport_number,
            "company_name": member.company_name,
            "designation": member.designation,
            "phone_number": member.phone_number,
            "address": member.address,
            "city": member.city,
            "country": member.country,
            "state": member.state,
            "zipcode": member.zipcode
        }
        session['membershipDetails'] = {
            "membership_type": member.membership_type,
            "amount_paid": member.amount_paid,
            "residence_phone": member.residence_phone,
            "spouse_name": member.spouse_name,
            "number_of_children": member.number_of_children,
            "spouse_birth_date": member.spouse_birth_date.strftime('%Y-%m-%d') if member.spouse_birth_date else ""
        }
        session['editing_member_id'] = member.id

    if request.method == 'POST':
        if step == 0:
            # Handle Terms & Conditions acceptance
            terms_accepted = request.form.get('terms')
            if not terms_accepted:
                flash("You must agree to the Terms & Conditions to continue.", "error")
                return redirect(url_for('main.membership_form', step=0, member_id=member_id if is_edit else None))
            
            # Store terms acceptance in session
            session['terms_accepted'] = True
            return redirect(url_for('main.membership_form', step=1, member_id=member_id if is_edit else None))

        elif step == 1:
            session['personalData'] = {
                key: request.form.get(key)
                for key in [
                    "application_name", "qualification", "birth_place", "date_of_birth",
                    "email", "website", "nationality", "passport_number",
                    "company_name", "designation", "phone_number", "address",
                    "city", "country", "state", "zipcode"
                ]
            }
            return redirect(url_for('main.membership_form', step=2, member_id=member_id if is_edit else None))

        elif step == 2:
            # Validate numeric fields
            amount_paid = request.form.get("amount_paid", "")
            number_of_children = request.form.get("number_of_children", "")
            error = False
            # Allow decimal for amount_paid
            try:
                float_amount_paid = float(amount_paid)
            except (ValueError, TypeError):
                flash("Amount Paid must be a valid number.", "error")
                error = True
            # Allow empty or integer for number_of_children
            if number_of_children:
                try:
                    int_number_of_children = int(number_of_children)
                except (ValueError, TypeError):
                    flash("Number of Children must be a valid integer.", "error")
                    error = True
            if error:
                session['membershipDetails'] = {
                    key: request.form.get(key)
                    for key in [
                        "membership_type", "amount_paid", "residence_phone",
                        "spouse_name", "number_of_children", "spouse_birth_date"
                    ]
                }
                return redirect(url_for('main.membership_form', step=2, member_id=member_id if is_edit else None))

            session['membershipDetails'] = {
                key: request.form.get(key)
                for key in [
                    "membership_type", "amount_paid", "residence_phone",
                    "spouse_name", "number_of_children", "spouse_birth_date"
                ]
            }
            return redirect(url_for('main.membership_form', step=3, member_id=member_id if is_edit else None))

        elif step == 3:
            # Check if terms were accepted
            if not session.get('terms_accepted'):
                flash("You must agree to the Terms & Conditions to submit the form.", "error")
                return redirect(url_for('main.membership_form', step=0, member_id=member_id if is_edit else None))
            
            try:
                personal = session.get('personalData', {})
                member_data = session.get('membershipDetails', {})

                # Convert dates
                dob = datetime.strptime(personal.get('date_of_birth'), '%Y-%m-%d').date() if personal.get('date_of_birth') else None
                spouse_dob = datetime.strptime(member_data.get('spouse_birth_date'), '%Y-%m-%d').date() if member_data.get('spouse_birth_date') else None

                if is_edit:
                    member = Member.query.get_or_404(session.get('editing_member_id'))
                else:
                    member = Member()

                # Assign personal data
                for key, value in personal.items():
                    setattr(member, key, value)
                member.date_of_birth = dob

                # Assign membership details with type conversion
                member.membership_type = member_data.get('membership_type')
                # Convert amount_paid to float/decimal
                try:
                    member.amount_paid = float(member_data.get('amount_paid', 0))
                except (ValueError, TypeError):
                    member.amount_paid = 0
                member.residence_phone = member_data.get('residence_phone')
                member.spouse_name = member_data.get('spouse_name')
                # Convert number_of_children to int
                try:
                    member.number_of_children = int(member_data.get('number_of_children', 0)) if member_data.get('number_of_children') else 0
                except (ValueError, TypeError):
                    member.number_of_children = 0
                member.spouse_birth_date = spouse_dob

                if not is_edit:
                    db.session.add(member)

                db.session.commit()
                session.pop('personalData', None)
                session.pop('membershipDetails', None)
                session.pop('editing_member_id', None)
                session.pop('terms_accepted', None)

                flash(f"Membership form {'updated' if is_edit else 'submitted'} successfully!", 'success')
                return redirect(url_for('main.membership_form', step=4))

            except Exception as e:
                db.session.rollback()
                flash(f"Error saving form: {str(e)}", 'error')
                return redirect(url_for('main.membership_form', step=3, member_id=member_id if is_edit else None))

    return render_template(
        'membership-form.html',
        step=step,
        personalData=session.get('personalData', {}),
        membershipDetails=session.get('membershipDetails', {}),
        is_edit=is_edit
    )


@bp.route('/thank-you')
def thank_you():
    return "<h2>Thank you for your submission!</h2>"

@bp.route('/demo-past-events')
def demo_past_event():
    breadcrumbs = [("Home", "/"), ("Past Events", None)]
    return render_template("demo-past-event.html", breadcrumbs=breadcrumbs )

@bp.route('/past-events')
def past_event_page():
    # Load latest past event with its images for public page without altering layout
    past_event = PastEvent.query.order_by(PastEvent.event_date.is_(None), PastEvent.event_date.desc(), PastEvent.created_at.desc()).first()
    images = past_event.images if past_event else []
    sidebar_events = PastEvent.query.order_by(PastEvent.event_date.is_(None), PastEvent.event_date.desc(), PastEvent.created_at.desc()).all()
    breadcrumbs = [("Home", "/"), ("Past Events", None)]
    return render_template("past-events.html", past_event=past_event, past_event_images=images, sidebar_events=sidebar_events, breadcrumbs=breadcrumbs)


@bp.route('/past-events/<int:past_event_id>')
def past_event_detail(past_event_id):
    # Render same layout for a specific past event
    past_event = PastEvent.query.get_or_404(past_event_id)
    sidebar_events = PastEvent.query.order_by(PastEvent.event_date.is_(None), PastEvent.event_date.desc(), PastEvent.created_at.desc()).all()
    return render_template("past-events.html", past_event=past_event, past_event_images=past_event.images, sidebar_events=sidebar_events)


# ---------------- Admin APIs for Past Events ----------------

def _delete_past_event_assets_folder(event_id):
    try:
        folder_path = os.path.join('app', 'static', 'images', 'past_events', f"event_{event_id}")
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f"Error deleting past event assets for event {event_id}: {e}")


@bp.route('/admin/past-events/create', methods=['POST'])
@login_required
@validate_session
def admin_create_past_event():
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    try:
        title = request.form.get('title', '').strip()
        event_date_raw = request.form.get('event_date', '').strip()

        if not title:
            return jsonify({'status': 'error', 'message': 'Title is required'}), 400

        # Create event first to get ID
        event = PastEvent(title=title)
        if event_date_raw:
            try:
                event.event_date = datetime.strptime(event_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid event_date format, expected YYYY-MM-DD'}), 400

        db.session.add(event)
        db.session.commit()

        folder_name = f"event_{event.id}"

        # Save banner image if provided
        banner_file = request.files.get('banner_image')
        if banner_file:
            banner_path = save_uploaded_file(banner_file, folder_name)
            if not banner_path:
                return jsonify({'status': 'error', 'message': 'Invalid banner image type'}), 400
            event.banner_image_path = banner_path
            db.session.commit()

        # Handle multiple gallery images with descriptions and optional orders
        gallery_files = request.files.getlist('gallery_images')
        descriptions = request.form.getlist('gallery_descriptions')
        orders = request.form.getlist('gallery_orders')

        images_created = []
        for index, img_file in enumerate(gallery_files):
            if not img_file:
                continue
            saved_path = save_uploaded_file(img_file, folder_name)
            if not saved_path:
                # skip invalid files rather than failing the whole request
                continue
            description_text = descriptions[index] if index < len(descriptions) else None
            try:
                display_order = int(orders[index]) if index < len(orders) and orders[index] is not None and orders[index] != '' else index
            except ValueError:
                display_order = index
            past_img = PastEventImage(
                past_event_id=event.id,
                image_path=saved_path,
                description=description_text,
                display_order=display_order
            )
            db.session.add(past_img)
            images_created.append(saved_path)

        if images_created:
            db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Past event created successfully',
            'event': {
                'id': event.id,
                'title': event.title,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'banner_image_path': event.banner_image_path,
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error creating past event: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to create past event'}), 500


@bp.route('/admin/past-events/list', methods=['GET'])
@login_required
@validate_session
def admin_list_past_events():
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    events = PastEvent.query.order_by(PastEvent.event_date.is_(None), PastEvent.event_date.desc(), PastEvent.created_at.desc()).all()
    data = []
    for ev in events:
        data.append({
            'id': ev.id,
            'title': ev.title,
            'event_date': ev.event_date.isoformat() if ev.event_date else None,
            'banner_image_path': ev.banner_image_path
        })
    return jsonify({'status': 'success', 'events': data})


@bp.route('/admin/past-events/<int:event_id>', methods=['GET'])
@login_required
@validate_session
def admin_get_past_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    ev = PastEvent.query.get_or_404(event_id)
    return jsonify({
        'status': 'success',
        'event': {
            'id': ev.id,
            'title': ev.title,
            'event_date': ev.event_date.isoformat() if ev.event_date else None,
            'banner_image_path': ev.banner_image_path,
            'images': [
                {
                    'id': im.id,
                    'image_path': im.image_path,
                    'description': im.description,
                    'display_order': im.display_order
                } for im in ev.images
            ]
        }
    })


@bp.route('/admin/past-events/<int:event_id>', methods=['DELETE'])
@login_required
@validate_session
def admin_delete_past_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        ev = PastEvent.query.get_or_404(event_id)
        db.session.delete(ev)
        db.session.commit()
        _delete_past_event_assets_folder(event_id)
        return jsonify({'status': 'success', 'message': 'Past event deleted'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting past event {event_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete past event'}), 500


@bp.route('/admin/past-events/<int:event_id>/images', methods=['POST'])
@login_required
@validate_session
def admin_add_images_to_past_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        ev = PastEvent.query.get_or_404(event_id)
        folder_name = f"event_{ev.id}"

        gallery_files = request.files.getlist('gallery_images')
        descriptions = request.form.getlist('gallery_descriptions')
        orders = request.form.getlist('gallery_orders')

        created = []
        for index, img_file in enumerate(gallery_files):
            if not img_file:
                continue
            saved_path = save_uploaded_file(img_file, folder_name)
            if not saved_path:
                continue
            description_text = descriptions[index] if index < len(descriptions) else None
            try:
                display_order = int(orders[index]) if index < len(orders) and orders[index] is not None and orders[index] != '' else index
            except ValueError:
                display_order = index
            past_img = PastEventImage(
                past_event_id=ev.id,
                image_path=saved_path,
                description=description_text,
                display_order=display_order
            )
            db.session.add(past_img)
            created.append(saved_path)

        if created:
            db.session.commit()

        return jsonify({'status': 'success', 'message': 'Images added', 'count': len(created)})
    except Exception as e:
        db.session.rollback()
        print(f"Error adding images to past event {event_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to add images'}), 500


@bp.route('/admin/past-events/<int:event_id>/update', methods=['POST'])
@login_required
@validate_session
def admin_update_past_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        ev = PastEvent.query.get_or_404(event_id)
        title = request.form.get('title', '').strip()
        event_date_raw = request.form.get('event_date', '').strip()

        if title:
            ev.title = title
        if event_date_raw:
            try:
                ev.event_date = datetime.strptime(event_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid event_date format, expected YYYY-MM-DD'}), 400

        # Optional banner replacement
        banner_file = request.files.get('banner_image')
        if banner_file and allowed_file(banner_file.filename):
            folder_name = f"event_{ev.id}"
            banner_path = save_uploaded_file(banner_file, folder_name)
            if not banner_path:
                return jsonify({'status': 'error', 'message': 'Invalid banner image type'}), 400
            ev.banner_image_path = banner_path

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Past event updated', 'event': {
            'id': ev.id,
            'title': ev.title,
            'event_date': ev.event_date.isoformat() if ev.event_date else None,
            'banner_image_path': ev.banner_image_path
        }})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating past event {event_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update past event'}), 500


@bp.route('/admin/past-events/images/<int:image_id>', methods=['PUT', 'DELETE'])
@login_required
@validate_session
def admin_update_or_delete_past_event_image(image_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        img = PastEventImage.query.get_or_404(image_id)
        if request.method == 'DELETE':
            # delete underlying file if exists
            try:
                rel_path = img.image_path.lstrip('/')
                fs_path = os.path.join('app', rel_path) if not rel_path.startswith('app/') else rel_path
                if os.path.exists(fs_path):
                    os.remove(fs_path)
            except Exception:
                pass
            db.session.delete(img)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Image deleted'})

        # PUT update description/order
        description = request.form.get('description')
        display_order = request.form.get('display_order')
        if description is not None:
            img.description = description
        if display_order is not None and display_order != '':
            try:
                img.display_order = int(display_order)
            except ValueError:
                pass
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Image updated'})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating/deleting image {image_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update image'}), 500

@bp.route('/contact', methods=['GET', 'POST'])
def contact_page():
    form = ContactFormWT()
    
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        website = request.form.get('website', '').strip()
        purpose = request.form.get('purpose', '').strip()
        message = request.form.get('message', '').strip()

        # Validate required fields
        if not name or not email or not purpose:
            flash("Please fill in all required fields (name, email, purpose)", "danger")
            return redirect(url_for('main.contact_page'))

        # Basic email validation
        if '@' not in email or '.' not in email:
            flash("Please enter a valid email address", "danger")
            return redirect(url_for('main.contact_page'))

        try:
            submission = ContactForm(
                name=name,
                email=email,
                website=website if website else None,
                purpose=purpose,
                message=message if message else None
            )
            db.session.add(submission)
            db.session.commit()

            flash("Your message has been submitted successfully!", "success")
            return redirect(url_for('main.contact_page'))
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
            flash("An error occurred while submitting your message. Please try again.", "danger")
            return redirect(url_for('main.contact_page'))

    breadcrumbs = [("Home", "/"), ("Contact Us", None)]
    return render_template("contact.html", crumbs=breadcrumbs, form=form)


# ---------------- Budget Events Public Pages ----------------

@bp.route('/budget-events')
def budget_events_page():
    events = BudgetEvent.query.order_by(BudgetEvent.event_date.is_(None), BudgetEvent.event_date.desc(), BudgetEvent.created_at.desc()).all()
    return render_template("budgetEvent.html", budget_events=events)

@bp.route('/budget-events/<int:event_id>')
def budget_events_detail_page(event_id):
    ev = BudgetEvent.query.get_or_404(event_id)
    return render_template("budgetEventDetails.html", event=ev, images=ev.images)


# ---------------- Admin APIs for Budget Events ----------------

def _delete_budget_event_assets_folder(event_id):
    try:
        folder_path = os.path.join('app', 'static', 'images', 'budget_events', f"event_{event_id}")
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f"Error deleting budget event assets for event {event_id}: {e}")


@bp.route('/admin/budget-events/create', methods=['POST'])
@login_required
@validate_session
def admin_create_budget_event():
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        title = request.form.get('title', '').strip()
        event_date_raw = request.form.get('event_date', '').strip()

        if not title:
            return jsonify({'status': 'error', 'message': 'Title is required'}), 400

        ev = BudgetEvent(title=title)
        if event_date_raw:
            try:
                ev.event_date = datetime.strptime(event_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid event_date format, expected YYYY-MM-DD'}), 400

        db.session.add(ev)
        db.session.commit()

        folder_name = f"event_{ev.id}"

        banner_file = request.files.get('banner_image')
        if banner_file:
            banner_path = save_uploaded_budget_file(banner_file, folder_name)
            if not banner_path:
                return jsonify({'status': 'error', 'message': 'Invalid banner image type'}), 400
            ev.banner_image_path = banner_path
            db.session.commit()

        gallery_files = request.files.getlist('gallery_images')
        descriptions = request.form.getlist('gallery_descriptions')
        orders = request.form.getlist('gallery_orders')

        created = []
        for index, img_file in enumerate(gallery_files):
            if not img_file:
                continue
            saved_path = save_uploaded_budget_file(img_file, folder_name)
            if not saved_path:
                continue
            description_text = descriptions[index] if index < len(descriptions) else None
            try:
                display_order = int(orders[index]) if index < len(orders) and orders[index] is not None and orders[index] != '' else index
            except ValueError:
                display_order = index
            img = BudgetEventImage(
                budget_event_id=ev.id,
                image_path=saved_path,
                description=description_text,
                display_order=display_order
            )
            db.session.add(img)
            created.append(saved_path)

        if created:
            db.session.commit()

        return jsonify({'status': 'success', 'message': 'Budget event created successfully', 'event': {
            'id': ev.id,
            'title': ev.title,
            'event_date': ev.event_date.isoformat() if ev.event_date else None,
            'banner_image_path': ev.banner_image_path
        }})
    except Exception as e:
        db.session.rollback()
        print(f"Error creating budget event: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to create budget event'}), 500


@bp.route('/admin/budget-events/list', methods=['GET'])
@login_required
@validate_session
def admin_list_budget_events():
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    events = BudgetEvent.query.order_by(BudgetEvent.event_date.is_(None), BudgetEvent.event_date.desc(), BudgetEvent.created_at.desc()).all()
    data = []
    for ev in events:
        data.append({
            'id': ev.id,
            'title': ev.title,
            'event_date': ev.event_date.isoformat() if ev.event_date else None,
            'banner_image_path': ev.banner_image_path
        })
    return jsonify({'status': 'success', 'events': data})


@bp.route('/admin/budget-events/<int:event_id>', methods=['GET'])
@login_required
@validate_session
def admin_get_budget_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    ev = BudgetEvent.query.get_or_404(event_id)
    return jsonify({'status': 'success', 'event': {
        'id': ev.id,
        'title': ev.title,
        'event_date': ev.event_date.isoformat() if ev.event_date else None,
        'banner_image_path': ev.banner_image_path,
        'images': [
            {
                'id': im.id,
                'image_path': im.image_path,
                'description': im.description,
                'display_order': im.display_order
            } for im in ev.images
        ]
    }})


@bp.route('/admin/budget-events/<int:event_id>', methods=['DELETE'])
@login_required
@validate_session
def admin_delete_budget_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        ev = BudgetEvent.query.get_or_404(event_id)
        db.session.delete(ev)
        db.session.commit()
        _delete_budget_event_assets_folder(event_id)
        return jsonify({'status': 'success', 'message': 'Budget event deleted'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting budget event {event_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete budget event'}), 500


@bp.route('/admin/budget-events/<int:event_id>/images', methods=['POST'])
@login_required
@validate_session
def admin_add_images_to_budget_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        ev = BudgetEvent.query.get_or_404(event_id)
        folder_name = f"event_{ev.id}"

        gallery_files = request.files.getlist('gallery_images')
        descriptions = request.form.getlist('gallery_descriptions')
        orders = request.form.getlist('gallery_orders')

        created = []
        for index, img_file in enumerate(gallery_files):
            if not img_file:
                continue
            saved_path = save_uploaded_budget_file(img_file, folder_name)
            if not saved_path:
                continue
            description_text = descriptions[index] if index < len(descriptions) else None
            try:
                display_order = int(orders[index]) if index < len(orders) and orders[index] is not None and orders[index] != '' else index
            except ValueError:
                display_order = index
            img = BudgetEventImage(
                budget_event_id=ev.id,
                image_path=saved_path,
                description=description_text,
                display_order=display_order
            )
            db.session.add(img)
            created.append(saved_path)

        if created:
            db.session.commit()

        return jsonify({'status': 'success', 'message': 'Images added', 'count': len(created)})
    except Exception as e:
        db.session.rollback()
        print(f"Error adding images to budget event {event_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to add images'}), 500


@bp.route('/admin/budget-events/<int:event_id>/update', methods=['POST'])
@login_required
@validate_session
def admin_update_budget_event(event_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        ev = BudgetEvent.query.get_or_404(event_id)
        title = request.form.get('title', '').strip()
        event_date_raw = request.form.get('event_date', '').strip()

        if title:
            ev.title = title
        if event_date_raw:
            try:
                ev.event_date = datetime.strptime(event_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid event_date format, expected YYYY-MM-DD'}), 400

        banner_file = request.files.get('banner_image')
        if banner_file and allowed_file(banner_file.filename):
            folder_name = f"event_{ev.id}"
            banner_path = save_uploaded_budget_file(banner_file, folder_name)
            if not banner_path:
                return jsonify({'status': 'error', 'message': 'Invalid banner image type'}), 400
            ev.banner_image_path = banner_path

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Budget event updated', 'event': {
            'id': ev.id,
            'title': ev.title,
            'event_date': ev.event_date.isoformat() if ev.event_date else None,
            'banner_image_path': ev.banner_image_path
        }})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating budget event {event_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update budget event'}), 500


@bp.route('/admin/budget-events/images/<int:image_id>', methods=['PUT', 'DELETE'])
@login_required
@validate_session
def admin_update_or_delete_budget_event_image(image_id):
    if current_user.role not in ['host', 'member']:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        img = BudgetEventImage.query.get_or_404(image_id)
        if request.method == 'DELETE':
            try:
                rel_path = img.image_path.lstrip('/')
                fs_path = os.path.join('app', rel_path) if not rel_path.startswith('app/') else rel_path
                if os.path.exists(fs_path):
                    os.remove(fs_path)
            except Exception:
                pass
            db.session.delete(img)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Image deleted'})

        description = request.form.get('description')
        display_order = request.form.get('display_order')
        if description is not None:
            img.description = description
        if display_order is not None and display_order != '':
            try:
                img.display_order = int(display_order)
            except ValueError:
                pass
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Image updated'})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating/deleting budget image {image_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update image'}), 500

@bp.route('/events')
def all_events_page():
    # Ensure both values are passed
    breadcrumbs = [("Home", "/"), ("Events", "/events"), ("Past Events", None)]
    event_details_list = get_events()
    selected_event = event_details_list[0] if event_details_list else None
    return render_template("events.html", events=event_details_list, selected_event=selected_event,  crumbs=breadcrumbs)

@bp.route('/events/<int:event_id>')
def event_detail_page(event_id):
    event_details_list = get_events()
    selected_event = next((e for e in event_details_list if e["id"] == event_id), None)
    if selected_event:
        breadcrumbs = [("Home", "/"), ("Events", "/events"), (selected_event["title"], None)]
        return render_template("events.html", events=event_details_list, selected_event=selected_event, crumbs=breadcrumbs)
    return "Event not found", 404



@bp.route('/upcoming-event')
def upcoming_page():
    return render_template("upcoming-event.html")

@bp.route('/Budget-Event')
def budget_event():
    events = BudgetEvent.query.order_by(BudgetEvent.event_date.is_(None), BudgetEvent.event_date.desc(), BudgetEvent.created_at.desc()).all()
    return render_template("budgetEvent.html", budget_events=events)

@bp.route('/Budget-Event-Details/<int:event_id>')
def budget_event_details(event_id):
    ev = BudgetEvent.query.get_or_404(event_id)
    return render_template("budgetEventDetails.html", event=ev, images=ev.images)

@bp.route('/your-route')
def your_route():
    cookie_preferences = get_cookie('cookie_preferences', default={'necessary': True, 'analytics': False, 'marketing': False})
    
    # Only set analytics cookies if user has accepted them
    if cookie_preferences.get('analytics'):
        # Set analytics cookies
        pass
    
    # Only set marketing cookies if user has accepted them
    if cookie_preferences.get('marketing'):
        # Set marketing cookies
        pass

@bp.route('/api/cookie-consent', methods=['POST'])
def handle_cookie_consent():
    """
    Handle cookie consent preferences
    """
    try:
        data = request.get_json()
        analytics = data.get('analytics', False)
        marketing = data.get('marketing', False)
        
        response = make_response(jsonify({'status': 'success'}))
        response = set_cookie_consent(response, analytics=analytics, marketing=marketing)
        
        return response
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# API routes for admin functionality
@bp.route('/api/export-inquiry/<int:inquiry_id>')
@login_required
@validate_session
def get_export_inquiry(inquiry_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    inquiry = ExportInquiry.query.get_or_404(inquiry_id)
    return jsonify({
        'id': inquiry.id,
        'full_name': inquiry.full_name,
        'company_name': inquiry.company_name,
        'email': inquiry.email,
        'phone_number': inquiry.phone_number,
        'country': inquiry.country,
        'product_quantity': inquiry.product_quantity,
        'product_details': inquiry.product_details,
        'export_requirements': inquiry.export_requirements,
        'submitted_at': inquiry.submitted_at.strftime('%Y-%m-%d %H:%M')
    })

@bp.route('/api/export-inquiry/<int:inquiry_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_export_inquiry(inquiry_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    inquiry = ExportInquiry.query.get_or_404(inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/import-inquiry/<int:inquiry_id>')
@login_required
@validate_session
def get_import_inquiry(inquiry_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    inquiry = ImportInquiry.query.get_or_404(inquiry_id)
    return jsonify({
        'id': inquiry.id,
        'full_name': inquiry.full_name,
        'company_name': inquiry.company_name,
        'email': inquiry.email,
        'phone_number': inquiry.phone_number,
        'country': inquiry.country,
        'product_quantity': inquiry.product_quantity,
        'product_details': inquiry.product_details,
        'sender_details': inquiry.sender_details,
        'submitted_at': inquiry.submitted_at.strftime('%Y-%m-%d %H:%M')
    })

@bp.route('/api/import-inquiry/<int:inquiry_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_import_inquiry(inquiry_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    inquiry = ImportInquiry.query.get_or_404(inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/business-opportunity/<int:opportunity_id>')
@login_required
@validate_session
def get_business_opportunity(opportunity_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    opportunity = BusinessOpportunity.query.get_or_404(opportunity_id)
    return jsonify({
        'id': opportunity.id,
        'full_name': opportunity.full_name,
        'email': opportunity.email,
        'phone_number': opportunity.phone_number,
        'business_opportunity': opportunity.business_opportunity,
        'submitted_at': opportunity.submitted_at.strftime('%Y-%m-%d %H:%M')
    })

@bp.route('/api/business-opportunity/<int:opportunity_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_business_opportunity(opportunity_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    opportunity = BusinessOpportunity.query.get_or_404(opportunity_id)
    db.session.delete(opportunity)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/suggestion/<int:suggestion_id>')
@login_required
@validate_session
def get_suggestion(suggestion_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    suggestion = Suggestions.query.get_or_404(suggestion_id)
    return jsonify({
        'id': suggestion.id,
        'full_name': suggestion.full_name,
        'email': suggestion.email,
        'phone_number': suggestion.phone_number,
        'suggestions': suggestion.suggestions,
        'submitted_at': suggestion.submitted_at.strftime('%Y-%m-%d %H:%M')
    })

@bp.route('/api/suggestion/<int:suggestion_id>/status', methods=['PUT'])
@login_required
@validate_session
def update_suggestion_status(suggestion_id):
    if current_user.role != 'member':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    suggestion = Suggestions.query.get_or_404(suggestion_id)
    # Add status field to Suggestions model if not exists
    # suggestion.status = data.get('status')
    # suggestion.notes = data.get('notes')
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/suggestion/<int:suggestion_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_suggestion(suggestion_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    suggestion = Suggestions.query.get_or_404(suggestion_id)
    db.session.delete(suggestion)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/complaint/<int:complaint_id>')
@login_required
@validate_session
def get_complaint(complaint_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    complaint = Complaints.query.get_or_404(complaint_id)
    return jsonify({
        'id': complaint.id,
        'full_name': complaint.full_name,
        'email': complaint.email,
        'phone_number': complaint.phone_number,
        'complaints': complaint.complaints,
        'submitted_at': complaint.submitted_at.strftime('%Y-%m-%d %H:%M')
    })

@bp.route('/api/complaint/<int:complaint_id>/status', methods=['PUT'])
@login_required
@validate_session
def update_complaint_status(complaint_id):
    if current_user.role != 'member':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    complaint = Complaints.query.get_or_404(complaint_id)
    # Add status field to Complaints model if not exists
    # complaint.status = data.get('status')
    # complaint.notes = data.get('notes')
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/complaint/<int:complaint_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_complaint(complaint_id):
    if current_user.role not in ['member', 'host']:
        return jsonify({'error': 'Access denied'}), 403
    
    complaint = Complaints.query.get_or_404(complaint_id)
    db.session.delete(complaint)
    db.session.commit()
    return jsonify({'success': True})


# Separate admin pages for better organization
@bp.route('/admin/export-inquiry')
@login_required
@validate_session
def admin_export_inquiry():
    if current_user.role != 'member':
        return "Access denied", 403
    export_inquiries = ExportInquiry.query.order_by(ExportInquiry.submitted_at.desc()).all()
    return render_template('admin/export-inquiry.html', export_inquiries=export_inquiries)

@bp.route('/admin/import-inquiry')
@login_required
@validate_session
def admin_import_inquiry():
    if current_user.role != 'member':
        return "Access denied", 403
    import_inquiries = ImportInquiry.query.order_by(ImportInquiry.submitted_at.desc()).all()
    return render_template('admin/import-inquiry.html', import_inquiries=import_inquiries)

@bp.route('/admin/business-opportunity')
@login_required
@validate_session
def admin_business_opportunity():
    if current_user.role != 'member':
        return "Access denied", 403
    business_opportunities = BusinessOpportunity.query.order_by(BusinessOpportunity.submitted_at.desc()).all()
    return render_template('admin/business-opportunity.html', business_opportunities=business_opportunities)

@bp.route('/admin/suggestions')
@login_required
@validate_session
def admin_suggestions():
    if current_user.role != 'member':
        return "Access denied", 403
    suggestions = Suggestions.query.order_by(Suggestions.submitted_at.desc()).all()
    return render_template('admin/suggestions.html', suggestions=suggestions)

@bp.route('/admin/complaints')
@login_required
@validate_session
def admin_complaints():
    complaints = Complaints.query.order_by(Complaints.submitted_at.desc()).all()
    return render_template('admin/complaints.html', complaints=complaints)



@bp.route('/test-email')
def test_email():
    """Test route to verify email configuration"""
    try:
        from flask import current_app
        if not current_app.config.get('MAIL_SERVER') or not current_app.config.get('MAIL_USERNAME'):
            return "Email configuration not set up. Please configure MAIL_SERVER and MAIL_USERNAME in your .env file."
        
        msg = Message(
            subject='Test Email - TransChamber',
            recipients=['test@example.com'],
            body='This is a test email from TransChamber to verify email configuration.'
        )
        mail.send(msg)
        return "Email sent successfully! Check your email configuration."
    except Exception as e:
        return f"Email error: {str(e)}"


# --------------------------------------Past Events Section Start--------------------------------------

# VIP Management Routes

@bp.route('/admin/vip/add', methods=['POST'])
@login_required
@validate_session
def add_vip():
    """Add a new VIP"""
    try:
        name = request.form.get('name')
        designation = request.form.get('designation', '')
        company = request.form.get('company', '')
        description = request.form.get('description', '')
        display_order = int(request.form.get('display_order', 0))
        is_active = 'is_active' in request.form
        
        # Handle image upload (optional)
        image_file = request.files.get('image')
        image_path = None
        
        if image_file and allowed_file(image_file.filename):
            # Save image
            filename = secure_filename(image_file.filename)
            name_part, ext = os.path.splitext(filename)
            filename = f"vip_{name_part}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
            
            # Create vips folder if it doesn't exist
            upload_folder = os.path.join('app', 'static', 'images', 'vips')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            
            image_path = f"static/images/vips/{filename}"
        
        # Create VIP record
        vip = VIP(
            name=name,
            designation=designation,
            company=company,
            description=description,
            image_path=image_path,
            display_order=display_order,
            is_active=is_active
        )
        
        db.session.add(vip)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'VIP added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@bp.route('/admin/vip/<int:vip_id>', methods=['GET'])
@login_required
@validate_session
def get_vip(vip_id):
    """Get VIP details for editing"""
    try:
        vip = VIP.query.get_or_404(vip_id)
        return jsonify({
            'status': 'success',
            'vip': {
                'id': vip.id,
                'name': vip.name,
                'designation': vip.designation,
                'company': vip.company,
                'description': vip.description,
                'image_path': vip.image_path,
                'display_order': vip.display_order,
                'is_active': vip.is_active
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@bp.route('/admin/vip/update', methods=['POST'])
@login_required
@validate_session
def update_vip():
    """Update VIP details"""
    try:
        vip_id = request.form.get('vip_id')
        vip = VIP.query.get_or_404(vip_id)
        
        vip.name = request.form.get('name')
        vip.designation = request.form.get('designation', '')
        vip.company = request.form.get('company', '')
        vip.description = request.form.get('description', '')
        vip.display_order = int(request.form.get('display_order', 0))
        vip.is_active = 'is_active' in request.form
        
        # Handle image upload if provided
        image_file = request.files.get('image')
        if image_file and allowed_file(image_file.filename):
            # Delete old image if exists
            if vip.image_path:
                vip.delete_image_file()
            
            # Save new image
            filename = secure_filename(image_file.filename)
            name_part, ext = os.path.splitext(filename)
            filename = f"vip_{name_part}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
            
            upload_folder = os.path.join('app', 'static', 'images', 'vips')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            
            vip.image_path = f"static/images/vips/{filename}"
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'VIP updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@bp.route('/admin/vip/list', methods=['GET'])
@login_required
@validate_session
def get_vip_list():
    """Get list of all VIPs for dashboard"""
    try:
        vips = VIP.query.order_by(VIP.display_order.asc(), VIP.created_at.desc()).all()
        vip_list = []
        for vip in vips:
            vip_list.append({
                'id': vip.id,
                'name': vip.name,
                'designation': vip.designation,
                'company': vip.company,
                'description': vip.description,
                'image_path': vip.image_path,
                'is_active': vip.is_active,
                'display_order': vip.display_order,
                'created_at': vip.created_at.isoformat() if vip.created_at else None,
                'updated_at': vip.updated_at.isoformat() if vip.updated_at else None
            })
        return jsonify({'status': 'success', 'vips': vip_list})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/admin/vip/<int:vip_id>', methods=['DELETE'])
@login_required
@validate_session
def delete_vip(vip_id):
    """Delete VIP"""
    try:
        vip = VIP.query.get_or_404(vip_id)
        
        # Delete image file
        vip.delete_image_file()
        
        # Delete from database
        db.session.delete(vip)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'VIP deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/test-db')
def test_database():
    """Test route to check database connectivity and user creation"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Check if User table exists
        users = User.query.all()
        
        # Try to create a test user
        test_user = User(
            username='test_user_' + str(uuid.uuid4())[:8],
            email='test@example.com',
            role='member'
        )
        test_user.set_password('testpass123')
        
        db.session.add(test_user)
        db.session.commit()
        
        # Delete the test user
        db.session.delete(test_user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Database is working correctly',
            'user_count': len(users),
            'test_user_created': True
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}',
            'error_type': type(e).__name__
        })

@bp.route('/test-config')
def test_config():
    """Test route to check configuration settings"""
    from flask import current_app
    
    config_info = {
        'secret_key_set': bool(current_app.config.get('SECRET_KEY')),
        'database_uri_set': bool(current_app.config.get('SQLALCHEMY_DATABASE_URI')),
        'session_lifetime': str(current_app.config.get('PERMANENT_SESSION_LIFETIME')),
        'debug_mode': current_app.debug,
        'environment': current_app.env
    }
    
    return jsonify({
        'status': 'success',
        'config': config_info
    })