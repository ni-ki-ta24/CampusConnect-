from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone, timedelta
from functools import wraps
import os
import socket
import random
import string

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    """User model for students, faculty, and admins"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, faculty, hod, dean, principal, admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class Notice(db.Model):
    """Notice model for academic and event notices"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='general')  # academic, event, general, urgent
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='notices')

class Event(db.Model):
    """Event model for college events"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100))
    organized_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='events')

class Club(db.Model):
    """Club model for student clubs"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='clubs')

class Issue(db.Model):
    """Issue model for campus issues reporting"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # water, cleanliness, hostel, other
    status = db.Column(db.String(20), default='pending')  # pending, resolved
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='issues')

class AccessShare(db.Model):
    """Model for sharing access with other users"""
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_level = db.Column(db.String(50), default='view')  # view, edit, full
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    
    owner = db.relationship('User', foreign_keys=[owner_id], backref='shared_access')
    shared_with = db.relationship('User', foreign_keys=[shared_with_id], backref='received_access')

# ==================== TEAM MODELS ====================

class Team(db.Model):
    """Team model for collaborative work"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_public = db.Column(db.Boolean, default=True)
    
    creator = db.relationship('User', backref='created_teams')
    members = db.relationship('TeamMember', backref='team', cascade='all, delete-orphan')
    activities = db.relationship('TeamActivity', backref='team', cascade='all, delete-orphan')

class TeamMember(db.Model):
    """Team member association model"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, member
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='team_memberships')
    
    __table_args__ = (db.UniqueConstraint('team_id', 'user_id', name='unique_team_member'),)

class TeamActivity(db.Model):
    """Team activity log for tracking all actions"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created_notice, created_event, etc.
    details = db.Column(db.Text)
    item_type = db.Column(db.String(50))  # notice, event, club, issue
    item_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='team_activities')

# ==================== PLACEMENT MODELS ====================

class Placement(db.Model):
    """Placement records - companies visiting campus"""
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    package = db.Column(db.String(100))  # Salary package
    location = db.Column(db.String(100))
    eligibility = db.Column(db.String(200))  # Eligible branches
    last_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, completed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='placements')
    applications = db.relationship('PlacementApplication', backref='placement', cascade='all, delete-orphan')

class PlacementApplication(db.Model):
    """Student applications for placements"""
    id = db.Column(db.Integer, primary_key=True)
    placement_id = db.Column(db.Integer, db.ForeignKey('placement.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='applied')  # applied, shortlisted, rejected, selected
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    student = db.relationship('User', backref='placement_applications')
    
    __table_args__ = (db.UniqueConstraint('placement_id', 'student_id', name='unique_application'),)

# ==================== OTP MODEL ====================

class OTP(db.Model):
    """OTP verification model for email verification"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via email (simulated - prints to console)"""
    print(f"\n{'='*50}")
    print(f"OTP EMAIL SIMULATION")
    print(f"{'='*50}")
    print(f"To: {email}")
    print(f"Subject: CampusConnect+ Email Verification")
    print(f"Message: Your OTP is {otp}")
    print(f"Valid for 10 minutes")
    print(f"{'='*50}\n")
    return True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== COLLEGE INFO ====================

COLLEGE_INFO = {
    'name': 'ISB&M College of Engineering',
    'short_name': 'ISB&M COE',
    'tagline': 'Excellence in Technical Education',
    'established': '2008',
    'address': 'ISB&M College of Engineering, Nande, Taluka - Maval, Pune - 410506, Maharashtra, India',
    'phone': '+91-2114-223123',
    'email': 'info@isbmcoe.org',
    'website': 'www.isbmcoe.org',
    'photo': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRm4jRZHhndxjhE8SB-G3Jk_neowqXesHhDdw&s',
    'vision': 'To become a premier institute in technical education by providing holistic education to students.',
    'mission': 'To impart quality technical education through innovative teaching-learning processes.',
    'about': 'ISBM College of Engineering is a premier technical institution.',
    'courses': [
        {'name': 'B.E. in Computer Engineering', 'duration': '4 Years', 'intake': '120'},
        {'name': 'B.E. in Mechanical Engineering', 'duration': '4 Years', 'intake': '60'},
        {'name': 'B.E. in Electronics & Telecommunication', 'duration': '4 Years', 'intake': '60'}
    ],
    'principal': 'Dr. P.K. Srivastava',
    'contact': 'coe@isbmcoe.org',
    'departments': [
        {'name': 'Computer Engineering', 'icon': 'laptop', 'description': 'Software Development, AI, ML', 'hod': 'Prof Dikshendra Sarpate', 'intake': '180'},
        {'name': 'Mechanical Engineering', 'icon': 'cogs', 'description': 'Automobile, Thermal, Manufacturing', 'hod': 'Dr. Vaibhav Edake', 'intake': '60'},
        {'name': 'Electrical Engineering', 'icon': 'bolt', 'description': 'Power Systems, Electronics', 'hod': 'Dr. V. H. Shinde', 'intake': '60'},
        {'name': 'Electronics & Telecommunication', 'icon': 'wifi', 'description': 'Communication, Embedded Systems', 'hod': 'Prof Sitaram Longani', 'intake': '30'},
        {'name': 'AI & Data Science', 'icon': 'brain', 'description': 'Artificial Intelligence, Data Science, Machine Learning', 'hod': 'Prof Anil V. Walke', 'intake': '120'},
        {'name': 'AI & ML', 'icon': 'robot', 'description': 'Artificial Intelligence & Machine Learning', 'hod': 'Prof Kirti Randhe', 'intake': '120'},
        {'name': 'Applied Science (1st Year)', 'icon': 'flask', 'description': 'First Year Engineering Courses', 'hod': 'Prof Krishna Kr. Yadav', 'intake': '300'},
        {'name': 'CSE', 'icon': 'desktop', 'description': 'Computer Science & Engineering', 'hod': 'Prof Dikshendra Sarpate', 'intake': '60'},
        {'name': 'VLSI', 'icon': 'microchip', 'description': 'VLSI Design & Technology', 'hod': 'Dr. M. S. Chougule', 'intake': '60'},
        {'name': 'BBA', 'icon': 'briefcase', 'description': 'Bachelor of Business Administration', 'hod': 'Prof. R. R. Sharma', 'intake': '120'},
        {'name': 'BCA', 'icon': 'laptop-code', 'description': 'Bachelor of Computer Applications', 'hod': 'Prof. S. D. Kathole', 'intake': '120'}
    ],
    'facilities': [
        {'name': 'Central Library', 'icon': 'book', 'description': 'Digital library with 15,000+ books'},
        {'name': 'Computer Center', 'icon': 'desktop', 'description': '300+ computers with internet'},
        {'name': 'Sports Complex', 'icon': 'football-ball', 'description': 'Cricket ground, basketball court'},
        {'name': 'Hostel', 'icon': 'bed', 'description': 'Safe accommodation for students'}
    ],
    'achievements': [
        {'title': 'NBA Accreditation', 'description': 'All programs NBA accredited', 'year': '2022'},
        {'title': 'Best Engineering College', 'description': 'Award in Mumbai region', 'year': '2023'}
    ],
    'recruiters': ['TCS', 'Infosys', 'Wipro', 'Accenture', 'Cognizant', 'Capgemini']
}

# ==================== ROLE-BASED ACCESS CONTROL ====================

def role_required(*allowed_roles):
    def decorator(f):
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

# ==================== ROUTES ====================

@app.route('/')
def index():
    now = datetime.now(timezone.utc)
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
    events = Event.query.filter(Event.date >= now).order_by(Event.date).limit(5).all()
    clubs = Club.query.limit(6).all()
    return render_template('index.html', notices=notices, events=events, clubs=clubs, college=COLLEGE_INFO)

@app.route('/college')
def college_info():
    return render_template('college.html', college=COLLEGE_INFO)

@app.route('/faculty')
def faculty():
    faculty_members = [
        {'name': 'Dr. A. K. Patil', 'designation': 'Professor & HOD', 'department': 'Computer Engineering', 'qualification': 'Ph.D.'},
        {'name': 'Dr. S. M. Joshi', 'designation': 'Professor & HOD', 'department': 'Mechanical Engineering', 'qualification': 'Ph.D.'}
    ]
    return render_template('faculty.html', faculty=faculty_members)

@app.route('/gallery')
def gallery():
    gallery_images = [
        {'title': 'College Building', 'category': 'campus', 'url': 'https://images.unsplash.com/photo-1562774053-701939374585?w=400'},
        {'title': 'Library', 'category': 'campus', 'url': 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=400'}
    ]
    return render_template('gallery.html', images=gallery_images)

@app.route('/departments')
def departments():
    return render_template('departments.html', college=COLLEGE_INFO)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        # Generate OTP and send
        otp_code = generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Create OTP record
        otp = OTP(email=email, otp_code=otp_code, expires_at=expires_at)
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP (simulated - prints to console)
        send_otp_email(email, otp_code)
        
        # Store email in session for verification
        session['pending_verification_email'] = email
        
        flash(f'OTP sent to {email}! Check the server console for the OTP.', 'info')
        return redirect(url_for('verify_otp'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed! Please check your credentials.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/notices')
def notices():
    category = request.args.get('category')
    if category:
        notices = Notice.query.filter_by(category=category).order_by(Notice.created_at.desc()).all()
    else:
        notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('notices.html', notices=notices)


@app.route('/notices/new', methods=['GET', 'POST'])
@login_required
def new_notice():
    # HOD, Faculty, Dean, Principal, Admin can post notices
    allowed_roles = ['faculty', 'hod', 'dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to post notices.', 'danger')
        return redirect(url_for('notices'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', 'general')
        
        notice = Notice(title=title, content=content, category=category, posted_by=current_user.id)
        db.session.add(notice)
        db.session.commit()
        
        flash('Notice posted successfully!', 'success')
        return redirect(url_for('notices'))
    
    return render_template('new_notice.html')

@app.route('/events')
def events():
    upcoming = request.args.get('upcoming')
    now = datetime.now(timezone.utc)
    if upcoming:
        events = Event.query.filter(Event.date >= now).order_by(Event.date).all()
    else:
        events = Event.query.order_by(Event.date.desc()).all()
    return render_template('events.html', events=events)

@app.route('/events/new', methods=['GET', 'POST'])
@login_required
def new_event():
    allowed_roles = ['faculty', 'hod', 'dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to create events.', 'danger')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        location = request.form.get('location')
        
        event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        
        event = Event(title=title, description=description, date=event_date, location=location, organized_by=current_user.id)
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('new_event.html')

@app.route('/clubs')
def clubs():
    clubs = Club.query.all()
    return render_template('clubs.html', clubs=clubs)

@app.route('/clubs/new', methods=['GET', 'POST'])
@login_required
def new_club():
    allowed_roles = ['dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to create clubs.', 'danger')
        return redirect(url_for('clubs'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        club = Club(name=name, description=description, created_by=current_user.id)
        db.session.add(club)
        db.session.commit()
        
        flash('Club created successfully!', 'success')
        return redirect(url_for('clubs'))
    
    return render_template('new_club.html')

@app.route('/complaints', methods=['GET', 'POST'])
@login_required
def complaints():
    # Only students, HOD, Faculty can post complaints (NOT Dean, Principal)
    if request.method == 'POST':
        # Only students, HOD, Faculty can submit complaints
        allowed_roles_for_complaints = ['student', 'hod', 'faculty']
        if current_user.role not in allowed_roles_for_complaints:
            flash('Only students and faculty can submit complaints.', 'danger')
            return redirect(url_for('complaints'))
            
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category', 'other')
        
        issue = Issue(title=title, description=description, category=category, reported_by=current_user.id)
        db.session.add(issue)
        db.session.commit()
        
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('complaints'))
    
    issues = Issue.query.order_by(Issue.created_at.desc()).all()
    return render_template('complaints.html', issues=issues)

@app.route('/complaints/resolve/<int:issue_id>', methods=['POST'])
@login_required
def resolve_complaint(issue_id):
    allowed_roles = ['hod', 'dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to resolve complaints.', 'danger')
        return redirect(url_for('complaints'))
    
    issue = Issue.query.get_or_404(issue_id)
    issue.status = 'resolved'
    db.session.commit()
    
    flash('Complaint marked as resolved!', 'success')
    return redirect(url_for('complaints'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(10).all()
    events = Event.query.order_by(Event.created_at.desc()).limit(10).all()
    issues = Issue.query.order_by(Issue.created_at.desc()).limit(10).all()
    
    return render_template('admin.html', users=users, notices=notices, events=events, issues=issues)

@app.route('/admin/user/<int:user_id>/promote', methods=['POST'])
@login_required
def promote_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    valid_roles = ['student', 'faculty', 'hod', 'dean', 'principal', 'admin']
    if new_role in valid_roles:
        user.role = new_role
        db.session.commit()
        flash(f'User {user.username} promoted to {new_role}!', 'success')
    else:
        flash('Invalid role!', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('admin'))

# ==================== SHARE ACCESS ROUTES ====================

@app.route('/share')
@login_required
def share_access():
    """Share access dashboard - manage shared access"""
    my_shares = AccessShare.query.filter_by(owner_id=current_user.id).all()
    shared_with_me = AccessShare.query.filter_by(shared_with_id=current_user.id).all()
    other_users = User.query.filter(User.id != current_user.id).all()
    
    return render_template('share.html', 
                         my_shares=my_shares, 
                         shared_with_me=shared_with_me,
                         other_users=other_users)

@app.route('/share/create', methods=['POST'])
@login_required
def create_share():
    """Share access with another user"""
    shared_with_email = request.form.get('email')
    access_level = request.form.get('access_level', 'view')
    
    user_to_share = User.query.filter_by(email=shared_with_email).first()
    
    if not user_to_share:
        flash('User not found!', 'danger')
        return redirect(url_for('share_access'))
    
    if user_to_share.id == current_user.id:
        flash('You cannot share access with yourself!', 'danger')
        return redirect(url_for('share_access'))
    
    existing = AccessShare.query.filter_by(
        owner_id=current_user.id, 
        shared_with_id=user_to_share.id
    ).first()
    
    if existing:
        existing.access_level = access_level
        flash(f'Updated access for {user_to_share.username}', 'success')
    else:
        share = AccessShare(
            owner_id=current_user.id,
            shared_with_id=user_to_share.id,
            access_level=access_level
        )
        db.session.add(share)
        flash(f'Access shared with {user_to_share.username}', 'success')
    
    db.session.commit()
    return redirect(url_for('share_access'))

@app.route('/share/revoke/<int:share_id>', methods=['POST'])
@login_required
def revoke_share(share_id):
    """Revoke shared access"""
    share = AccessShare.query.get_or_404(share_id)
    
    if share.owner_id != current_user.id:
        flash('You can only revoke your own shares!', 'danger')
        return redirect(url_for('share_access'))
    
    user_name = share.shared_with.username
    db.session.delete(share)
    db.session.commit()
    
    flash(f'Access revoked for {user_name}', 'success')
    return redirect(url_for('share_access'))

# ==================== TEAM ROUTES ====================

# Helper function to log team activity
def log_team_activity(team_id, user_id, action, details, item_type=None, item_id=None):
    """Log an activity for the team"""
    activity = TeamActivity(
        team_id=team_id,
        user_id=user_id,
        action=action,
        details=details,
        item_type=item_type,
        item_id=item_id
    )
    db.session.add(activity)
    db.session.commit()

# Helper function to get user's teams
def get_user_teams(user_id):
    """Get all teams a user belongs to"""
    memberships = TeamMember.query.filter_by(user_id=user_id).all()
    return [m.team for m in memberships]

@app.route('/teams')
@login_required
def teams():
    """List all teams and user's teams"""
    all_teams = Team.query.all()
    my_teams = get_user_teams(current_user.id)
    return render_template('teams.html', all_teams=all_teams, my_teams=my_teams)

@app.route('/teams/new', methods=['POST'])
@login_required
def create_team():
    """Create a new team"""
    name = request.form.get('name')
    description = request.form.get('description')
    is_public = request.form.get('is_public') == 'on'
    
    # Check if team name already exists
    if Team.query.filter_by(name=name).first():
        flash('Team name already exists!', 'danger')
        return redirect(url_for('teams'))
    
    team = Team(
        name=name,
        description=description,
        created_by=current_user.id,
        is_public=is_public
    )
    db.session.add(team)
    db.session.commit()
    
    # Add creator as admin member
    member = TeamMember(team_id=team.id, user_id=current_user.id, role='admin')
    db.session.add(member)
    
    # Log activity
    log_team_activity(team.id, current_user.id, 'created_team', f'Created team "{name}"')
    
    flash(f'Team "{name}" created successfully!', 'success')
    return redirect(url_for('team_dashboard', team_id=team.id))

@app.route('/teams/<int:team_id>')
@login_required
def team_dashboard(team_id):
    """View team dashboard with activity feed"""
    team = Team.query.get_or_404(team_id)
    
    # Check if user is a member
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    is_member = membership is not None
    
    # Get team activities (recent 20)
    activities = TeamActivity.query.filter_by(team_id=team_id).order_by(TeamActivity.created_at.desc()).limit(20).all()
    
    # Get team members
    members = TeamMember.query.filter_by(team_id=team_id).all()
    
    return render_template('team_dashboard.html', team=team, activities=activities, 
                         members=members, is_member=is_member, membership=membership)

@app.route('/teams/<int:team_id>/join', methods=['POST'])
@login_required
def join_team(team_id):
    """Join a team"""
    team = Team.query.get_or_404(team_id)
    
    # Check if already a member
    existing = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if existing:
        flash('You are already a member of this team!', 'warning')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    member = TeamMember(team_id=team_id, user_id=current_user.id, role='member')
    db.session.add(member)
    
    # Log activity
    log_team_activity(team_id, current_user.id, 'joined_team', f'Joined team "{team.name}"')
    
    flash(f'You have joined team "{team.name}"!', 'success')
    return redirect(url_for('team_dashboard', team_id=team_id))

@app.route('/teams/<int:team_id>/leave', methods=['POST'])
@login_required
def leave_team(team_id):
    """Leave a team"""
    team = Team.query.get_or_404(team_id)
    
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not membership:
        flash('You are not a member of this team!', 'warning')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    # Check if user is the only admin
    if membership.role == 'admin':
        admin_count = TeamMember.query.filter_by(team_id=team_id, role='admin').count()
        if admin_count == 1:
            flash('You cannot leave as you are the only admin! Transfer admin role first.', 'danger')
            return redirect(url_for('team_dashboard', team_id=team_id))
    
    team_name = team.name
    db.session.delete(membership)
    
    # Log activity
    log_team_activity(team_id, current_user.id, 'left_team', f'Left team "{team_name}"')
    
    flash(f'You have left team "{team_name}"!', 'success')
    return redirect(url_for('teams'))

@app.route('/teams/<int:team_id>/members/add', methods=['POST'])
@login_required
def add_team_member(team_id):
    """Add a member to team (admin only)"""
    team = Team.query.get_or_404(team_id)
    
    # Check if current user is admin
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not membership or membership.role != 'admin':
        flash('Only team admins can add members!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    email = request.form.get('email')
    user_to_add = User.query.filter_by(email=email).first()
    
    if not user_to_add:
        flash('User not found!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    # Check if already a member
    existing = TeamMember.query.filter_by(team_id=team_id, user_id=user_to_add.id).first()
    if existing:
        flash('User is already a member!', 'warning')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    role = request.form.get('role', 'member')
    new_member = TeamMember(team_id=team_id, user_id=user_to_add.id, role=role)
    db.session.add(new_member)
    
    # Log activity
    log_team_activity(team_id, current_user.id, 'added_member', 
                    f'Added {user_to_add.username} as {role}', 'member', user_to_add.id)
    
    flash(f'{user_to_add.username} added to team!', 'success')
    return redirect(url_for('team_dashboard', team_id=team_id))

@app.route('/teams/<int:team_id>/members/<int:member_id>/remove', methods=['POST'])
@login_required
def remove_team_member(team_id, member_id):
    """Remove a member from team (admin only)"""
    team = Team.query.get_or_404(team_id)
    
    # Check if current user is admin
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not membership or membership.role != 'admin':
        flash('Only team admins can remove members!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    member_to_remove = TeamMember.query.get_or_404(member_id)
    
    if member_to_remove.team_id != team_id:
        flash('Member not in this team!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    if member_to_remove.user_id == current_user.id:
        flash('You cannot remove yourself!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    removed_user = member_to_remove.user.username
    db.session.delete(member_to_remove)
    
    # Log activity
    log_team_activity(team_id, current_user.id, 'removed_member', f'Removed {removed_user}')
    
    flash(f'{removed_user} removed from team!', 'success')
    return redirect(url_for('team_dashboard', team_id=team_id))

@app.route('/teams/<int:team_id>/members/<int:member_id>/promote', methods=['POST'])
@login_required
def promote_team_member(team_id, member_id):
    """Promote a member to admin (admin only)"""
    team = Team.query.get_or_404(team_id)
    
    # Check if current user is admin
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not membership or membership.role != 'admin':
        flash('Only team admins can promote members!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    member_to_promote = TeamMember.query.get_or_404(member_id)
    
    if member_to_promote.team_id != team_id:
        flash('Member not in this team!', 'danger')
        return redirect(url_for('team_dashboard', team_id=team_id))
    
    member_to_promote.role = 'admin'
    
    # Log activity
    log_team_activity(team_id, current_user.id, 'promoted_member', 
                    f'Promoted {member_to_promote.user.username} to admin')
    
    flash(f'{member_to_promote.user.username} promoted to admin!', 'success')
    return redirect(url_for('team_dashboard', team_id=team_id))

# ==================== PLACEMENT ROUTES ====================

@app.route('/placements')
@login_required
def placements():
    """List all placement opportunities"""
    status = request.args.get('status')
    if status:
        placements_list = Placement.query.filter_by(status=status).order_by(Placement.created_at.desc()).all()
    else:
        placements_list = Placement.query.order_by(Placement.created_at.desc()).all()
    
    # Get student's applications
    my_applications = []
    if current_user.role == 'student':
        my_applications = PlacementApplication.query.filter_by(student_id=current_user.id).all()
    
    return render_template('placements.html', placements=placements_list, my_applications=my_applications)

@app.route('/placements/new', methods=['GET', 'POST'])
@login_required
def new_placement():
    """Add new placement opportunity (faculty/admin only)"""
    allowed_roles = ['faculty', 'hod', 'dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to add placements.', 'danger')
        return redirect(url_for('placements'))
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        description = request.form.get('description')
        package = request.form.get('package')
        location = request.form.get('location')
        eligibility = request.form.get('eligibility')
        last_date_str = request.form.get('last_date')
        status = request.form.get('status', 'upcoming')
        
        last_date = None
        if last_date_str:
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        
        placement = Placement(
            company_name=company_name,
            description=description,
            package=package,
            location=location,
            eligibility=eligibility,
            last_date=last_date,
            status=status,
            created_by=current_user.id
        )
        db.session.add(placement)
        db.session.commit()
        
        flash('Placement opportunity added successfully!', 'success')
        return redirect(url_for('placements'))
    
    return render_template('new_placement.html')

@app.route('/placements/<int:placement_id>/apply', methods=['POST'])
@login_required
def apply_placement(placement_id):
    """Apply for a placement (students only)"""
    if current_user.role != 'student':
        flash('Only students can apply for placements.', 'danger')
        return redirect(url_for('placements'))
    
    placement = Placement.query.get_or_404(placement_id)
    
    # Check if already applied
    existing = PlacementApplication.query.filter_by(
        placement_id=placement_id, 
        student_id=current_user.id
    ).first()
    
    if existing:
        flash('You have already applied for this placement!', 'warning')
        return redirect(url_for('placements'))
    
    application = PlacementApplication(
        placement_id=placement_id,
        student_id=current_user.id,
        status='applied'
    )
    db.session.add(application)
    db.session.commit()
    
    flash(f'Applied for {placement.company_name} successfully!', 'success')
    return redirect(url_for('placements'))

@app.route('/placements/<int:placement_id>/applications')
@login_required
def placement_applications(placement_id):
    """View applications for a placement (faculty/admin only)"""
    allowed_roles = ['faculty', 'hod', 'dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to view applications.', 'danger')
        return redirect(url_for('placements'))
    
    placement = Placement.query.get_or_404(placement_id)
    applications = PlacementApplication.query.filter_by(placement_id=placement_id).all()
    
    return render_template('placement_applications.html', placement=placement, applications=applications)

@app.route('/placements/<int:placement_id>/applications/<int:app_id>/update', methods=['POST'])
@login_required
def update_application(placement_id, app_id):
    """Update application status (faculty/admin only)"""
    allowed_roles = ['faculty', 'hod', 'dean', 'principal', 'admin']
    if current_user.role not in allowed_roles:
        flash('You do not have permission to update applications.', 'danger')
        return redirect(url_for('placements'))
    
    application = PlacementApplication.query.get_or_404(app_id)
    new_status = request.form.get('status')
    
    application.status = new_status
    db.session.commit()
    
    flash(f'Application status updated to {new_status}!', 'success')
    return redirect(url_for('placement_applications', placement_id=placement_id))

# ==================== REST API ====================

def check_api_role(required_roles):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    if current_user.role not in required_roles:
        return jsonify({'error': 'Insufficient permissions'}), 403
    return None

@app.route('/api/users', methods=['GET'])
@login_required
def api_get_users():
    perm = check_api_role(['admin'])
    if perm:
        return perm
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat()
    } for u in users])

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def api_get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    })

@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
@login_required
def api_update_user_role(user_id):
    perm = check_api_role(['admin'])
    if perm:
        return perm
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'role' in data:
        valid_roles = ['student', 'faculty', 'hod', 'dean', 'principal', 'admin']
        if data['role'] in valid_roles:
            user.role = data['role']
            db.session.commit()
            return jsonify({'message': 'Role updated successfully', 'new_role': user.role})
        return jsonify({'error': 'Invalid role'}), 400
    
    return jsonify({'error': 'No role provided'}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def api_delete_user(user_id):
    perm = check_api_role(['admin'])
    if perm:
        return perm
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'User {username} deleted successfully'})

@app.route('/api/notices', methods=['GET'])
@login_required
def api_get_notices():
    category = request.args.get('category')
    if category:
        notices = Notice.query.filter_by(category=category).order_by(Notice.created_at.desc()).all()
    else:
        notices = Notice.query.order_by(Notice.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'content': n.content,
        'category': n.category,
        'posted_by': n.user.username if n.user else None,
        'created_at': n.created_at.isoformat()
    } for n in notices])

@app.route('/api/notices', methods=['POST'])
@login_required
def api_create_notice():
    perm = check_api_role(['faculty', 'hod', 'dean', 'principal', 'admin'])
    if perm:
        return perm
    
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400
    
    notice = Notice(
        title=data['title'],
        content=data['content'],
        category=data.get('category', 'general'),
        posted_by=current_user.id
    )
    db.session.add(notice)
    db.session.commit()
    
    return jsonify({'message': 'Notice created successfully', 'id': notice.id}), 201

@app.route('/api/events', methods=['GET'])
@login_required
def api_get_events():
    upcoming = request.args.get('upcoming')
    now = datetime.now(timezone.utc)
    
    if upcoming:
        events = Event.query.filter(Event.date >= now).order_by(Event.date).all()
    else:
        events = Event.query.order_by(Event.date.desc()).all()
    
    return jsonify([{
        'id': e.id,
        'title': e.title,
        'description': e.description,
        'date': e.date.isoformat(),
        'location': e.location,
        'organized_by': e.user.username if e.user else None
    } for e in events])

@app.route('/api/events', methods=['POST'])
@login_required
def api_create_event():
    perm = check_api_role(['faculty', 'hod', 'dean', 'principal', 'admin'])
    if perm:
        return perm
    
    data = request.get_json()
    if not data or not data.get('title') or not data.get('description') or not data.get('date'):
        return jsonify({'error': 'Title, description, and date are required'}), 400
    
    try:
        event_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
    except:
        return jsonify({'error': 'Invalid date format'}), 400
    
    event = Event(
        title=data['title'],
        description=data['description'],
        date=event_date,
        location=data.get('location', ''),
        organized_by=current_user.id
    )
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'message': 'Event created successfully', 'id': event.id}), 201

@app.route('/api/clubs', methods=['GET'])
@login_required
def api_get_clubs():
    clubs = Club.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'created_by': c.user.username if c.user else None,
        'created_at': c.created_at.isoformat()
    } for c in clubs])

@app.route('/api/clubs', methods=['POST'])
@login_required
def api_create_club():
    perm = check_api_role(['dean', 'principal', 'admin'])
    if perm:
        return perm
    
    data = request.get_json()
    if not data or not data.get('name') or not data.get('description'):
        return jsonify({'error': 'Name and description are required'}), 400
    
    club = Club(
        name=data['name'],
        description=data['description'],
        created_by=current_user.id
    )
    db.session.add(club)
    db.session.commit()
    
    return jsonify({'message': 'Club created successfully', 'id': club.id}), 201

@app.route('/api/issues', methods=['GET'])
@login_required
def api_get_issues():
    issues = Issue.query.order_by(Issue.created_at.desc()).all()
    return jsonify([{
        'id': i.id,
        'title': i.title,
        'description': i.description,
        'category': i.category,
        'status': i.status,
        'reported_by': i.user.username if i.user else None,
        'created_at': i.created_at.isoformat()
    } for i in issues])

@app.route('/api/issues', methods=['POST'])
@login_required
def api_create_issue():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('description'):
        return jsonify({'error': 'Title and description are required'}), 400
    
    issue = Issue(
        title=data['title'],
        description=data['description'],
        category=data.get('category', 'other'),
        reported_by=current_user.id
    )
    db.session.add(issue)
    db.session.commit()
    
    return jsonify({'message': 'Issue reported successfully', 'id': issue.id}), 201

@app.route('/api/issues/<int:issue_id>/resolve', methods=['PUT'])
@login_required
def api_resolve_issue(issue_id):
    perm = check_api_role(['hod', 'dean', 'principal', 'admin'])
    if perm:
        return perm
    
    issue = Issue.query.get_or_404(issue_id)
    issue.status = 'resolved'
    db.session.commit()
    
    return jsonify({'message': 'Issue resolved successfully'})

@app.route('/api/share', methods=['GET'])
@login_required
def api_get_shares():
    my_shares = AccessShare.query.filter_by(owner_id=current_user.id).all()
    shared_with_me = AccessShare.query.filter_by(shared_with_id=current_user.id).all()
    
    return jsonify({
        'shared_by_me': [{
            'id': s.id,
            'user': s.shared_with.username,
            'email': s.shared_with.email,
            'access_level': s.access_level,
            'created_at': s.created_at.isoformat()
        } for s in my_shares],
        'shared_with_me': [{
            'id': s.id,
            'owner': s.owner.username,
            'email': s.owner.email,
            'access_level': s.access_level,
            'created_at': s.created_at.isoformat()
        } for s in shared_with_me]
    })

@app.route('/api/share', methods=['POST'])
@login_required
def api_create_share():
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    user_to_share = User.query.filter_by(email=data['email']).first()
    if not user_to_share:
        return jsonify({'error': 'User not found'}), 404
    
    access_level = data.get('access_level', 'view')
    
    existing = AccessShare.query.filter_by(
        owner_id=current_user.id, 
        shared_with_id=user_to_share.id
    ).first()
    
    if existing:
        existing.access_level = access_level
    else:
        share = AccessShare(
            owner_id=current_user.id,
            shared_with_id=user_to_share.id,
            access_level=access_level
        )
        db.session.add(share)
    
    db.session.commit()
    return jsonify({'message': f'Access shared with {user_to_share.username}'}), 201

@app.route('/api/share/<int:share_id>', methods=['DELETE'])
@login_required
def api_delete_share(share_id):
    share = AccessShare.query.get_or_404(share_id)
    
    if share.owner_id != current_user.id and share.shared_with_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    db.session.delete(share)
    db.session.commit()
    
    return jsonify({'message': 'Share deleted successfully'})

@app.route('/api/roles', methods=['GET'])
@login_required
def api_get_roles():
    roles = {
        'student': {'view_notices': True, 'post_notices': False, 'view_events': True, 'create_events': False, 'view_clubs': True, 'create_clubs': False, 'report_issues': True, 'resolve_issues': False, 'manage_users': False},
        'faculty': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': False, 'report_issues': True, 'resolve_issues': False, 'manage_users': False},
        'hod': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': False, 'report_issues': True, 'resolve_issues': True, 'manage_users': False},
        'dean': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': True, 'report_issues': True, 'resolve_issues': True, 'manage_users': False},
        'principal': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': True, 'report_issues': True, 'resolve_issues': True, 'manage_users': False},
        'admin': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': True, 'report_issues': True, 'resolve_issues': True, 'manage_users': True}
    }
    return jsonify(roles)

@app.route('/api/my-role', methods=['GET'])
@login_required
def api_my_role():
    role_perms = {
        'student': {'view_notices': True, 'post_notices': False, 'view_events': True, 'create_events': False, 'view_clubs': True, 'create_clubs': False, 'report_issues': True, 'resolve_issues': False, 'manage_users': False},
        'faculty': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': False, 'report_issues': True, 'resolve_issues': False, 'manage_users': False},
        'hod': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': False, 'report_issues': True, 'resolve_issues': True, 'manage_users': False},
        'dean': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': True, 'report_issues': True, 'resolve_issues': True, 'manage_users': False},
        'principal': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': True, 'report_issues': True, 'resolve_issues': True, 'manage_users': False},
        'admin': {'view_notices': True, 'post_notices': True, 'view_events': True, 'create_events': True, 'view_clubs': True, 'create_clubs': True, 'report_issues': True, 'resolve_issues': True, 'manage_users': True}
    }
    
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'permissions': role_perms.get(current_user.role, {})
    })

# ==================== OTP VERIFICATION ROUTES ====================

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP for email verification"""
    if request.method == 'POST':
        otp_entered = request.form.get('otp')
        email = session.get('pending_verification_email')
        
        if not email:
            flash('Session expired. Please register again.', 'danger')
            return redirect(url_for('register'))
        
        # Find valid OTP for this email
        otp_record = OTP.query.filter_by(email=email, otp_code=otp_entered).first()
        
        if not otp_record:
            flash('Invalid OTP. Please try again.', 'danger')
            return render_template('verify_otp.html', email=email)
        
        # Check if OTP is expired
        if otp_record.expires_at < datetime.now(timezone.utc):
            flash('OTP has expired. Please request a new one.', 'danger')
            return render_template('verify_otp.html', email=email)
        
        # Mark as verified
        otp_record.is_verified = True
        db.session.commit()
        
        # Clear session
        session.pop('pending_verification_email', None)
        
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('login'))
    
    # GET request - show OTP form
    email = session.get('pending_verification_email')
    if not email:
        flash('No pending verification. Please register.', 'warning')
        return redirect(url_for('register'))
    
    return render_template('verify_otp.html', email=email)

@app.route('/resend_otp')
def resend_otp():
    """Resend OTP for email verification"""
    email = session.get('pending_verification_email')
    
    if not email:
        flash('Session expired. Please register again.', 'danger')
        return redirect(url_for('register'))
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    # Delete old OTPs for this email
    OTP.query.filter_by(email=email).delete()
    
    # Create new OTP
    new_otp = OTP(email=email, otp_code=otp_code, expires_at=expires_at)
    db.session.add(new_otp)
    db.session.commit()
    
    # Send OTP (simulated)
    send_otp_email(email, otp_code)
    
    flash(f'New OTP sent to {email}. Check the server console!', 'info')
    return redirect(url_for('verify_otp'))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def error_404(error):
    return render_template('error.html', error='404 - Page Not Found'), 404

@app.errorhandler(500)
def error_500(error):
    return render_template('error.html', error='500 - Internal Server Error'), 500

# ==================== MAIN ====================

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(email='admin@campus.edu').first():
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin',
                email='admin@campus.edu',
                password=admin_password,
                role='admin'
            )
            db.session.add(admin)
            
            # Create HOD accounts
            hod_password = bcrypt.generate_password_hash('hod123').decode('utf-8')
            hod = User(
                username='hod',
                email='hod@campus.edu',
                password=hod_password,
                role='hod'
            )
            db.session.add(hod)
            
            # Create Dean account
            dean_password = bcrypt.generate_password_hash('dean123').decode('utf-8')
            dean = User(
                username='dean',
                email='dean@campus.edu',
                password=dean_password,
                role='dean'
            )
            db.session.add(dean)
            
            sample_notice = Notice(
                title='Welcome to CampusConnect+',
                content='This is the official college communication platform.',
                category='general',
                posted_by=1
            )
            db.session.add(sample_notice)
            
            sample_event = Event(
                title='Tech Fest 2024',
                description='Annual technical festival.',
                date=datetime(2024, 12, 15, 10, 0),
                location='Main Auditorium',
                organized_by=1
            )
            db.session.add(sample_event)
            
            sample_club = Club(
                name='Coding Club',
                description='Learn programming and build projects.',
                created_by=1
            )
            db.session.add(sample_club)
            
            db.session.commit()
            print("Database initialized with sample data!")
    
    local_ip = get_local_ip()
    print("\n" + "="*50)
    print("CampusConnect+ is running!")
    print("="*50)
    print(f"\nNetwork access: http://{local_ip}:5000")
    print("\nShare this URL with others on your network!")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

