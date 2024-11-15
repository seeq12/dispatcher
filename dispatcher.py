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

import pandas as pd
from dotenv import load_dotenv
from jira import JIRA

from atl_confluence import ConfluenceData
from engineer import Engineer
from issue import Issue
from schedule import Schedule
from score import Score
from slack import Slack

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
    test_mode = os.getenv("TEST_MODE", "False").lower() == "true"
    slack_mode = os.getenv("SLACK_MODE", "False").lower() == "true"
    if slack_mode:
        slack = Slack()

    Engineer.set_jira(jira)
    print("Getting confluence data")
    confluence = ConfluenceData()
    print("Creating schedule")
    schedule = Schedule(os.getenv("SCHEDULE_ID"), 2, "weeks")
    print("Creating engineers")
    engineers = Engineer.create_engineers(schedule, confluence)
    print("Querying jira for unassigned tickets")
    jira_issues = jira.search_issues(jql_str=os.getenv("JQL"))

    workload_before = Score(engineers).scores["workload"]
    availability = Score(engineers).scores["availability"]
    workload_after = ""
    if test_mode:
        summary = "------------------TEST MODE: No tickets assigned\n"
    summary = ""
    for jira_issue in jira_issues:
        try:
            ticket = Issue(jira_issue, jira)
            score = Score(engineers, issue=ticket)

            print(score.scores.to_string())
            score.set_final_score()

            print("-------------------------------------")
            print(score.scores.to_string())

            selected_engineer = score.get_selected_engineer()

            ticket._assign_issue(selected_engineer, test_mode=test_mode)
            summary += f"<https://seeq.atlassian.net/browse/{ticket.key}|{ticket.key}> - {ticket.organization} - {jira_issue.fields.summary}: assigned to {selected_engineer}\n"

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
            score.set_workload_score()
            workload_after = score.scores["workload"]
        except Exception as e:
            print(
                f"Error processing issue {jira_issue.key}: {e} - {traceback.format_exc()}"
            )
            break
    if slack_mode:
        workload_before = workload_before.rename("Workload Before")
        workload_after = workload_after.rename("Workload After")

        merged = pd.concat([availability, workload_before, workload_after], axis=1)
        merged["Delta"] = merged["Workload After"] - merged["Workload Before"]
        slack.send_message(f"{summary}")
        slack.send_message(
            f"```{merged.sort_values(by='Workload Before', ascending=False).to_markdown()}```"
        )


main()
