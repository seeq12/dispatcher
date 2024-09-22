from jira import JIRA
from datetime import datetime, timezone
import pandas as pd
import traceback
import logging
import utils

logger = logging.getLogger()


class Score:
    def __init__(self, issue, engineers):
        self.issue = issue
        self.engineers = engineers

        self.scores = pd.DataFrame(
            index=[eng.email for eng in self.engineers],
            columns=[
                "availability",
                "workload",
                "time",
                "named_engineer",
                "final_score",
            ],
        )
        self.set_availability_score()
        self.set_workload_score()
        self.set_time_score()
        self.set_named_engineer()

    def set_engineers(self, engineers):
        results = []
        for engineer in engineers:
            results.append({"engineer": engineer})
        return results

    def set_named_engineer(self):
        self.scores["named_engineer"] = {
            eng.email: (
                1
                if any(org in eng.organizations for org in self.issue.organization)
                else None
            )
            for eng in self.engineers
        }

    def set_workload_score(self):
        self.scores["workload"] = {
            eng.email: eng.tickets_assigned for eng in self.engineers
        }

    # score based on how many work hours the engineer has before the sla breaches
    def set_time_score(self):
        if not self.issue.breach_time or self.issue.is_breached:
            print(
                f"Not setting time score because breach_time: {self.issue.breach_time}, is_breached: {self.issue.is_breached}"
            )
            return

        self.scores["time"] = {
            eng.email: utils.calculate_remaining_work_hours(
                start_datetime=datetime.now(timezone.utc),
                end_datetime=self.issue.breach_time,
                start_time=eng.work_time["start"].replace(tzinfo=timezone.utc),
                end_time=eng.work_time["end"].replace(tzinfo=timezone.utc),
            )
            for eng in self.engineers
        }

    def set_availability_score(self):
        self.scores["availability"] = {
            eng.email: eng.availability for eng in self.engineers
        }

    def set_final_score(self):
        self.normalize_scores()

        # final score is 1 if named_engineer for the row is 1, otherwise it is the average of the other scores
        if self.scores["named_engineer"].any():
            self.scores["final_score"] = self.scores["named_engineer"]
        else:
            self.scores["final_score"] = self.scores.mean(axis=1)

    def normalize_scores(self):
        # normalize all scores, except final_score and named_engineer
        for score_type in set(self.scores.columns) - set(
            ["final_score", "named_engineer"]
        ):
            self.scores[score_type] = self.scores[score_type].apply(
                lambda x: utils.normalize_num(
                    num=x, nums=self.scores[score_type].tolist()
                )
            )

        # apply (1 - score) for workload
        self.scores["workload"] = 1 - self.scores["workload"]

    def _average_scores(self, engineer):
        # print(engineer.email, engineer.scores.items())
        scores = [
            value for key, value in engineer.scores.items() if key != "final_score"
        ]
        return sum(scores) / len(scores)

    def get_selected_engineer(self):
        # return the row with the highest final_score in the scores dataframe, if there are multiple rows with the same final_score, return randomly.
        selected_engineers = self.scores[
            self.scores["final_score"] == self.scores["final_score"].max()
        ]

        if selected_engineers.shape[0] > 1:
            print(
                f"Multiple engineers with the same final score: {selected_engineers.index.tolist()}"
            )
            return selected_engineers.sample().index[0]
        else:
            return selected_engineers.index[0]

    def assign_issue(self):
        self.issue.assign_issue(self.get_selected_engineer())

    def get_issue(self):
        return self.issue
