"""IIMK EPGP Calender App

The app get session details form a google sheet and renders an ics
The google sheet is expected to have the following columns

Sec - Section detail - A to F
Code - Format: EPGP-203
Course Name - Format: Economic Environment (EE)
Session - Serial Number - 1 , 2, 3, etc. Quiz sessions will be 11, 12, 13 etc.
Date - Format: 08-Mar-25
Time - Format: 9:00 AM to 11:45 AM in IST
"""

import os
from flask import Flask, Response, render_template, abort
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz  # type: ignore
import csv
import requests  # type: ignore

app = Flask(__name__)
load_dotenv()

################################################################################
# Configuration
################################################################################

DOMAIN = "subinabid.pythonanywhere.com"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
VALID_CALENDARS = [f"epgp17{suffix}" for suffix in "abcdef"]

################################################################################
# Helper Functions
################################################################################


def handle_events(csv_url):
    """Handle events from the CSV URL"""

    # Fetch the CSV content
    response = requests.get(csv_url)
    response.raise_for_status()

    # Parse CSV rows
    reader = csv.DictReader(response.text.splitlines())
    events = []

    for row in reader:
        try:
            # Handle buffers and holidays
            if row["Code"] == "" or row["Session"] == "":
                # print(f"Code or Session Error: Skipping Empty row: {row}")
                continue

            # Extract and convert fields
            event_date = row.get("Date", "").strip()
            event_time = row.get("Time", "").strip()

            # Split the time range
            start_str, end_str = [t.strip() for t in event_time.split("to")]

            # Combine with date and parse as IST datetime
            try:
                start_ist = datetime.strptime(
                    f"{event_date} {start_str}", "%d-%b-%y %I:%M %p"
                )
            except ValueError:
                # If the first format fails, try the second format
                # This is a fallback in case the date format is different
                start_ist = datetime.strptime(
                    f"{event_date} {start_str}", "%d-%B-%y %I:%M %p"
                )

            try:
                end_ist = datetime.strptime(
                    f"{event_date} {end_str}", "%d-%b-%y %I:%M %p"
                )
            except ValueError:
                end_ist = datetime.strptime(
                    f"{event_date} {end_str}", "%d-%B-%y %I:%M %p"
                )

            # Convert IST to UTC (subtract 5 hours 30 minutes)
            start_utc = start_ist - timedelta(hours=5, minutes=30)
            end_utc = end_ist - timedelta(hours=5, minutes=30)

            # Format for ICS (UTC time, Z suffix)
            dtstart = start_utc.strftime("%Y%m%dT%H%M%SZ")
            dtend = end_utc.strftime("%Y%m%dT%H%M%SZ")

            event = {
                "id": f"{row['Code'].strip()}-{row['Sec']}-{row['Session'].strip()}@iimcal.sabid.in",
                "title": row["Course Name"].strip(),
                "description": row.get("Course Name", "").strip(),
                "location": "Online",
                "start": dtstart,
                "end": dtend,
            }

            events.append(event)

        except Exception as e:
            # Optionally log or skip invalid rows
            print(f"Skipping invalid row: {row}\nReason: {e}")

    return events


def get_classes(tab_name):
    """Get session details from the google sheet"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name.upper()}"

    return handle_events(csv_url)


def get_exams():
    """Get exam details from the google sheet"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=EXAMS"

    return handle_events(csv_url)


def format_ics_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str)
    return dt.astimezone(pytz.UTC).strftime("%Y%m%dT%H%M%SZ")


def generate_ics(calendar_id, events):
    """Generate ICS data for a given calendar and events"""
    ics = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        f"PRODID:-//IIMCal//{calendar_id.upper()} Calendar//EN",
    ]

    for event in events:
        ics.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event['id']}@iimcal.sabid.in",
                f"DTSTAMP:{format_ics_datetime(datetime.utcnow().isoformat())}",
                f"DTSTART:{format_ics_datetime(event['start'])}",
                f"DTEND:{format_ics_datetime(event['end'])}",
                f"SUMMARY:{event['title']}",
                f"DESCRIPTION:{event['description']}",
                f"LOCATION:{event['location']}",
                "END:VEVENT",
            ]
        )

    ics.append("END:VCALENDAR")
    return "\r\n".join(ics)


################################################################################
# Routes
################################################################################


@app.route("/")
def home():
    """Home Page"""
    sections = VALID_CALENDARS  # ['epgp17a', 'epgp17b', ...]
    return render_template("index.html", sections=sections, domain=DOMAIN)


@app.route("/<calendar_id>.ics")
def serve_calendar(calendar_id):
    """Serve Section Calendars as ICS"""
    if calendar_id not in VALID_CALENDARS:
        abort(404, description="Calendar not found")

    events = get_classes(calendar_id)
    exams = get_exams()
    events.extend(exams)
    ics_data = generate_ics(calendar_id, events)

    return Response(
        ics_data,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={calendar_id}.ics"},
    )


@app.route("/test")
def test():
    """Test Page"""
    tab_name = "EPGP17B"
    events = get_classes(tab_name)
    exams = get_exams()
    events.extend(exams)
    return events


################################################################################
# Entry Point
################################################################################

if __name__ == "__main__":
    app.run(debug=True)
