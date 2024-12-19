import json
import httpx
import os
import logging
from datetime import datetime, timedelta

from schedule import Schedule

from dotenv import load_dotenv

logger = logging.getLogger()

load_dotenv()


class PTO:

    def __init__(self, schedule, engineers):
        self.schedule = schedule  # Use the same schedule as the one used in the dispatcher, but 52 weeks
        self.engineers = (
            engineers  # Use the same engineers as the one used in the dispatcher
        )
        self.get_pto_from_team_sync()

    def sync_pto_with_schedule(self):
        self.match_pto_for_all(self.engineers_pto)

    def get_pto_from_team_sync(self):
        # this is where I call the teamsync API to get the PTO for all engineers
        self.engineers_pto = {}

    def get_pto_for_engineer(self, engineer):
        return self.engineers_pto[engineer.id]

    def match_pto_for_all(self, engineers_pto):
        for engineer in self.engineers:
            schedule_for_engineer = self.schedule.get_schedule_for_engineer(engineer.id)
            pto_for_engineer = engineers_pto.get(
                engineer.email
            )  # get pto using email to make it easier for TeamSync
            self.match_pto_with_rotation(
                engineer, schedule_for_engineer, pto_for_engineer
            )

    def match_pto_with_rotation(self, rotations, pto):
        for rotation in rotations:
            for pto_period in pto:
                if self.is_pto_within_rotation(rotation, pto_period):
                    self.post_schedule_override(
                        rotation["rotationId"],
                        rotation["startDate"],
                        rotation["endDate"],
                    )

    def is_pto_within_rotation(self, rotation, pto_period):
        # I may have to rework this logic to account for timezones
        return datetime.fromisoformat(rotation["startDate"]) <= datetime.fromisoformat(
            pto_period["startDate"]
        ) and datetime.fromisoformat(rotation["endDate"]) >= (
            datetime.fromisoformat(pto_period["endDate"] + timedelta(days=1))
        )

    def post_schedule_override(self, rotation_id, start_date, end_date):
        override_id = "5ca61c308ceea6273c166c53"  # Seeq Support Automation accountId
        url = f"https://api.atlassian.com/jsm/ops/api/d6454c95-d34b-48af-9663-08d399ac4cf2/v1/schedules/d85b457d-4d01-4a0c-bbeb-69d979d03693/overrides"
        auth = httpx.BasicAuth(os.getenv("API_EMAIL"), os.getenv("API_SECRET"))
        client = httpx.Client(auth=auth)
        headers = {"Accept": "application/json"}
        body = {
            "responder": {"type": "user", "id": override_id},
            "rotationIds": [rotation_id],
            "startDate": start_date,
            "endDate": end_date,
        }
        response = client.post(url, headers=headers, auth=auth, body=body)
        return response

    def update_availability(self):
        scale = sorted([float(num) for num in os.getenv("PTO_SCALE").split(",")])

        for engineer in self.engineers:
            ptos = self.get_pto_for_engineer(engineer)
            for pto in ptos:
                pto_start_date = datetime.fromisoformat(pto["startDate"])
                pto_end_date = datetime.fromisoformat(pto["endDate"])

                # if PTO starts on Monday and/or ends on Friday then add the weekend to the PTO calculation
                if pto_start_date.weekday() == 0:
                    logger.info(
                        f"Engineer {engineer.email}: PTO starts on Monday ({pto_start_date}), adding weekend to PTO calculation. New start time: {pto_start_date - timedelta(days=2)}"
                    )
                    pto_start_date = pto_start_date - timedelta(days=2)
                if pto_end_date.weekday() == 4:
                    logger.info(
                        f"Engineer {engineer.email}: PTO ends on Friday ({pto_end_date}), adding weekend to PTO calculation. New end time: {pto_end_date + timedelta(days=2)}"
                    )
                    pto_end_date = pto_end_date + timedelta(days=2)

                # during PTO set availability to 0
                if pto_start_date < datetime.now() < pto_end_date:
                    engineer.availability = 0
                    logger.info(
                        f"Overriding availability for {engineer.email} to 0, because of PTO"
                    )
                # handle availability before and after PTO
                elif pto_end_date - pto_start_date >= timedelta(days=len(scale)):
                    # Only enter the availability scaling logic if the PTO is greater than or equal to length of the scale
                    if (
                        timedelta(days=0)
                        < (pto_start_date - datetime.now())
                        < timedelta(days=len(scale))
                    ):
                        # If PTO starts in less days than the length of the scale,
                        # set the availability to the scale value where the index matches the days
                        #
                        # e.g. for a scale like [0.0, 0.25, 0.5, 0.75, 1.0] and 3 days until PTO starts,
                        # set the availability to 0.5.
                        # If 0 days until PTO starts meaning it's the day of the PTO, set the availability to 0
                        # If you want to set availability to 0 one day before PTO use the scale [0.0, 0.0, 0.25, 0.5, 0.75, 1.0]
                        engineer.availability = scale[
                            (pto_start_date - datetime.now()).days
                        ]
                        logger.info(
                            f"Scaling availability to {engineer.availability} before PTO for engineer {engineer.email}. Because it starts in {pto_start_date - datetime.now()} days"
                        )
                    elif (
                        timedelta(days=0)
                        < (datetime.now() - pto_end_date)
                        < timedelta(days=len(scale))
                    ):
                        engineer.availability = scale[
                            (datetime.now() - pto_end_date).days
                        ]
                        logger.info(
                            f"Scaling availability to {engineer.availability} after PTO for engineer {engineer.email}. Because it ended {datetime.now() - pto_end_date} days ago"
                        )
