import asyncio
import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger()

load_dotenv()


class Engineer:
    def __init__(self, id, availability, organizations):
        self.id = id
        self.get_engineer_from_jira(id)
        self.availability: float = availability
        self.organizations: list = organizations
        self.set_assigned_tickets()
        self.scores: dict = {}

    @classmethod
    def set_jira(cls, jira):
        cls.jira = jira

    @classmethod
    def create_engineers(cls, schedule, confluence):
        eng_ids = schedule.get_enginners_from_schedule()
        av = confluence.get_confluence_table("availability")
        org = confluence.get_confluence_table("named_engineer")

        engs = []
        for eng_id in eng_ids:
            # if the engineer from schedule is not in the availability table, log a warning and skip
            if eng_id not in [
                item for sublist in list(av["Name"].values) for item in sublist
            ]:
                logger.warning(
                    f"Engineer {eng_id} not found in availability table {[item for sublist in list(av["Name"].values) for item in sublist]}"
                )
                continue

            for _, row in av.iterrows():
                if eng_id in row["Name"]:
                    availability = float(row["Ticket Load"])
                    break

            organizations = []
            for _, row in org.iterrows():
                if eng_id in row["SSE/SRE"]:
                    organizations.append(row["Account"])

            new_eng = cls(eng_id, availability, organizations)
            new_eng.add_schedule(schedule.get_schedule_for_engineer(eng_id))
            engs.append(new_eng)

        return engs

    def get_engineer_from_jira(self, id):
        user = self.jira.user(id=id)
        self.email = getattr(user, "emailAddress", None)
        self.name = getattr(user, "displayName", None)

    async def reset_engineer(self, semaphore):
        async with semaphore:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.set_assigned_tickets)
            self.scores = {}

    def add_schedule(self, schedule):
        self.schedule = schedule

    def set_assigned_tickets(self):
        # api call to jira to get number of ticket assigned to engineer
        if os.getenv("TICKET_COUNT_JQL"):
            jql_str = f"assignee = '{self.email}' AND {os.getenv("TICKET_COUNT_JQL")}"
        else:
            jql_str = f"project = sup and assignee = '{self.email}' and status NOT IN (Canceled, Closed, Logged, Slated)"
        self.tickets_assigned = self.jira.search_issues(jql_str=jql_str).total

    def set_engineer_score(self, score_type, score):
        if score is None:
            return
        self.scores[score_type] = score
