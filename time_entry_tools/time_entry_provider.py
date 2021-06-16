"""Abstract Class for a Time Tracking Provider"""
from abc import ABC, abstractmethod


class TimeEntryProvider(ABC):
    """Abstract Class for a Time Tracking Provider"""
    @abstractmethod
    def get_work_records(self, start_date: str, end_date: str):
        """Return a list of WorkRecords"""
        raise NotImplementedError

    @abstractmethod
    def save_work_records(self, work_records: list):
        """Save the given WorkRecords to the Time Tracking Provider"""
        raise NotImplementedError
