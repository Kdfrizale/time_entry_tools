import csv
import configparser

from gooey import Gooey, GooeyParser

from time_entry_tools.ClockifyTaskSyncService import ClockifyTaskSyncService
from time_entry_tools.clockify_time_entry_provider import ClockifyTimeEntryProvider
from time_entry_tools.library_time_entry_provider import LibraryTimeEntryProvider


def export_library_tasks_to_file(library_client, filename):
    workitems = library_client.get_workItems_for_User()
    formatted_workitem_list = [[workitem.project.name, workitem.id + " - " + workitem.title] for workitem in workitems]
    header = ['Project', 'Task']

    with open(filename, "w", newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(header)
        writer.writerows(formatted_workitem_list)


# @Gooey(program_name="Task Exporter", auto_start=True, use_cmd_args=True)
def main():
    ## Parse Command-Line arguments
    parser = GooeyParser(description="Task Exporter")
    # parser.add_argument("user_name", help="Your library user name", type=str)
    # parser.add_argument("password", help="Your library password", type=str, widget='PasswordField')
    # parser.add_argument("output_file", help="Output csv filename", type=str, widget='FileSaver')
    args = parser.parse_args()

    ## Read configuration file
    config = configparser.ConfigParser()
    config.read("config.cfg")

    library_client = LibraryTimeEntryProvider(library_url=config['Library']['server_url'], user_name=args.user_name,
                                              password=args.password, library_workitem_query=config['Library']['workitem_query'])
    clockify_client = ClockifyTimeEntryProvider(config["Clockify"]["api_key"], config["Clockify"]["workspace_id"])

    ## OLD METHOD - Export to CSV then manual Import
    # export_library_tasks_to_file(library_client, args.output_file)

    ## NEW METHOD - Automatic Sync with library and clockify
    myServiceTest = ClockifyTaskSyncService(library_client, clockify_client)
    myServiceTest.sync()


if __name__ == '__main__':
    main()
