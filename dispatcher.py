# One class of Engineer that will have attributes:
# to hold their work time, with start and end times.
# An attribute to hold their name and another to hold their email address.
# An attribute to hold a list of their dedicated organizations
# An attribute to store their availability being 0 unavailable and 1 available, any number in between is partially available
# An attribute to hold the number of tickets they have currently assigned to them
# an attribute to hold the upper and lower limit of tickets they can handle
#
# Another class of Issue that will have attributes:
# Issue created timestamp
# Issue SLA due timestamp
# Issue status
# Issue severity
# Issue request type
# Issue assignee
# Issue Organization
# Issue key
# An attribute to hold a list of engineers and a score for each one
#

from jira import JIRA
import os
from dotenv import load_dotenv
import asyncio
from datetime import time
import traceback
import logging
from engineer import Engineer
from issue import Issue
from score import Score

load_dotenv()
logger = logging.getLogger()


async def reset_all_engineers(engineers):
    # Collect all reset_engineer coroutines
    reset_tasks = [engineer.reset_engineer() for engineer in engineers]

    # Run all reset_engineer coroutines concurrently
    await asyncio.gather(*reset_tasks)


def main():
    jira = JIRA(
        server=os.getenv("SERVER"),
        basic_auth=(os.getenv("API_EMAIL"), os.getenv("API_SECRET")),
    )
    eng1 = Engineer(
        email="hiroito.watanabe@seeq.com",
        organizations=["Seeq", "Silicon Ranch Company"],
        availability=0.5,
        work_time={"start": time(13, 0, 0), "end": time(22, 0, 0)},
        jira=jira,
    )
    eng2 = Engineer(
        email="mike.cantrell@seeq.com",
        organizations=["Silicon Ranch Company", "Eastman Chemical Company"],
        availability=1,
        work_time={"start": time(15, 0, 0), "end": time(1, 0, 0)},
        jira=jira,
    )
    eng3 = Engineer(
        email="steve.osoro@seeq.com",
        organizations=["Seeq", "Silicon Ranch Company"],
        availability=1,
        work_time={"start": time(11, 0, 0), "end": time(18, 0, 0)},
        jira=jira,
    )
    eng4 = Engineer(
        email="nickson.njogu@seeq.com",
        organizations=["Seeq", "Silicon Ranch Company"],
        availability=1,
        work_time={"start": time(5, 0, 0), "end": time(13, 0, 0)},
        jira=jira,
    )

    print("Querying jira for unassigned tickets")
    jira_issues = jira.search_issues(
        jql_str=f'project = sup and assignee = EMPTY and status NOT IN (Canceled, Closed, Logged, Slated) and "Request Type" not in ("Analytics Help (SUP)", "Application Development (SUP)", "Applied ML (SUP)", "Seeq Certification and Training (SUP)") AND "Escalation[Dropdown]" = "E1 - Front-Line Support" ORDER BY created ASC'
    )
    for jira_issue in jira_issues:
        try:
            ticket = Issue(jira_issue, jira)
            score = Score(ticket, [eng1, eng2, eng3, eng4])
            print(score.scores.to_string())
            score.set_final_score()
            print("-------------------------------------")
            print(score.scores.to_string())
            score.assign_issue()

            # Reset all engineers
            asyncio.run(reset_all_engineers([eng1, eng2, eng3, eng4]))

            print("=====================================")
            # print(score)
        except Exception as e:
            print(
                f"Error processing issue {jira_issue.key}: {e} - {traceback.format_exc()}"
            )
            break


main()