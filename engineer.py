import asyncio
import logging

logger = logging.getLogger()


class Engineer:
    def __init__(self, email, organizations, availability, work_time, jira):
        self.jira = jira
        self.email = email
        self.organizations = organizations
        # self.upper_limit = upper_limit or 0
        # self.lower_limit = lower_limit or 0
        self.availability = availability or 1
        self.work_time = work_time or None
        self.set_assigned_tickets()
        self.scores = {}

    async def reset_engineer(self):
        loop = asyncio.get_event_loop()
        # print(f"Resetting {self.email}")
        await loop.run_in_executor(None, self.set_assigned_tickets)
        self.scores = {}

    def add_work_time(self, start, end):
        self.work_time = {"start": start, "end": end}

    def set_availability(self, availability):
        self.availability = availability

    def set_assigned_tickets(self):
        # api call to jira to get number of ticket assigned to engineer
        self.tickets_assigned = self.jira.search_issues(
            jql_str=f"project = sup and assignee = '{self.email}' and status NOT IN (Canceled, Closed, Logged, Slated)"
        ).total

    def set_engineer_score(self, score_type, score):
        if score is None:
            return
        self.scores[score_type] = score
