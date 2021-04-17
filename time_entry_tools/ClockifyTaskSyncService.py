import time


class ClockifyTaskSyncService():
    def __init__(self, library_client, clockify_client):
        self._library_client = library_client
        self._clockify_client = clockify_client
        self.library_workitems = None
        self.clockify_projects = None

    def sync(self):
        self.library_workitems = self._library_client.get_workItems_for_User()
        self.clockify_projects = self._clockify_client.get_projects()
        self.add_tasks_to_clockify()
        self.remove_tasks_from_clockify()

    def add_tasks_to_clockify(self):
        # Add Projects to Clockify
        self.add_projects_from_library_to_clockify()
        self.clockify_projects = self._clockify_client.get_projects()  # Update list to include ids of newly created projects
        self.add_tasks_from_library_to_clockify()

    def add_projects_from_library_to_clockify(self):
        clockify_projects_names = {project.name for project in self.clockify_projects}
        library_projects = {workitem.project.name for workitem in self.library_workitems}
        projects_not_in_clockify = library_projects.difference(clockify_projects_names)
        for project in projects_not_in_clockify:
            self._clockify_client.add_project(project)
            time.sleep(self._clockify_client.api_rate_limit_delay)  # Rate limit to less than 10 API requests per second

    def add_tasks_from_library_to_clockify(self):
        ## Add Tasks not in clockify to clockify
        ## compare tasks in library and clockify
        library_tasks = {workitem.id + " - " + workitem.title for workitem in self.library_workitems}
        clockify_tasks = []
        for project in self.clockify_projects:
            tasks = self._clockify_client.get_tasks_for_project(project.id)
            clockify_tasks += tasks
            time.sleep(self._clockify_client.api_rate_limit_delay)  # Rate limit to less than 10 API requests per second

        tasks_to_add_to_clockify = library_tasks.difference(set(clockify_tasks))

        # get Library Project name for task
        library_workitem_tuples_to_add = [(workitem.project.name, workitem.id + " - " + workitem.title) for workitem in
                                          self.library_workitems if
                                          workitem.id + " - " + workitem.title in tasks_to_add_to_clockify]

        # get clockify project id for that project name
        clockify_projects_dict = dict(self.clockify_projects)
        for workitem_to_add in library_workitem_tuples_to_add:
            project_id = clockify_projects_dict.get(workitem_to_add[0], "notFound")
            if project_id == "notFound":
                raise Exception("Project ID not found")
            else:
                self._clockify_client.add_task(project_id, workitem_to_add[1])
                time.sleep(
                    self._clockify_client.api_rate_limit_delay)  # Rate limit to less than 10 API requests per second

    def remove_tasks_from_clockify(self):
        pass
