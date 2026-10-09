
# Read the app.py file
with open('d:/New folder (2)/Campus Connect++/CampusConnect+/app.py', 'r') as f:
    content = f.read()

# REST API section to add
rest_api = '''

# ==================== REST API ====================
from flask import jsonify, request
from functools import wraps

# API Key authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        # For development, accept a simple key
        if api_key != 'campus-connect-api-key-2024':
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check role permissions for API
def check_api_role(required_roles):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    if current_user.role not in required_roles:
        return jsonify({'error': 'Insufficient permissions'}), 403
    return None

# ==================== USER API ====================

@app.route('/api/users', methods=['GET'])
@login_required
def api_get_users():
    """Get all users (Admin only)"""
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
    """Get specific user"""
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
    """Update user role (Admin only)"""
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
    """Delete user (Admin only)"""
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

# ==================== NOTICES API ====================

@app.route('/api/notices', methods=['GET'])
@login_required
def api_get_notices():
    """Get all notices"""
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
    """Create new notice (Faculty/HOD/Dean/Principal/Admin)"""
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

@app.route('/api/notices/<int:notice_id>', methods=['DELETE'])
@login_required
def api_delete_notice(notice_id):
    """Delete notice (Admin only)"""
    perm = check_api_role(['admin'])
    if perm:
        return perm
    
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    return jsonify({'message': 'Notice deleted successfully'})

# ==================== EVENTS API ====================

@app.route('/api/events', methods=['GET'])
@login_required
def api_get_events():
    """Get all events"""
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
    """Create new event (Faculty/HOD/Dean/Principal/Admin)"""
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

# ==================== CLUBS API ====================

@app.route('/api/clubs', methods=['GET'])
@login_required
def api_get_clubs():
    """Get all clubs"""
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
    """Create new club (Dean/Principal/Admin)"""
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

# ==================== ISSUES API ====================

@app.route('/api/issues', methods=['GET'])
@login_required
def api_get_issues():
    """Get all issues"""
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
    """Report new issue (All authenticated users)"""
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
    """Resolve issue (HOD/Dean/Principal/Admin)"""
    perm = check_api_role(['hod', 'dean', 'principal', 'admin'])
    if perm:
        return perm
    
    issue = Issue.query.get_or_404(issue_id)
    issue.status = 'resolved'
    db.session.commit()
    
    return jsonify({'message': 'Issue resolved successfully'})

# ==================== ROLE ACCESS API ====================

@app.route('/api/roles', methods=['GET'])
@login_required
def api_get_roles():
    """Get all available roles and their permissions"""
    roles = {
        'student': {
            'view_notices': True,
            'post_notices': False,
            'view_events': True,
            'create_events': False,
            'view_clubs': True,
            'create_clubs': False,
            'report_issues': True,
            'resolve_issues': False,
            'manage_users': False
        },
        'faculty': {
            'view_notices': True,
            'post_notices': True,
            'view_events': True,
            'create_events': True,
            'view_clubs': True,
            'create_clubs': False,
            'report_issues': True,
            'resolve_issues': False,
            'manage_users': False
        },
        'hod': {
            'view_notices': True,
            'post_notices': True,
            'view_events': True,
            'create_events': True,
            'view_clubs': True,
            'create_clubs': False,
            'report_issues': True,
            'resolve_issues': True,
            'manage_users': False
        },
        'dean': {
            'view_notices': True,
            'post_notices': True,
            'view_events': True,
            'create_events': True,
            'view_clubs': True,
            'create_clubs': True,
            'report_issues': True,
            'resolve_issues': True,
            'manage_users': False
        },
        'principal': {
            'view_notices': True,
            'post_notices': True,
            'view_events': True,
            'create_events': True,
            'view_clubs': True,
            'create_clubs': True,
            'report_issues': True,
            'resolve_issues': True,
            'manage_users': False
        },
        'admin': {
            'view_notices': True,
            'post_notices': True,
            'view_events': True,
            'create_events': True,
            'view_clubs': True,
            'create_clubs': True,
            'report_issues': True,
            'resolve_issues': True,
            'manage_users': True
        }
    }
    return jsonify(roles)

@app.route('/api/my-role', methods=['GET'])
@login_required
def api_my_role():
    """Get current user's role and permissions"""
    role_perms = {
        'student': {
            'view_notices': True, 'post_notices': False, 'view_events': True,
            'create_events': False, 'view_clubs': True, 'create_clubs': False,
            'report_issues': True, 'resolve_issues': False, 'manage_users': False
        },
        'faculty': {
            'view_notices': True, 'post_notices': True, 'view_events': True,
            'create_events': True, 'view_clubs': True, 'create_clubs': False,
            'report_issues': True, 'resolve_issues': False, 'manage_users': False
        },
        'hod': {
            'view_notices': True, 'post_notices': True, 'view_events': True,
            'create_events': True, 'view_clubs': True, 'create_clubs': False,
            'report_issues': True, 'resolve_issues': True, 'manage_users': False
        },
        'dean': {
            'view_notices': True, 'post_notices': True, 'view_events': True,
            'create_events': True, 'view_clubs': True, 'create_clubs': True,
            'report_issues': True, 'resolve_issues': True, 'manage_users': False
        },
        'principal': {
            'view_notices': True, 'post_notices': True, 'view_events': True,
            'create_events': True, 'view_clubs': True, 'create_clubs': True,
            'report_issues': True, 'resolve_issues': True, 'manage_users': False
        },
        'admin': {
            'view_notices': True, 'post_notices': True, 'view_events': True,
            'create_events': True, 'view_clubs': True, 'create_clubs': True,
            'report_issues': True, 'resolve_issues': True, 'manage_users': True
        }
    }
    
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'permissions': role_perms.get(current_user.role, {})
    })

# ==================== END REST API ====================
'''

# Insert before ERROR HANDLERS
content = content.replace('# ==================== ERROR HANDLERS ====================', rest_api + '\n# ==================== ERROR HANDLERS ====================')

# Write back
with open('d:/New folder (2)/Campus Connect++/CampusConnect+/app.py', 'w') as f:
    f.write(content)

print('REST API endpoints added successfully!')

