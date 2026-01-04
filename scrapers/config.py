# Configuration for Quarex Candidate Scraper
# IMPORTANT: Add this file to .gitignore - contains credentials

# cPanel SSH/SFTP Settings (GoDaddy)
CPANEL_HOST = "quarex.org"
CPANEL_USERNAME = ""  # Fill in your GoDaddy cPanel username
CPANEL_PASSWORD = ""  # Fill in your GoDaddy cPanel password
CPANEL_PORT = 22

# Remote paths on cPanel
REMOTE_CANDIDATE_DIR = "/home/YOUR_CPANEL_USER/public_html/libraries/politician-libraries/"

# Local paths
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
LOCAL_CANDIDATE_DIR = os.path.join(PROJECT_DIR, "libraries", "politician-libraries")
LOCAL_BACKUP_DIR = os.path.join(BASE_DIR, "backups")
LOCAL_REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# Scraper settings
REQUEST_DELAY = 2  # Seconds between requests (be polite to Ballotpedia)
USER_AGENT = "Quarex Candidate Scraper (educational/civic project)"

# Email notifications (optional)
SEND_EMAIL_REPORTS = False
EMAIL_FROM = ""
EMAIL_TO = ""
SMTP_SERVER = ""
SMTP_PORT = 587
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
