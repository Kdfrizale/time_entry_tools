from fractions import Fraction


def convert_to_hours(durationSeconds: float) -> float:
    return max(round(durationSeconds / 3600, 2), 0.25)


def round_hours_for_library(hourDuration: float) -> str:
    return str(Fraction(round(hourDuration * 4) / 4)) + "h"


def get_workitem_id_from_task_name(taskName: str):
    return taskName.split(" ")[0]


class WorkRecord:
    def __init__(self, date: str, timeSpent: float, workItemID: str, description: str = None):
        self.date = date
        self.timeSpent = timeSpent
        self.workItemID = workItemID
        self.description = description
