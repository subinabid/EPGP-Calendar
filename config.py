"""Configuration for IIMKCal"""

import os

################################################################################
# Configuration
################################################################################

DOMAIN = "subinabid.pythonanywhere.com"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
VALID_CALENDARS = [f"epgp17{suffix}" for suffix in "abcdef"]
VALID_TERMS = [f"q{num}" for num in range(1, 8)]  # q1, q2, ..., q7
ELECTIVE_TERMS = [f"q{num}" for num in range(5, 8)]  # q5, q6, q7
