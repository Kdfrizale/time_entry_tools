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
    def projects_endpoint(self):
        return "https://api.clockify.me/api/v1/workspaces/%s/projects" % self.clockify_workspace_id

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

    def get_projects(self):
        response = requests.get(self.projects_endpoint, headers=self.headers)
        return self.parse_clockify_response_for_projects(response.json())

    def save_work_records(self, work_records: list):
        raise NotImplementedError

    def add_project(self, project_name):
        json_request = {
            "name": project_name,
        }
        response = requests.post(self.projects_endpoint, headers=self.headers, json=json_request)
        if response.status_code != 201:
            raise Exception("Project creation failed in Clockify! Response code : ", response.status_code)

    def get_tasks_for_project(self, project_id):
        response = requests.get(self.projects_endpoint + "/%s/tasks" % project_id, headers=self.headers)
        return self.parse_clockify_response_for_project_tasks(response.json())


    def add_task(self, project_id, task_name):
        json_request = {
            "name": task_name,
        }
        response = requests.post(self.projects_endpoint + "/%s/tasks" % project_id, headers=self.headers, json=json_request)
        if response.status_code != 201:
            raise Exception("Task creation failed in Clockify! Response code : ", response.status_code)

    @staticmethod
    def parse_clockify_response_for_project_tasks(json_response):
        tasks = []
        for task_json in json_response:
            tasks.append(str(task_json.get('name')))
        return tasks

    @staticmethod
    def parse_clockify_response_for_projects(json_response):
        projects = []
        for project in json_response:
            projects.append((str(project.get('name')), str(project.get('id'))))
        return projects
        # print(projects)

    @staticmethod
    def parse_clockify_response_for_work_records(json_response):
        dates = json_response.get('groupOne')
        work_records = []
        for date in dates:
            for task in date.get("children"):
                # NOTE: This sums up all clockify time entries into a single Work Record and concats the descriptions
                # together
                # NOTE: Do not concatenate if it is a sales cost center work item
                if( 'Sales' in task.get("name")):
                    # logic to deal with sales workItems that should not concatenate time_records
                    for time_record in task.get("children"):
                        work_records.append(WorkRecord(date=date.get("name"),
                                                       timeSpent=convert_to_hours(time_record.get('duration')),
                                                       workItemID=get_workitem_id_from_task_name(task.get("name")),
                                                       description=time_record.get("name")))
                else:
                    task_workRecords = task.get("children")
                    task_workRecord_descriptions = [task_workRecord.get("name") for task_workRecord in task_workRecords]

                    work_records.append(WorkRecord(date=date.get("name"),
                                                   timeSpent=convert_to_hours(task.get('duration')),
                                                   workItemID=get_workitem_id_from_task_name(task.get("name")),
                                                   description=",".join(task_workRecord_descriptions)))
        return work_records
