from collections import namedtuple

LibrayWorkItem = namedtuple("LibrayWorkItem", "project_name workitem_title")
ClockifyTask = namedtuple("ClockifyTask", "project_id task_name task_id")

class ClockifyTaskSyncService:
    def __init__(self, library_client, clockify_client):
        self._library_client = library_client
        self._clockify_client = clockify_client
        self.library_workitems_raw = None
        self.clockify_projects = None
        self.clockify_active_tasks = None
        self.clockify_done_tasks = None
        self.library_workitems = None

    def initialize_data(self):
        self.library_workitems_raw = self._library_client.get_workItems_for_User()
        self.library_workitems = self.get_library_workitems_from_raw()
        self.sync_projects()
        self.clockify_active_tasks = self.get_active_tasks_from_clockify()
        self.clockify_done_tasks = self.get_done_tasks_from_clockify()

    def sync(self):
        """Primary method. Syncs both projects and tasks from the Library to Clockify."""
        self.initialize_data()
        self.add_tasks_to_clockify()
        self.remove_tasks_from_clockify()

    def sync_projects(self):
        """Create projects in Clockify that exist in the library."""
        self.clockify_projects = self._clockify_client.get_projects()
        self.add_projects_from_library_to_clockify()
        self.clockify_projects = self._clockify_client.get_projects()  # Update list to include ids of newly created projects

    def get_library_workitems_from_raw(self):
        return [LibrayWorkItem(project_name=workitem.project.name, workitem_title=workitem.id + " - " + workitem.title)
                for workitem in self.library_workitems_raw]

    def add_projects_from_library_to_clockify(self):
        clockify_projects_names = {project.name for project in self.clockify_projects}
        library_projects = {workitem.project.name for workitem in self.library_workitems_raw}
        projects_not_in_clockify = library_projects.difference(clockify_projects_names)
        for project in projects_not_in_clockify:
            self._clockify_client.add_project(project)

    ##TODO could combine this to be a single query, that is then filtered to active and done (helps as # of projects grows N vs N*2)
    def get_active_tasks_from_clockify(self):
        """Get all ACTIVE tasks from all projects in Clockify."""
        clockify_tasks = []
        for project in self.clockify_projects:
            clockify_tasks.extend([ClockifyTask(project_id=project.id, task_name=task.name, task_id=task.id)
                                   for task in self._clockify_client.get_active_tasks_for_project(project.id)])
        return clockify_tasks

    def get_done_tasks_from_clockify(self):
        """Get all DONE tasks from all projects in Clockify."""
        clockify_tasks = []
        for project in self.clockify_projects:
            clockify_tasks.extend([ClockifyTask(project_id=project.id, task_name=task.name, task_id=task.id)
                                   for task in self._clockify_client.get_done_tasks_for_project(project.id)])
        return clockify_tasks

    def add_tasks_to_clockify(self):
        """Compare Tasks in Library vs Clockify.  Add tasks not in Clockify to Clockify"""
        clockify_active_task_names = [task.task_name for task in self.clockify_active_tasks]
        library_workitems_to_add = [library_workitem for library_workitem in self.library_workitems if
                                    library_workitem.workitem_title not in clockify_active_task_names]
        if library_workitems_to_add:
            clockify_done_task_names = [task.task_name for task in self.clockify_done_tasks]
            clockify_done_tasks_dict = {task.task_name: (task.project_id, task.task_id) for task in
                                        self.clockify_done_tasks}
            clockify_projects_dict = dict(self.clockify_projects)
            for workitem_to_add in library_workitems_to_add:
                self.handle_task_addition_to_clockify(workitem_to_add, clockify_done_task_names, clockify_done_tasks_dict, clockify_projects_dict)

    def handle_task_addition_to_clockify(self, workitem_to_add, clockify_done_task_names, clockify_done_tasks_dict, clockify_projects_dict):
        """Create the task in Clockify if it does not exist.  If it does exist and is marked DONE, then mark it ACTIVE."""
        if workitem_to_add.workitem_title in clockify_done_task_names:
            ## Task needs to be marked active
            task_to_mark_active = clockify_done_tasks_dict[workitem_to_add.workitem_title]
            self._clockify_client.mark_task_as_active(task_to_mark_active[0], task_to_mark_active[1],
                                                      workitem_to_add.workitem_title)
        else:
            ## Task does not exist
            project_id = clockify_projects_dict.get(workitem_to_add.project_name, "notFound")
            if project_id == "notFound":
                raise Exception("Project ID not found")
            else:
                self._clockify_client.add_task(project_id, workitem_to_add.workitem_title)

    def remove_tasks_from_clockify(self):
        """Compare tasks in Library vs Clockify.  Remove tasks not in Library from Clockify."""
        library_tasks = {workitem.workitem_title for workitem in self.library_workitems}
        clockify_tasks_to_remove = [task for task in self.clockify_active_tasks if task.task_name not in library_tasks]

        for task in clockify_tasks_to_remove:
            self._clockify_client.mark_task_as_done(task.project_id, task.task_id, task.task_name)
