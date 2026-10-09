# Team Collaboration Feature Plan

## Information Gathered:
1. **Current Models:** User, Notice, Event, Club, Issue, AccessShare
2. **Authentication:** Flask-Login with role-based access
3. **Share Feature:** Already exists - can share access with view/edit/full levels
4. **Templates:** Uses Bootstrap 5, Font Awesome

## Plan - Team Collaboration Features:

### Step 1: Add Team Models in app.py
- Create `Team` model - team name, description, created_by, created_at
- Create `TeamMember` model - team_id, user_id, role (admin/member), joined_at
- Create `TeamActivity` model - team_id, user_id, action, details, created_at

### Step 2: Add Team Routes in app.py
- `/teams` - List all teams / Create team
- `/teams/<team_id>` - View team dashboard
- `/teams/<team_id>/join` - Join a team
- `/teams/<team_id>/leave` - Leave a team
- `/teams/<team_id>/members` - Manage team members
- `/teams/<team_id>/activity` - View team activity feed

### Step 3: Create Team Templates
- `templates/teams.html` - List and create teams
- `templates/team_dashboard.html` - Team dashboard with activity feed

### Step 4: Update Profile Page
- Show user's teams in profile
- Show team activity in profile

### Step 5: Track Activities
- When notices/events/clubs/issues are created, log activity to team
- Show "Created by [username]" on content
- Show activity timeline in team dashboard

## Dependent Files to Edit:
1. `app.py` - Add Team models and routes
2. `templates/teams.html` - New team list page
3. `templates/team_dashboard.html` - New team dashboard
4. `templates/profile.html` - Add team info
5. `templates/base.html` - Add teams link in navigation

## Followup Steps:
- Test team creation and membership
- Verify activity tracking works
- Test that all team members can see changes

