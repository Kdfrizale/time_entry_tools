import requests
from time_entry_tools.workrecord import WorkRecord, convert_to_hours, get_workitem_id_from_task_name

from time_entry_tools.time_entry_provider import TimeEntryProvider


class ClockifyTimeEntryProvider(TimeEntryProvider):
    def __init__(self, clockify_api_key, clockify_workspace_id):
        self.clockify_api_key = clockify_api_key
        self.clockify_workspace_id = clockify_workspace_id

    @property
    def summary_report_endpoint(self):
        return "https://reports.api.clockify.me/v1/workspaces/%s/reports/summary" % self.clockify_workspace_id

    @property
    def headers(self):
        return {
            "content-type": "application/json",
            "x-api-key": self.clockify_api_key
        }

    def get_work_records(self, stateDateTime: str, endDateTime: str):
        json_request = {
            "dateRangeStart": stateDateTime,
            "dateRangeEnd": endDateTime,
            "summaryFilter": {
                "groups": [
                    "DATE",
                    "TASK",
                    "TIMEENTRY"
                ]
            }
        }
        response = requests.post(self.summary_report_endpoint, headers=self.headers, json=json_request)
        return self.parse_clockify_response_for_work_records(response.json())

    def save_work_records(self, work_records: list):
        raise NotImplementedError

    @staticmethod
    def parse_clockify_response_for_work_records(json_response):
        dates = json_response.get('groupOne')
        work_records = []
        for date in dates:
            for task in date.get("children"):
                # NOTE: This sums up all clockify time entries into a single Work Record and concats the descriptions
                # together
                task_workRecords = task.get("children")
                task_workRecord_descriptions = [task_workRecord.get("name") for task_workRecord in task_workRecords]

                work_records.append(WorkRecord(date=date.get("name"),
                                               timeSpent=convert_to_hours(task.get('duration')),
                                               workItemID=get_workitem_id_from_task_name(task.get("name")),
                                               description=",".join(task_workRecord_descriptions)))
        return work_records
