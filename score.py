import logging
from datetime import datetime, timezone

import pandas as pd

import utils

logger = logging.getLogger()


class Score:
    def __init__(self, engineers, **kwargs):
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

        if kwargs.get("issue"):
            self.set_named_engineer_score(kwargs.get("issue"))
            self.set_time_score(kwargs.get("issue"))

    def set_engineers(self, engineers):
        results = []
        for engineer in engineers:
            results.append({"engineer": engineer})
        return results

    def set_named_engineer_score(self, issue):
        self.scores["named_engineer"] = {
            eng.email: (
                1
                if any(org in eng.organizations for org in issue.organization)
                else None
            )
            for eng in self.engineers
        }

    def set_workload_score(self):
        self.scores["workload"] = {
            eng.email: eng.tickets_assigned for eng in self.engineers
        }

    # score based on how many work hours the engineer has before the sla breaches
    def set_time_score(self, issue):
        if not issue.breach_time or issue.is_breached:
            logger.warning(
                f"Not setting time score because breach_time: {issue.breach_time}, is_breached: {issue.is_breached}"
            )
            return

        self.scores["time"] = {
            eng.email: utils.calculate_remaining_work_hours(
                start_datetime=datetime.now(timezone.utc),
                end_datetime=issue.breach_time,
                schedule=eng.schedule,
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
            # if availability is 0, final_score is 0
            if (self.scores["availability"] == 0).any():
                self.scores.loc[self.scores["availability"] == 0, "final_score"] = 0

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
                f"Multiple engineers with the same final score: {selected_engineers.index.tolist()}, assigning it randomly"
            )
            return selected_engineers.sample().index[0]
        else:
            return selected_engineers.index[0]

    def assign_issue(self, test_mode=False):
        self.issue._assign_issue(self.get_selected_engineer(), test_mode=test_mode)

    def get_issue(self):
        return self.issue
