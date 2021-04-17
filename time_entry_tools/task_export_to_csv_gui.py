import csv
import configparser
import time

from gooey import Gooey, GooeyParser

from time_entry_tools.ClockifyTaskSyncService import ClockifyTaskSyncService
from time_entry_tools.clockify_time_entry_provider import ClockifyTimeEntryProvider
from time_entry_tools.library_time_entry_provider import LibraryTimeEntryProvider

def sync_library_and_clockify_projects_and_tasks(library_client, clockify_client):
    workitems = library_client.get_workItems_for_User()
    clockify_projects = clockify_client.get_projects()
    add_projects_from_library_to_clockify(workitems, clockify_projects, clockify_client)
    clockify_projects = clockify_client.get_projects()  ## Update list to include ids of newly created proejcts
    add_tasks_from_library_to_clockify(workitems, clockify_projects, clockify_client)

def add_projects_from_library_to_clockify(library_workitems, clockify_projects, clockify_client):
    clockify_projects_names = {project[0] for project in clockify_projects}
    library_projects = {workitem.project.name for workitem in library_workitems}
    projects_not_in_clockify = library_projects.difference(clockify_projects_names)
    # print("Projects not in clockify: ", projects_not_in_clockify)
    for project in projects_not_in_clockify:
        clockify_client.add_project(project)
        time.sleep(0.11) # Rate limit to less than 10 API requests per second


def add_tasks_from_library_to_clockify(library_workitems, clockify_projects, clockify_client):
    ## Add Tasks not in clockify to clockify
    ## compare tasks in library and clockify
    library_tasks = {workitem.id + " - " + workitem.title for workitem in library_workitems}
    clockify_tasks = []
    for project in clockify_projects:
        project_id = project[1]
        tasks = clockify_client.get_tasks_for_project(project_id)
        clockify_tasks += tasks
        time.sleep(0.11) # Rate limit to less than 10 API requests per second

    tasks_to_add_to_clockify = library_tasks.difference(set(clockify_tasks))

    # get Library Project name for task
    library_workitem_tuples_to_add = [(workitem.project.name, workitem.id + " - " + workitem.title) for workitem in library_workitems if workitem.id + " - " + workitem.title in tasks_to_add_to_clockify]

    # get clockify project id for that project name
    clockify_projects_dict = dict(clockify_projects)
    for workitem_to_add in library_workitem_tuples_to_add:
        project_id = clockify_projects_dict.get(workitem_to_add[0], -1)
        if project_id == -1:
            raise Exception("Project ID not found")
        else:
            print("project Id", project_id)
            print("workitem", workitem_to_add[1])
            clockify_client.add_task(project_id, workitem_to_add[1])
            time.sleep(0.11) # Rate limit to less than 10 API requests per second


def export_library_tasks_to_file(library_client, filename):
    workitems = library_client.get_workItems_for_User()

    formatted_workitem_list = [[workitem.project.name, workitem.id + " - " + workitem.title] for workitem in workitems]
    header = ['Project', 'Task']

    with open(filename, "w", newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(header)
        writer.writerows(formatted_workitem_list)


@Gooey(program_name="Task Exporter", auto_start=True, use_cmd_args=True)
def main():
    ## Parse Command-Line arguments
    parser = GooeyParser(description="Task Exporter")
    parser.add_argument("user_name", help="Your library user name", type=str)
    parser.add_argument("password", help="Your library password", type=str, widget='PasswordField')
    # parser.add_argument("output_file", help="Output csv filename", type=str, widget='FileSaver')
    args = parser.parse_args()

    ## Read configuration file
    config = configparser.ConfigParser()
    config.read("config.cfg")

    library_client = LibraryTimeEntryProvider(library_url=config['Library']['server_url'], user_name=args.user_name,
                                              password=args.password)
    clockify_client = ClockifyTimeEntryProvider(config["Clockify"]["api_key"], config["Clockify"]["workspace_id"])

    myServiceTest = ClockifyTaskSyncService(library_client, clockify_client)
    myServiceTest.sync()

    ## OLD METHOD - Export to CSV then manual Import
    # export_library_tasks_to_file(library_client, args.output_file)

    ## NEW METHOD - Automatic Sync with library and clockify
    # sync_library_and_clockify_projects_and_tasks(library_client, clockify_client)
    myServiceTest = ClockifyTaskSyncService(library_client, clockify_client)
    myServiceTest.sync()


if __name__ == '__main__':
    main()
