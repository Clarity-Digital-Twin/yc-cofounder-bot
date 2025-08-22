# YC Co-Founder Matching UI Structure

This document describes the UI elements of YC Startup School's co-founder matching platform for CUA automation.

## Dashboard Page

**URL**: `https://www.startupschool.org/cofounder-matching`

### Key Elements
- **View Profiles Button**: Central button to start browsing profiles
- **Queue Counter**: Shows "X founders in your queue meet your requirements!"
- **Sidebar Navigation**:
  - Dashboard
  - Discover Profiles
  - Revisit Profiles
  - Inbox
  - Read the YC Guide
  - Curriculum
  - My Account

### Filters Section
- Located on the right side
- Shows current filter criteria
- Has an "Edit" button to modify filters

## Profile View Page

### Layout
- **Back Button**: Top left navigation back to list
- **Save to Favorites**: Top right with star icon
- **Profile Header**:
  - Profile image (circular)
  - Name
  - Location (e.g., "San Francisco, CA, USA")
  - Last seen status

### Key Sections
1. **Quick Summary Box**:
   - Shows if they're technical/non-technical
   - Ready within X months
   - Can help with/explore areas
   - Willing to do (Engineering/Product)

2. **About Me Section**:
   - Introduction paragraph
   - Background details
   - Experience summary

3. **My Background Section**:
   - Impressive accomplishments
   - Education details
   - Work history

### Action Buttons
- **"Invite to connect" Button**: Green, prominent CTA
- **"Skip for now" Button**: Gray, secondary action
- **Invite Counter**: "You have X invites left for this week"

### Message Box
- Appears when clicking "Invite to connect"
- Placeholder text: "If you're excited about potentially working with this co-founder, type a short message here and click 'Invite.'"

## Important CSS Selectors/Identifiers for Automation

For CUA prompts, use these descriptions:
- "Click the 'View Profiles' button" - for starting profile browsing
- "Click the 'Invite to connect' green button" - for sending invites
- "Click 'Skip for now'" - to skip a profile
- "Click the message text area" - to focus message input
- "Click the Back button" - to return to profile list

## Notes for CUA Implementation

1. The platform limits invites to 20 per week
2. Profiles show "Last seen" status
3. Filter criteria are displayed and editable
4. Platform uses standard web technologies (no special frameworks detected)
5. Navigation is sidebar-based with clear labeling

## Privacy Note

This document contains only structural information. No personal profile data or identifying information has been retained.