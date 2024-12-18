# https://developer.atlassian.com/cloud/jira/service-desk-ops/rest/v2/intro/#about

import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class Schedule:
    def __init__(self, id, interval, interval_units):
        self.id = id
        self.interval = interval
        self.interval_units = interval_units
        self.get_all_periods()

    def get_schedule(self):
        url = f"https://api.atlassian.com/jsm/ops/api/d6454c95-d34b-48af-9663-08d399ac4cf2/v1/schedules/{self.id}/timeline?interval={self.interval}&intervalUnit={self.interval_units}"
        auth = httpx.BasicAuth(os.getenv("API_EMAIL"), os.getenv("API_SECRET"))
        client = httpx.Client(auth=auth)
        headers = {"Accept": "application/json"}
        response = client.get(url, headers=headers, auth=auth)
        self.schedule = json.loads(response.text)

    def get_all_rotations(self):
        self.get_schedule()
        self.all_rotations = [
            rotation for rotation in self.schedule["finalTimeline"]["rotations"]
        ]

    def get_all_periods(self):
        self.get_all_rotations()
        self.all_periods = []
        for rotation in self.all_rotations:
            if rotation.get("periods"):
                self.all_periods.extend(rotation.get("periods"))

    def get_enginners_from_schedule(self):
        all_engineers = set()
        for period in self.all_periods:
            all_engineers.add(period["responder"]["id"])
        return all_engineers

    def get_schedule_for_engineer(self, engineerId):
        schedule = []
        for period in self.all_periods:
            if period["responder"]["id"] == engineerId:
                schedule.append(
                    {"startDate": period["startDate"], "endDate": period["endDate"]}
                )
        return schedule
