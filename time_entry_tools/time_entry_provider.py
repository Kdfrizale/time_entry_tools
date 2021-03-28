from abc import ABC, abstractmethod


class TimeEntryProvider(ABC):
    @abstractmethod
    def get_work_records(self, stateDate: str, endDate: str):
        raise NotImplementedError

    @abstractmethod
    def save_work_records(self, work_records: list):
        raise NotImplementedError