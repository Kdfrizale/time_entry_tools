"""Class to represent a Work Record"""
from fractions import Fraction


def convert_to_hours(duration_seconds: float) -> float:
    """Convert seconds to hours"""
    return max(round(duration_seconds / 3600, 2), 0.25)


def round_hours_for_library(hour_duration: float) -> str:
    """Round the input to the nearest quarter hour.  Convert to String"""
    return str(Fraction(round(hour_duration * 4) / 4)) + "h"


def get_workitem_id_from_task_name(task_name: str):
    """Parse the Task Name to get the Work Item ID"""
    return task_name.split(" ")[0]


class WorkRecord:
    """Class to represent a Work Record"""
    def __init__(self, date: str, time_spent: float, work_item_id: str, description: str = None):
        self.date = date
        self.time_spent = time_spent
        self.work_item_id = work_item_id
        self.description = description
