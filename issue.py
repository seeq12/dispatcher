import logging
from datetime import datetime, timezone

logger = logging.getLogger()


class Issue:
    _date_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    def __init__(self, issue, jira):
        print(issue.key)
        self.jira = jira
        self.issue = issue
        self.set_created()
        self.set_status()
        self.set_severity()
        self.set_request_type()
        self.set_assignee()
        self.set_organization()
        self.set_key()
        self.set_breach_time()
        self.set_is_breached()
        self.engineers = []
        print(self.organization)

    def add_engineer(self, engineer, score):
        self.engineers.append({"engineer": engineer, "score": score})

    def set_breach_time(self):
        try:
            self.breach_time = datetime.strptime(
                self.issue.fields.customfield_11332.ongoingCycle.breachTime.jira,
                self._date_format,
            ).astimezone(timezone.utc)
        except:
            logger.error(
                f"Error parsing SLA breach time for issue {self.issue.key}, most likely SLA already met"
            )
            self.breach_time = None

    def set_is_breached(self):
        try:
            self.is_breached = (
                self.issue.fields.customfield_11332.ongoingCycle.breached == "true"
            )
        except:
            try:
                self.is_breached = (
                    self.issue.fields.customfield_11332.completedCycles[0].breached
                    == "true"
                )
            except:
                logger.error(
                    f"Error parsing SLA breach status for issue {self.issue.key}"
                )
                self.is_breached = None

    def set_created(self):
        try:
            self.created = datetime.strptime(
                self.issue.fields.created, self._date_format
            ).astimezone(timezone.utc)
        except:
            logger.error(f"Error parsing created date for issue {self.issue.key}")

    def set_status(self):
        try:
            self.status = self.issue.fields.status.name
        except:
            logger.warning(f"Error parsing status for issue {self.issue.key}")
            self.status = None

    def set_severity(self):
        try:
            self.severity = self.issue.fields.customfield_11302.value
        except:
            logger.info(f"Error parsing severity for issue {self.issue.key}")
            self.severity = None

    def set_request_type(self):
        try:
            self.request_type = self.issue.fields.customfield_11307.requestType.name
        except:
            logger.info(f"Error parsing request type for issue {self.issue.key}")
            self.request_type = None

    def set_assignee(self):
        try:
            self.assignee = self.issue.fields.assignee.displayName
        except:
            logger.info(f"Error parsing assignee for issue {self.issue.key}")
            self.assignee = None

    def set_organization(self):
        try:
            self.organization = [
                org.name for org in getattr(self.issue.fields, "customfield_11200", [])
            ]
        except:
            logger.info(f"Error parsing organization for issue {self.issue.key}")
            self.organization = None

    def set_key(self):
        try:
            self.key = self.issue.key
        except:
            logger.error(f"Error parsing key for issue {self.issue.key}")

    def assign_issue(self, engineer):
        print(f"Assigning {self.key} to {engineer}")
        # self.jira.assign_issue(self.issue, engineer)
