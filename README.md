# LinkedIn Content Cleaner

A collection of Python scripts that use Selenium to automatically clean up your LinkedIn activity by deleting posts, comments, and removing reactions/likes.

## Scripts Overview

### 1. Posts Deleter (`posts.py`)
Automatically deletes LinkedIn posts from your recent activity page while preserving posts made to community groups.

### 2. Comments Deleter (`comments.py`)
Automatically deletes your LinkedIn comments from your recent activity (comments) page.

### 3. Reactions Deleter (`reactions.py`)
Automatically removes likes/reactions from your LinkedIn posts and comments.

## Features

### Posts Deleter
- Deletes regular posts by clicking the "..." menu and selecting delete
- Preserves the first post (configurable)
- Page refresh every 50 deletions to clear old content
- Includes safety features and user confirmation

### Comments Deleter
- Deletes comments via the comment overflow menu ("...")
- Preserves the first comment (configurable)
- Page refresh every 50 deletions to clear old content
- Handles confirmation dialogs automatically

### Reactions Deleter
- Removes likes from both posts and comments
- Expands comment sections to find liked comments
- Loads more comments and replies automatically
- Page refresh every 50 unlikes to clear old content
- Prevents re-liking issue by verifying `aria-pressed="true"`

## Installation

1. Install Python 3.7 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install ChromeDriver:
   - **Option 1 (Recommended)**: Install via webdriver-manager (automatic)
   - **Option 2**: Download manually from [ChromeDriver downloads](https://chromedriver.chromium.org/downloads) and add to PATH

## Usage

### Posts Deleter
```bash
python posts.py
```

### Comments Deleter
```bash
python comments.py
```

### Reactions Deleter
```bash
python reactions.py
```

## How to Use

1. Run any of the scripts
2. Follow the prompts:
   - Enter LinkedIn URL (each script has sensible defaults)
   - Set maximum number of items to process (optional)
   - Choose headless mode (optional)
   - Set initial scroll rounds to load more content (optional)

3. The script will open Chrome and navigate to LinkedIn
4. Log in to LinkedIn manually if needed
5. Press Enter when ready to start processing
6. The script will process items automatically

## Default URLs

- **Posts**: `https://www.linkedin.com/in/[username]/recent-activity/all/`
- **Comments**: `https://www.linkedin.com/in/[username]/recent-activity/comments/`
- **Reactions**: `https://www.linkedin.com/in/[username]/recent-activity/`

## Key Features

### Cross-Platform Compatibility
- Works on Mac, Windows, and Linux
- Uses standard Python libraries and Selenium
- Chrome WebDriver automatically detects the OS

### Error Handling
- Detects LinkedIn error pages and automatically refreshes
- Handles empty pages (likely due to LinkedIn errors)
- Robust retry mechanisms
- Comprehensive logging

### Safety Features
- Preserves first post/comment (configurable)
- Rate limiting protection with delays between actions
- Page refresh every 50 operations to clear stale content
- Detailed logging of all actions
- User confirmation before starting

### Smart Content Loading
- Initial aggressive scrolling to load more content
- Automatically clicks "Show previous comments" buttons
- Expands comment sections to reveal liked comments
- Loads more replies and previous content

## Important Notes

- **Always review content before running**: The scripts will delete content, so make sure you want to delete it
- **Rate limiting**: The scripts include delays to avoid being blocked by LinkedIn
- **Manual login required**: You'll need to log in to LinkedIn manually when the browser opens
- **First item preservation**: Each script preserves the first item by default (you can configure/remove this pretty easily) (posts/comments)

## Troubleshooting

- **ChromeDriver issues**: Make sure ChromeDriver is installed and matches your Chrome version
- **Element not found**: LinkedIn's interface may have changed; the scripts include multiple selectors for robustness
- **Rate limiting**: If you get blocked, wait a while before running the scripts again
- **LinkedIn error pages**: The scripts automatically detect and refresh when LinkedIn shows error pages

## File Structure

```
linkinreset/
├── posts.py          # Posts deleter script
├── comments.py       # Comments deleter script
├── reactions.py      # Reactions deleter script
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver
- Selenium
- See `requirements.txt` for full list

## Disclaimer

These scripts are for personal use only. Use responsibly and in accordance with LinkedIn's Terms of Service. The authors are not responsible for any issues that may arise from using these scripts.
