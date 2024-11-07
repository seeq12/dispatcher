import asyncio
import logging

logger = logging.getLogger()


class Engineer:
    def __init__(self, id):
        self.get_engineer_from_jira(id)
        self.organizations = []
        self.availability = 1
        self.set_assigned_tickets()
        self.scores = {}

    @classmethod
    def set_jira(cls, jira):
        cls.jira = jira

    def get_engineer_from_jira(self, id):
        user = self.jira.user(id=id)
        self.email = user.emailAddress
        self.name = user.displayName

    async def reset_engineer(self):
        loop = asyncio.get_event_loop()
        # print(f"Resetting {self.email}")
        await loop.run_in_executor(None, self.set_assigned_tickets)
        self.scores = {}

    def add_schedule(self, schedule):
        self.schedule = schedule

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
