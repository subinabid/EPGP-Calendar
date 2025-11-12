"""IIMK EPGP Calender App

The app get session details form a google sheet and renders an ics
The google sheet is expected to have the following columns

Sec - Section detail - A to F
Code - Format: EPGP-203
Course Name - Format: Economic Environment (EE)
Session - Serial Number - 1 , 2, 3, etc. Quiz sessions will be 31, 32, 33 etc. Assignments will be 51, 52, etc.
Date - Format: 08-Mar-25
Time - Format: 9:00 AM to 11:45 AM in IST

For the second year
    Course codes are suffixed by A, B etc if the same course is offered in multiple sections
    URLs are prefixed with quarter cides. Eg Q5, Q6 etc.
"""

from flask import Flask, Response, render_template
from dotenv import load_dotenv
from config import DOMAIN, VALID_CALENDARS
from helpers import (
    get_classes,
    get_exams,
    get_general_events,
    generate_ics,
    get_electives_list,
    get_elective_schedule,
    handle_elective,
    validate_calendar,
    validate_term,
)

################################################################################
# flask App Initialization
################################################################################
app = Flask(__name__)
load_dotenv()

################################################################################
# Routes
################################################################################


@app.route("/")
def home():
    """Home Page"""
    return render_template("index.html", sections=VALID_CALENDARS, domain=DOMAIN)


@app.route("/<calendar_id>.ics")
def serve_calendar(calendar_id):
    """Serve Section Calendars as ICS"""
    validate_calendar(calendar_id)

    events = get_classes(calendar_id)
    events.extend(get_exams())
    events.extend(get_general_events())
    ics_data = generate_ics(calendar_id, events)

    return Response(
        ics_data,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={calendar_id}.ics"},
    )


@app.route("/electives/<term>")
def electives(term):
    """Electives List Page"""
    validate_term(term)
    electives = get_electives_list(term.upper())

    return render_template(
        "electives.html", electives=electives, term=term.lower(), domain=DOMAIN
    )


@app.route("/<term>/<code>")
def elective_details(term, code):
    """Elective Details Page"""
    validate_term(term)
    schedule = get_elective_schedule(term.upper(), code)

    return render_template(
        "course.html", schedule=schedule, term=term.lower(), domain=DOMAIN
    )


@app.route("/<term>/<code>.ics")
def serve_elective_calendar(term, code):
    """Serve Elective Calendars as ICS"""

    validate_term(term)
    events = handle_elective(term.upper(), code)
    ics_data = generate_ics(f"{term.lower()}_{code}", events)

    return Response(
        ics_data,
        mimetype="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={term.lower()}_{code}.ics"
        },
    )


################################################################################
# Entry Point
################################################################################

if __name__ == "__main__":
    app.run(debug=True)
