import icalendar
import os
from dotenv import load_dotenv

load_dotenv()

ics_url = os.getenv("ICS_URL")


# using icalendar python library, subscribe to an ics file and return the events in the file
def get_events(ics_url):
    # get the ics file
    ics_file = icalendar.Calendar.from_ical(ics_url)
    # get the events in the ics file
    events = []
    for event in ics_file.walk("vevent"):
        events.append(event)
    return events
