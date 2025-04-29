"""Tests for the app module."""

import os
import requests  # type: ignore
from app import VALID_CALENDARS
from dotenv import load_dotenv

load_dotenv()


# Test Env variables
def test_env_variables():
    """Test if environment variables are loaded correctly."""
    assert os.getenv("GOOGLE_SHEET_ID") is not None


# Test valid calendars
def test_valid_calendars():
    """Test if valid calendars are set correctly."""
    assert isinstance(VALID_CALENDARS, list)
    assert len(VALID_CALENDARS) == 6
    for calendar in VALID_CALENDARS:
        assert calendar.startswith("epgp17")
        assert len(calendar) == 7


# Test access to Google Sheet
def test_google_sheet_access():
    """Test if the Google Sheet is accessible."""
    google_sheet_id = os.getenv("GOOGLE_SHEET_ID")
    assert google_sheet_id is not None
    url = (
        f"https://docs.google.com/spreadsheets/d/{google_sheet_id}/gviz/tq?tqx=out:csv"
    )
    response = requests.get(url)
    assert response.status_code == 200
