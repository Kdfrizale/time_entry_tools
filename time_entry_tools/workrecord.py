from fractions import Fraction


def convertToHours(durationSeconds: float) -> float:
    return max(round(durationSeconds / 3600, 2), 0.25)


def roundHoursForLibrary(hourDuration: float) -> str:
    return str(Fraction(round(hourDuration * 4) / 4)) + "h"


def getWorkItemIDFromTaskName(taskName: str):
    return taskName.split(" ")[0]


class WorkRecord:
    def __init__(self, date: str, timeSpent: float, workItemID: str, description: str = None):
        self.date = date
        self.timeSpent = timeSpent
        self.workItemID = workItemID
        self.description = description
