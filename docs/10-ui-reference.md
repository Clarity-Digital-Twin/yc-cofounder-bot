UI Reference

## Streamlit Dashboard Components

### User Profile Section
- **Purpose**: One-time setup of YOUR profile (loaded from CURRENT_COFOUNDER_PROFILE.MD)
- **Fields**:
  - Name, location, background
  - Technical skills and expertise
  - Vision and interests
  - What you bring to a partnership
- **Actions**: Save profile, Load from file

### Match Criteria Builder
- **Purpose**: Define your ideal cofounder
- **Fields**:
  - Required skills (e.g., "full-stack", "React", "ML")
  - Domain interests (e.g., "healthcare", "fintech")
  - Location preferences
  - Experience level
  - Availability timeline
- **Match Threshold**: Slider 0-100% (default 80%)

### Message Template Editor
- **Purpose**: Customize outreach messages (loaded from MATCH_MESSAGE_TEMPLATE.MD)
- **Placeholders**:
  - {candidate_name} - Their name
  - {common_interests} - Shared interests
  - {why_match} - Reason for reaching out
  - {your_name} - Your name
- **Preview**: Live preview with sample data

### Control Panel
- **Start Button**: Launch CUA autonomous browsing
- **Stop Button**: Emergency abort (creates .runs/stop.flag)
- **Status Indicators**:
  - CUA status (idle/running/stopped)
  - Profiles processed counter
  - Messages sent counter
  - Remaining quota
- **Settings**:
  - Session quota (default 10)
  - Rate limit delay (5-10s)
  - Screenshot saving (on/off)

### Live Event Log
- **Purpose**: Real-time monitoring of CUA actions
- **Events Shown**:
  - Navigation actions ("Opening YC site", "Clicking View Profile")
  - Profile evaluations ("Evaluating: John Doe")
  - Match decisions ("MATCH: 85% - Sending invite")
  - Errors and retries
- **Format**: Timestamp | Event Type | Details

### Results Table
- **Columns**:
  - Profile Name
  - Match Score (0-100%)
  - Decision (Match/Pass)
  - Rationale
  - Message Status (Sent/Skipped)
- **Actions**:
  - View full profile
  - View/edit message
  - Manual override

## YC Site Elements (for CUA)

### Login Page
- **URL**: From WEBSITE_LINK.MD
- **Elements**: Email/password fields, login button
- **Screenshot**: initial_log_in.png

### Profile List Page
- **Elements**:
  - Profile cards with summary
  - "View profile" buttons
  - Pagination/infinite scroll
- **CUA Actions**: Scroll, click profiles

### Individual Profile Page
- **Screenshot**: view_profile_clicked.png
- **Main Content**:
  - About section
  - Background/experience
  - Skills and interests
  - What they're looking for
- **Message Panel**:
  - Text area for message
  - "Invite to connect" button
  - Character limit indicator

## CUA Automation Flow

1. **Initialize**:
   - Load user profile and criteria
   - Open browser via CUA
   - Navigate to YC site

2. **Browse Profiles**:
   - Take screenshot of list
   - Identify "View profile" buttons
   - Click each profile sequentially

3. **Evaluate Match**:
   - Screenshot profile page
   - Extract text via OCR/CUA
   - Compare against user criteria
   - Calculate match score

4. **Send Invites**:
   - If score > threshold
   - Fill message with template
   - Click "Invite to connect"
   - Log result

5. **Continue Until**:
   - Quota reached
   - Stop button pressed
   - No more profiles

## Configuration Files

### Assets Used
- `WEBSITE_LINK.MD` - Target YC URL
- `CURRENT_COFOUNDER_PROFILE.MD` - User's profile template
- `MATCH_MESSAGE_TEMPLATE.MD` - Outreach message template
- `.env` - API keys and settings

### Output Files
- `events.jsonl` - All CUA actions and decisions
- `.runs/seen.sqlite` - Deduplication database
- `.runs/quota.sqlite` - Usage tracking
- `screenshots/` - Saved screenshots (optional)

## Best Practices for CUA

### Reliable Selectors
- Use visible text when possible
- Fallback to aria-labels
- Avoid dynamic class names
- Handle loading states

### Error Handling
- Retry with exponential backoff
- Take screenshot on error
- Log detailed error context
- Graceful degradation

### Performance
- Cache profile evaluations
- Batch API calls when possible
- Optimize screenshot size
- Minimize token usage