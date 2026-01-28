"""Helper functions for IIMKCal"""

import pytz  # type: ignore
import csv
import requests  # type: ignore
from datetime import datetime, timedelta
from flask import abort
from config import GOOGLE_SHEET_ID, VALID_CALENDARS, VALID_TERMS, ELECTIVE_TERMS

################################################################################
# Validation Functions
################################################################################


def validate_calendar(calendar_id: str) -> None:
    """Validate the calendar ID"""
    if calendar_id not in VALID_CALENDARS:
        abort(404, description="Calendar not found")


def validate_term_course(term: str) -> bool:
    """Validate the term for courses"""
    return term.lower() in VALID_TERMS


def validate_term_elective(term: str) -> bool:
    """Validate if the term has electives"""
    return term.lower() in ELECTIVE_TERMS


def validate_term(term: str) -> None:
    """Validate the term"""
    if not validate_term_elective(term):
        abort(404, description="Term does not have electives")
    if not validate_term_course(term):
        abort(404, description="Invalid Term")


################################################################################
# Helper Functions
################################################################################


def get_csv(csv_url: str) -> csv.DictReader:
    """Fetch CSV content from a URL and return a DictReader"""
    # Fetch the CSV content
    response = requests.get(csv_url)
    response.raise_for_status()

    # Parse CSV rows and return
    return csv.DictReader(response.text.splitlines())


def get_classes(tab_name):
    """Get session details from the google sheet"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name.upper()}"

    return handle_events(csv_url, includeSessionCount=True)


def get_exams():
    """Get exam details from the google sheet"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=EXAMS"

    return handle_events(csv_url)


def get_general_events():
    """Get general events from the google sheet"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GENERAL"

    return handle_events(csv_url)


def handle_event_dict(
    events_list: list[dict], includeSessionCount=False, elective=False
) -> list[dict]:
    """Handle events from a list of event dicts

    Args:
        events_list: List of event dictionaries
    Returns:
        List of event dictionaries
    """
    events = []
    if events_list:
        for row in events_list:
            try:
                # Handle buffers and holidays
                if row["Code"] == "" or row["Session"] == "":
                    continue

                # Extract and convert fields
                event_date = row.get("Date", "").strip()
                event_time = row.get("Time", "").strip().replace(".", ":")

                # Split the time range
                if "to" in event_time:
                    # Assuming the time is in the format "9:00 AM to 11:45 AM"
                    start_str, end_str = [t.strip() for t in event_time.split("to")]
                elif "-" in event_time:
                    # Assuming the time is in the format "9:00 AM - 11:45 AM"
                    start_str, end_str = [t.strip() for t in event_time.split("-")]
                else:
                    print(f"Time format error: {event_time}")
                    print(f"Skipping row: {row} \nReason: Invalid time format")
                    continue

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
                # Get location info
                location = row.get("Location", "").strip()
                if not location:
                    location = "Online"

                # Include session count in the title if requested
                if includeSessionCount:
                    session_count = row.get("Session", "").strip()
                    if (
                        session_count
                        and session_count.isdigit()
                        and int(session_count)
                        < 30  # Sessions < 30 are regular sessions
                    ):
                        title = (
                            f"{row['Course Name'].strip()} - Session {session_count}"
                        )
                    else:
                        title = row["Course Name"].strip()
                else:
                    title = row["Course Name"].strip()

                # Create event dictionary

                if elective:
                    event_id = f"{row['Code'].strip()}-{row['Session'].strip()}"
                else:
                    event_id = (
                        f"{row['Code'].strip()}-{row['Sec']}-{row['Session'].strip()}"
                    )

                event = {
                    "id": f"{event_id}@iimcal.sabid.in",
                    "title": title,
                    "description": title,
                    "location": location,
                    "start": dtstart,
                    "end": dtend,
                }
                events.append(event)
            except Exception as e:
                # Optionally log or skip invalid rows
                print(f"Skipping invalid row: {row}\nReason: {e}")
    return events


def handle_events(csv_url, includeSessionCount=False) -> list[dict]:
    """Handle events from the CSV URL

    Args:
        csv_url: URL of the CSV to fetch
        includeSessionCount: Whether to include session count in the event title

    Returns:
        List of event dictionaries
    """

    # Fetch the parsed CSV content as dict
    reader = get_csv(csv_url)
    return handle_event_dict(list(reader), includeSessionCount)


################################################################################
# Electives specific Functions
################################################################################


def get_electives_list(term: str) -> dict:
    """Get elective details from the google sheet"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={term.upper()}"

    # Fetch the CSV content as a dict
    reader = get_csv(csv_url)
    sorted_reader = sorted(reader, key=lambda x: x.get("Code1", "").strip())
    electives: dict = dict()

    # Generate electives dict
    for row in sorted_reader:
        code = row.get("Code1", "").strip()
        if code and not electives.get(code):
            electives[code] = {
                "area": row.get("Area", "").strip(),
                "course": row.get("Course", "").strip(),
                "faculty": [row.get("Faculty", "").strip()],
                "track": row.get("Track", "").strip(),
            }
        elif code:
            if row.get("Faculty", "").strip() not in electives[code]["faculty"]:
                electives[code]["faculty"].append(row.get("Faculty", "").strip())

    return electives


def get_elective_schedule(term: str, code: str) -> list[dict]:
    """Get schedule for a specific elective"""
    # Build the CSV export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={term.upper()}"

    # Fetch the CSV content as a dict
    reader = get_csv(csv_url)
    schedule = list()

    # Get schedule for the specific elective code
    for row in reader:
        if row.get("Code1", "").strip() == code:
            row["Code"] = row.get("Code1", "").strip()
            schedule.append(row)

    if not schedule:
        abort(404, description="Elective not found")
    return schedule


def handle_elective(term: str, code: str) -> list[dict]:
    """Handle elective events for a given term and code"""

    # Fetch the CSV content as dict
    reader = get_elective_schedule(term, code)
    for row in reader:
        row["Date"] = datetime.strptime(
            row.get("Date", "").strip(), "%d-%m-%Y"
        ).strftime("%d-%b-%y")
    return handle_event_dict(list(reader), includeSessionCount=True, elective=True)


################################################################################
# Formatter Functions
################################################################################


def format_ics_datetime(dt_str: str) -> str:
    """Format datetime string to ICS format (UTC)"""
    dt = datetime.fromisoformat(dt_str)
    return dt.astimezone(pytz.UTC).strftime("%Y%m%dT%H%M%SZ")


def generate_ics(calendar_id: str, events: list) -> str:
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
