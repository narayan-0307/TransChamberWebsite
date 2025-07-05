from flask import Flask, Blueprint, render_template, request, session, url_for, redirect, jsonify, make_response
from app.api.team_api import team_members  # Importing team members from the API module
from app.api.events_api import get_events
from app.api.events_details import event_details_list # Importing events from the API module

from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from config import Config  # Importing configuration settings
from flask import flash  # Add this import
from datetime import datetime  # Add this import

from app.api.leadershipBoard_api import data

from app.models import db, Member  # Importing the Member model
from app.utils import get_cookie, set_cookie_consent

import json
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    events = get_events()  # <-- Call the function here
    return render_template('home.html', events=events)  # Use plural if multiple

@bp.route('/about')
def about():
    breadcrumbs = [("Home", "/"), ("About", None)]
    return render_template('about.html', crumbs=breadcrumbs)

@bp.route('/misssion-vision-history')
def mvh():
    return render_template('misssion-vision-history.html')

@bp.route('/about-me')
def about_me():
    breadcrumbs = [("Home", "/"), ("About", "/about"), ("about-me", None)]
    return render_template('about-me.html', crumbs=breadcrumbs)


@bp.route('/my-gallery')
def myGallery():
    # return render_template('myGallery.html')
    breadcrumbs = [("Home", "/"), ("About", "/about"), ("MyGallery", None)]
    base_folder = os.path.join('app', 'static', 'media')
    folders = [name for name in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, name))]
    return render_template('myGallery.html', folders=folders, crumbs=breadcrumbs)


@bp.route('/my-gallery/<folder_name>')
def show_folder(folder_name):
    folder_path = os.path.join('app', 'static', 'media', folder_name)
    if not os.path.exists(folder_path):
        return "Folder not found", 404

    files = os.listdir(folder_path)
    images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    videos = [f for f in files if f.lower().endswith(('.mp4', '.webm', '.ogg'))]

    return render_template('gallery_images.html', folder=folder_name, images=images, videos=videos)


# @bp.route('/leadership-board')
# def leadership_board():
#     return render_template('leadership_board.html')



@bp.route('/leadership-board')
def leadership_board():
    breadcrumbs = [("Home", "/"), ("About", "/about"), ("Leadership Board", None)]
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
    breadcrumbs = [("Home", "/"), ("Membership", ""), ("Membership Type", None)]
    return render_template('membership-benefit.html', crumbs=breadcrumbs)

@bp.route('/membership-form', methods=['GET', 'POST'])
def membership_form():
    step = int(request.args.get('step', '1'))
    member_id = request.args.get('member_id')
    is_edit = bool(member_id)

    if is_edit and step == 1:
        # Fetch member data for editing
        member = Member.query.get_or_404(member_id)
        session["personalData"] = {
            "application_name": member.application_name,
            "qualification": member.qualification,
            "birth_place": member.birth_place,
            "date_of_birth": member.date_of_birth.strftime('%Y-%m-%d'),
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
        session["membershipDetails"] = {
            "membership_type": member.membership_type,
            "amount_paid": member.amount_paid,
            "residence_phone": member.residence_phone,
            "spouse_name": member.spouse_name,
            "number_of_children": member.number_of_children,
            "spouse_birth_date": member.spouse_birth_date.strftime('%Y-%m-%d') if member.spouse_birth_date else None
        }
        session["editing_member_id"] = member_id

    if request.method == 'POST':
        if step == 1:
            # Store personal data in session
            date_of_birth = request.form.get('date_of_birth')
            if date_of_birth:
                date_of_birth = date_of_birth  # already in YYYY-MM-DD
            
            session["personalData"] = {
                "application_name": request.form.get('application_name'),
                "qualification": request.form.get('qualification'),
                "birth_place": request.form.get('birth_place'),
                "date_of_birth": date_of_birth,
                "email": request.form.get('email'),
                "website": request.form.get('website'),
                "nationality": request.form.get('nationality'),
                "passport_number": request.form.get('passport_number'),
                "company_name": request.form.get('company_name'),
                "designation": request.form.get('designation'),
                "phone_number": request.form.get('phone_number'),
                "address": request.form.get('address'),
                "city": request.form.get('city'),
                "country": request.form.get('country'),
                "state": request.form.get('state'),
                "zipcode": request.form.get('zipcode')
            }
            return redirect(url_for('main.membership_form', step=2, member_id=member_id if is_edit else None))
        
        elif step == 2:
            # Store membership details in session
            spouse_birth_date = request.form.get('spouse_birth_date')
            if spouse_birth_date:
                spouse_birth_date = spouse_birth_date  # already in YYYY-MM-DD
            
            session["membershipDetails"] = {
                "membership_type": request.form.get('membership_type'),
                "amount_paid": request.form.get('amount_paid'),
                "residence_phone": request.form.get('residence_phone'),
                "spouse_name": request.form.get('spouse_name'),
                "number_of_children": request.form.get('number_of_children'),
                "spouse_birth_date": spouse_birth_date
            }
            return redirect(url_for('main.membership_form', step=3, member_id=member_id if is_edit else None))
        
        elif step == 3:
            try:
                # Get data from session
                personalData = session.get('personalData', {})
                membershipDetails = session.get('membershipDetails', {})

                # Convert date strings back to date objects
                dob = personalData.get('date_of_birth')
                if dob:
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                spouse_bd = membershipDetails.get('spouse_birth_date')
                if spouse_bd:
                    spouse_bd = datetime.strptime(spouse_bd, '%Y-%m-%d').date()

                if is_edit:
                    # Update existing member
                    member = Member.query.get_or_404(session.get('editing_member_id'))
                    member.application_name = personalData.get('application_name')
                    member.qualification = personalData.get('qualification')
                    member.birth_place = personalData.get('birth_place')
                    member.date_of_birth = dob
                    member.email = personalData.get('email')
                    member.website = personalData.get('website')
                    member.nationality = personalData.get('nationality')
                    member.passport_number = personalData.get('passport_number')
                    member.company_name = personalData.get('company_name')
                    member.designation = personalData.get('designation')
                    member.phone_number = personalData.get('phone_number')
                    member.address = personalData.get('address')
                    member.city = personalData.get('city')
                    member.country = personalData.get('country')
                    member.state = personalData.get('state')
                    member.zipcode = personalData.get('zipcode')
                    member.membership_type = membershipDetails.get('membership_type')
                    member.amount_paid = membershipDetails.get('amount_paid')
                    member.residence_phone = membershipDetails.get('residence_phone')
                    member.spouse_name = membershipDetails.get('spouse_name')
                    member.number_of_children = membershipDetails.get('number_of_children')
                    member.spouse_birth_date = spouse_bd
                else:
                    # Create new member
                    new_member = Member(
                        application_name=personalData.get('application_name'),
                        qualification=personalData.get('qualification'),
                        birth_place=personalData.get('birth_place'),
                        date_of_birth=dob,
                        email=personalData.get('email'),
                        website=personalData.get('website'),
                        nationality=personalData.get('nationality'),
                        passport_number=personalData.get('passport_number'),
                        company_name=personalData.get('company_name'),
                        designation=personalData.get('designation'),
                        phone_number=personalData.get('phone_number'),
                        address=personalData.get('address'),
                        city=personalData.get('city'),
                        country=personalData.get('country'),
                        state=personalData.get('state'),
                        zipcode=personalData.get('zipcode'),
                        membership_type=membershipDetails.get('membership_type'),
                        amount_paid=membershipDetails.get('amount_paid'),
                        residence_phone=membershipDetails.get('residence_phone'),
                        spouse_name=membershipDetails.get('spouse_name'),
                        number_of_children=membershipDetails.get('number_of_children'),
                        spouse_birth_date=spouse_bd
                    )
                    db.session.add(new_member)

                db.session.commit()
                session.pop('personalData', None)
                session.pop('membershipDetails', None)
                session.pop('editing_member_id', None)
                
                flash('Your membership form has been ' + ('updated' if is_edit else 'submitted') + ' successfully!', 'success')
                return redirect(url_for('main.membership_form', step=4))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving your data: {str(e)}', 'error')
                return redirect(url_for('main.membership_form', step=3, member_id=member_id if is_edit else None))

    # For GET requests, render the template with session data
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

@bp.route('/contact')
def contact_page():
    breadcrumbs = [("Home", "/"), ("Contact Us", None)]
    return render_template("contact.html", crumbs=breadcrumbs)

@bp.route('/events')
def all_events_page():
    # Ensure both values are passed
    breadcrumbs = [("Home", "/"), ("Events", "/events"), ("Past Events", None)]
    selected_event = event_details_list[0] if event_details_list else None
    return render_template("events.html", events=event_details_list, selected_event=selected_event,  crumbs=breadcrumbs)

@bp.route('/events/<int:event_id>')
def event_detail_page(event_id):
    selected_event = next((e for e in event_details_list if e["id"] == event_id), None)
    if selected_event:
        return render_template("events.html", events=event_details_list, selected_event=selected_event)
    return "Event not found", 404



@bp.route('/upcoming-event')
def upcoming_page():
    return render_template("upcoming-event.html")

# @bp.route('/Budget-Event')
# def budget_event():
#     return render_template("budgetEvent.html")

from app.api.budgetEvents_api import BudgetEvents  # or use json.load if stored as .json file

@bp.route('/Budget-Event/<int:event_id>')
def budget_event(event_id):
    # Use Python list or load from JSON file
    event = next((e for e in BudgetEvents if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404

    return render_template("budgetEvent.html", event=event, all_events=BudgetEvents)


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
