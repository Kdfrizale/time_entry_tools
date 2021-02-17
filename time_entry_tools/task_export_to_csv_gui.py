import csv
import configparser
from gooey import Gooey, GooeyParser

from time_entry_tools.library_time_entry_provider import LibraryTimeEntryProvider


@Gooey(program_name="Task Exporter", auto_start=True, use_cmd_args=True)
def main():
    ## Parse Command-Line arguments
    parser = GooeyParser(description="Task Exporter")
    parser.add_argument("user_name", help="Your library user name", type=str)
    parser.add_argument("password", help="Your library password", type=str, widget='PasswordField')
    parser.add_argument("output_file", help="Output csv filename", type=str, widget='FileSaver')
    args = parser.parse_args()

    ## Read configuration file
    config = configparser.ConfigParser()
    config.read("config.cfg")

    library_client = LibraryTimeEntryProvider(library_url=config['Library']['server_url'], user_name=args.user_name,
                                                      password=args.password)
    workitems = library_client.get_workItems_for_User()

    formatted_workitem_list = [[workitem.project.name, workitem.id + " - " + workitem.title] for workitem in workitems]
    header = ['Project', 'Task']

    with open(args.output_file, "w", newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(header)
        writer.writerows(formatted_workitem_list)


if __name__ == '__main__':
    main()
