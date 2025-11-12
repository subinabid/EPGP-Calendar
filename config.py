"""Configuration for IIMKCal"""

import os

################################################################################
# Configuration
################################################################################

DOMAIN = "subinabid.pythonanywhere.com"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CALENDAR_SUFFIX = ["a", "a1", "a2", "b", "c", "d", "e", "f"]
VALID_CALENDARS = [f"epgp17{suffix}" for suffix in CALENDAR_SUFFIX]
VALID_TERMS = [f"q{num}" for num in range(1, 8)]  # q1, q2, ..., q7
ELECTIVE_TERMS = [f"q{num}" for num in range(5, 8)]  # q5, q6, q7
