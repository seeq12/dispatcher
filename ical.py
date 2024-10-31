import os
import re

from dotenv import load_dotenv

import icalendar
import requests
from datetime import datetime, date, time

load_dotenv()

ics_url = os.getenv("ICS_URL")


def get_ics_file(ics_url):
    return requests.get(ics_url).text


def get_events(ics_url):
    ics_file = icalendar.Calendar.from_ical(get_ics_file(ics_url))
    for event in ics_file.walk("vevent"):
        if "EMEA Rotation" in event.get("SUMMARY"):
            engineers = parse_engineer_from_summary(event)
            dates = {'start_date': event.get("DTSTART").dt, 'end_date': event.get("DTEND").dt}
            print(dates)
            for engineer in engineers:
                engineers[engineer].update(dates)
            # engineers = {engineers[engineer].update(dates) for engineer in engineers}
            print(engineers)
            # print(datetime.strptime(str(event.get("DTSTART")), '%y/%m/%d'))


            print(event.get("DTSTART").dt, event.get("DTEND").dt, event.get("SUMMARY"))
            print("=====================================")


def parse_engineer_from_summary(event):
    pattern = r"EMEA Rotation (.*) - (.*)"
    summary = event.get("SUMMARY")

    match = re.match(pattern, summary)
    # print(list(match.groups()))
    # print(event.get("ATTENDEE"))

    results = []
    # compare list(match.groups()) with list of event.get("ATTENDEE") to get the engineer's email
    if match:
        attendees = event.get("ATTENDEE")
        if attendees:
            attendees = [strip_mail_to(attendee) for attendee in attendees]
            results = {attendee: {"shift": None} for attendee in attendees}
            # print(attendees)
            # print(clean_group_early(match.groups()[0]))
            early_group = clean_group_early(match.groups()[0])
            mid_group = clean_group_mid(match.groups()[1])
            for attendee in attendees:
                for group in early_group:
                    if group in attendee:
                        results[attendee]['shift'] = "early"
                for group in [mid_group]:
                    if group in attendee:
                        results[attendee]['shift'] = "mid"
    return results


def clean_group_early(group):
    return (
        group.lower()  # early bob and alice
        .replace("early", "")  #  bob and alice
        .replace("and", "")  #  bob  alice
        .replace("  ", ",")  #  bob,alice
        .strip()  # bob,alice
        .split(",")  # ['bob','alice']
    )


def clean_group_mid(group):
    return group.lower().replace("mid", "").strip()  # mid bob  #  bob  # bob


def strip_mail_to(email):
    return re.sub(r"mailto:", "", email)


def strip_email_domain(email):
    return re.sub(r"@seeq\.com", "", email)


get_events(ics_url)
