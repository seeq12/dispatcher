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
    logger.info("Getting confluence data")
    confluence = ConfluenceData()
    logger.info("Creating schedule")
    schedule = Schedule(os.getenv("SCHEDULE_ID"), os.getenv("SCHEDULE_WEEKS"), "weeks")
    logger.info("Creating engineers")
    engineers = Engineer.create_engineers(schedule, confluence)
    logger.info("Querying jira for unassigned tickets")
    jira_issues = jira.search_issues(jql_str=os.getenv("JQL"))

    workload_before = Score(engineers).scores["workload"]
    availability = Score(engineers).scores["availability"]
    workload_after = ""
    if test_mode:
        summary = "------------------TEST MODE: No tickets assigned\n"

    for jira_issue in jira_issues:
        try:
            ticket = Issue(jira_issue, jira)
            score = Score(engineers, issue=ticket)

            logger.info(f"Raw scores:\n{score.scores.to_string()}")
            score.set_final_score()
            logger.info(f"Normalized scores:\n{score.scores.to_string()}")

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

            score.set_workload_score()
            workload_after = score.scores["workload"]
        except Exception as e:
            logger.error(
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
