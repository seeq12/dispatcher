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

import asyncio
import logging
import os
import traceback

from dotenv import load_dotenv
from jira import JIRA

from atl_confluence import ConfluenceData
from engineer import Engineer
from issue import Issue
from schedule import Schedule
from score import Score

load_dotenv()
logger = logging.getLogger()


async def reset_all_engineers(engineers, semaphore):
    # Collect all reset_engineer coroutines
    reset_tasks = [engineer.reset_engineer(semaphore) for engineer in engineers]

    # Run all reset_engineer coroutines concurrently
    await asyncio.gather(*reset_tasks)


def main():
    jira = JIRA(
        server=os.getenv("SERVER"),
        basic_auth=(os.getenv("API_EMAIL"), os.getenv("API_SECRET")),
    )
    test_mode = (os.getenv("TEST_MODE", "False").lower() == 'true')

    Engineer.set_jira(jira)
    print("Getting confluence data")
    confluence = ConfluenceData()
    print("Creating schedule")
    schedule = Schedule(os.getenv("SCHEDULE_ID"), 2, "weeks")
    print("Creating engineers")
    engineers = Engineer.create_engineers(schedule, confluence)
    print("Querying jira for unassigned tickets")
    jira_issues = jira.search_issues(
        jql_str='project = sup \
                AND assignee = EMPTY \
                AND status NOT IN (Canceled, Closed, Logged, Slated) \
                AND "Request Type" not in \
                    ("Analytics Help (SUP)", \
                    "Application Development (SUP)", \
                    "Applied ML (SUP)", \
                    "Seeq Certification and Training (SUP)") \
                AND "Escalation[Dropdown]" = "E1 - Front-Line Support" \
                ORDER BY created ASC'
    )

    for jira_issue in jira_issues:
        try:
            ticket = Issue(jira_issue, jira)
            score = Score(ticket, engineers)
            print(score.scores.to_string())
            score.set_final_score()
            print("-------------------------------------")
            print(score.scores.to_string())
            selected_engineer = score.get_selected_engineer()
            ticket._assign_issue(selected_engineer, test_mode=test_mode)
            
            if test_mode:
                eng_assigned = selected_engineer
                for engineer in engineers:
                    if engineer.email == eng_assigned:
                        engineer.tickets_assigned += 1
            else:
                # Reset all engineers
                semaphore = asyncio.Semaphore(5)
                asyncio.run(reset_all_engineers(engineers, semaphore))

            print("=====================================")
            # print(score)
        except Exception as e:
            print(
                f"Error processing issue {jira_issue.key}: {e} - {traceback.format_exc()}"
            )
            break


main()
