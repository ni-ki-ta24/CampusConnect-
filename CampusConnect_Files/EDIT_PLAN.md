# Edit Plan: Add College Photo as Background of Dashboards

## Information Gathered:
1. **Project Structure:** Flask-based college communication platform with templates using Bootstrap 5
2. **College Info:** Stored in `COLLEGE_INFO` dictionary in `app.py` - includes name, tagline, departments, facilities, achievements
3. **Current college.html:** Has a hero section with a hardcoded Unsplash URL as background
4. **Dashboard Pages to Update:**
   - `index.html` - Home page (main dashboard)
   - `clubs.html` - Clubs listing
   - `profile.html` - User profile
   - `notices.html` - Notices listing
   - `events.html` - Events listing  
   - `issues.html` - Issues reporting
5. **CSS:** Located in `static/css/style.css`

## Plan:
### Step 1: Add college photo to COLLEGE_INFO in app.py
- Add a 'photo' key with a college image URL to the COLLEGE_INFO dictionary

### Step 2: Add dashboard background CSS in style.css
- Add new CSS class `.dashboard-bg` for college photo background
- Add `.dashboard-overlay` for text readability
- Add styles for dashboard containers

### Step 3: Update index.html (Home Dashboard)
- Add college photo as hero/background section
- Style the main content area with college background

### Step 4: Update clubs.html
- Add college photo background to the clubs page

### Step 5: Update profile.html
- Add college photo background to the profile page

### Step 6: Update other dashboard pages (notices, events, issues)
- Add college photo background where appropriate

## Dependent Files to Edit:
1. `app.py` - Add college photo URL
2. `static/css/style.css` - Add background styles
3. `templates/index.html` - Add background to home dashboard
4. `templates/clubs.html` - Add background to clubs page
5. `templates/profile.html` - Add background to profile page
6. `templates/notices.html` - Add background to notices page
7. `templates/events.html` - Add background to events page
8. `templates/issues.html` - Add background to issues page

## Followup Steps:
- Test that the application runs without errors
- Verify the college photo displays correctly on all dashboard pages
- Ensure text remains readable with the background image

