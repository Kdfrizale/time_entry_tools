"""Clockify Specific Time Entry Provider"""

from collections import namedtuple, deque
from datetime import datetime, timedelta
import time

import requests
from time_entry_tools.workrecord import WorkRecord, convert_to_hours, get_workitem_id_from_task_name
from time_entry_tools.time_entry_provider import TimeEntryProvider

Project = namedtuple('Project', 'name id')
Task = namedtuple('Task', 'name id')


def api_rate_limit(func):
    """Decorator to limit how often a function can be called"""
    def inner(self, *args, **kwargs):
        if self._previous_request_timestamps[0] >= datetime.now() - timedelta(seconds=1):
            print("API Rate Limiting... 10 Requests per second")
            time.sleep(self.api_rate_limit_delay) # Rate limit to less than 10 API requests per second
        self._previous_request_timestamps.append(datetime.now())
        return func(self,*args, **kwargs)
    return inner


class ClockifyTimeEntryProvider(TimeEntryProvider):
    """Clockify Interface Class"""
    def __init__(self, clockify_api_key, clockify_workspace_id):
        self.clockify_api_key = clockify_api_key
        self.clockify_workspace_id = clockify_workspace_id
        self._api_rate_limit_delay = 0.11  # seconds, rate limit to less than 10 requests per second
        self._previous_request_timestamps = deque(10*[datetime.min], maxlen=10)

    @property
    def api_rate_limit_delay(self):
        """Number of seconds to delay between requests to ensure the api usage limit is not exceeded"""
        return self._api_rate_limit_delay

    @property
    def summary_report_endpoint(self):
        """URL for the Clockify Summary Report endpoint"""
        return "https://reports.api.clockify.me/v1/workspaces/%s/reports/summary" % self.clockify_workspace_id

    @property
    def projects_endpoint(self):
        """URL for the Clockify Projects endpoint"""
        return "https://api.clockify.me/api/v1/workspaces/%s/projects" % self.clockify_workspace_id

    @property
    def headers(self):
        """HTTP Headers common to all requests to Clockify"""
        return {
            "content-type": "application/json",
            "x-api-key": self.clockify_api_key
        }

    @api_rate_limit
    def get_work_records(self, start_date_time: str, end_date_time: str):
        """REST Request to get work records in clockify between the selected dates."""
        json_request = {
            "dateRangeStart": start_date_time,
            "dateRangeEnd": end_date_time,
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

    @api_rate_limit
    def get_projects(self):
        """REST Request to get all projects in Clockify"""
        response = requests.get(self.projects_endpoint, headers=self.headers)
        return self.parse_clockify_response_for_projects(response.json())

    def save_work_records(self, work_records: list):
        raise NotImplementedError

    @api_rate_limit
    def add_project(self, project_name):
        """REST Request to add a project to Clockify"""
        json_request = {
            "name": project_name,
        }
        response = requests.post(self.projects_endpoint, headers=self.headers, json=json_request)
        if response.status_code != 201:
            raise Exception("Project creation failed in Clockify! Response code : ", response.status_code)

    @api_rate_limit
    def get_active_tasks_for_project(self, project_id):
        """REST Request to get all active tasks for a project in Clockify"""
        response = requests.get(self.projects_endpoint + "/%s/tasks?is-active=true" % project_id, headers=self.headers)
        return self.parse_clockify_response_for_project_tasks(response.json())

    @api_rate_limit
    def get_done_tasks_for_project(self, project_id):
        """REST Request to get all non-active tasks for a project in Clockify"""
        response = requests.get(self.projects_endpoint + "/%s/tasks?is-active=false" % project_id, headers=self.headers)
        return self.parse_clockify_response_for_project_tasks(response.json())

    @api_rate_limit
    def add_task(self, project_id, task_name):
        """REST Request to add a task to Clockify"""
        json_request = {
            "name": task_name,
        }
        response = requests.post(self.projects_endpoint + "/%s/tasks" % project_id, headers=self.headers,
                                 json=json_request)
        if response.status_code != 201:
            raise Exception("Task creation failed in Clockify! Response code : ", response.status_code)

    @api_rate_limit
    def mark_task_as_done(self, project_id, task_id, task_name):
        """REST Request to mark a Clockify Task as DONE"""
        json_request = {
          "name": task_name,
          "status": "DONE"
        }
        response = requests.put(self.projects_endpoint + f'/{project_id}/tasks/{task_id}', headers=self.headers, json=json_request)
        if response.status_code != 200:
            raise Exception("Task update failed in Clockify! Response code : ", response.status_code)

    @api_rate_limit
    def mark_task_as_active(self, project_id, task_id, task_name):
        """REST Request to mark a Clockify Task as ACTIVE"""
        json_request = {
            "name": task_name,
            "status": "ACTIVE"
        }
        response = requests.put(self.projects_endpoint + f'/{project_id}/tasks/{task_id}', headers=self.headers,
                                json=json_request)
        if response.status_code != 200:
            raise Exception("Task update failed in Clockify! Response code : ", response.status_code)

    @api_rate_limit
    def delete(self, project_id, task_id):
        """REST Request to Delete a Task in Clockify"""
        response = requests.delete(self.projects_endpoint + f'/{project_id}/tasks/{task_id}', headers=self.headers)
        if response.status_code != 200:
            raise Exception("Task deletion failed in Clockify! Response code : ", response.status_code)


    @staticmethod
    def parse_clockify_response_for_project_tasks(json_response):
        """Parse JSON response to get a list of tasks"""
        tasks = []
        for task_json in json_response:
            tasks.append(Task(str(task_json.get('name')), str(task_json.get('id'))))
        return tasks

    @staticmethod
    def parse_clockify_response_for_projects(json_response):
        """Parse JSON response to get list of Projects"""
        projects = []
        for project in json_response:
            projects.append(Project(str(project.get('name')),str(project.get('id'))))
            # projects.append((str(project.get('name')), str(project.get('id'))))
        return projects
        # print(projects)

    @staticmethod
    def parse_clockify_response_for_work_records(json_response):
        """Parse Clockify response into WorkRecord objects.
        Aggregates WorkRecords together if they are for the same WorkItem.
        If the WorkItem is for Sales, do NOT aggregate WorkRecords."""
        dates = json_response.get('groupOne')
        work_records = []
        for date in dates:
            for task in date.get("children"):
                # NOTE: This sums up all clockify time entries into a single Work Record and concats the descriptions
                # together
                # NOTE: Do not concatenate if it is a sales cost center work item
                if 'Sales' in task.get("name"):
                    # logic to deal with sales workItems that should not concatenate time_records
                    for time_record in task.get("children"):
                        work_records.append(WorkRecord(date=date.get("name"),
                                                       time_spent=convert_to_hours(time_record.get('duration')),
                                                       work_item_id=get_workitem_id_from_task_name(task.get("name")),
                                                       description=time_record.get("name")))
                else:
                    task_work_records = task.get("children")
                    task_work_record_descriptions = [task_workRecord.get("name")
                                                     for task_workRecord in task_work_records]

                    work_records.append(WorkRecord(date=date.get("name"),
                                                   time_spent=convert_to_hours(task.get('duration')),
                                                   work_item_id=get_workitem_id_from_task_name(task.get("name")),
                                                   description=",".join(task_work_record_descriptions)))
        return work_records
