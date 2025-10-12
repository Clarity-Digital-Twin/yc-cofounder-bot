# Personal Files Directory

This directory is for storing personal and private information that you want to use during development but don't want committed to the public repository.

## What Goes Here

Store any personal files needed for testing and development:

- **YC Profile** - Your personal YC co-founder matching profile
- **Criteria Documents** - Your specific matching criteria
- **Message Templates** - Personalized message templates
- **Test Data** - Any personal test data you want to work with
- **Notes** - Personal development notes

## File Suggestions

```
personal/
├── README.md              (this file - tracked in git)
├── my-yc-profile.txt      (your personal profile - NOT tracked)
├── my-criteria.txt        (your criteria - NOT tracked)
├── my-message-template.txt (your template - NOT tracked)
└── notes.md               (your notes - NOT tracked)
```

## Privacy

All files in this directory (except this README.md) are automatically ignored by git and will never be committed to the repository. This keeps your personal information private while allowing you to work with real data during development.

## Usage in Code

Reference these files when testing the bot:

```python
# Example: Load your personal profile
with open("personal/my-yc-profile.txt") as f:
    my_profile = f.read()
```

Or use them directly in the Streamlit UI by copying and pasting the content.
