import configparser
import PySimpleGUI as sg
from gooey import Gooey, GooeyParser
from datetime import datetime

from time_entry_tools.clockify_time_entry_provider import ClockifyTimeEntryProvider
from time_entry_tools.library_time_entry_provider import LibraryTimeEntryProvider


def get_user_confirmation() -> bool:
    layout = [[sg.Text("Continue with Import to Library?")],
              [sg.Button('Continue')],
              [sg.Button('Cancel')]]

    window = sg.Window('Continue with Import to the Library?', layout)
    event, values = window.read()
    window.close()
    return event == 'Continue'


@Gooey(program_name="Time Entry Export/Import", auto_start=True, use_cmd_args=True)
def main():
    ## Parse Command-Line arguments
    parser = GooeyParser(description="Time Entry Export/Import")
    parser.add_argument("user_name", help="Your library user name", type=str)
    parser.add_argument("password", help="Your library password", type=str, widget='PasswordField')

    start_date_time_default = datetime.today().strftime("%Y-%m-%d")
    end_date_time_default = datetime.today().strftime("%Y-%m-%d")
    parser.add_argument("-s", "--start_date", help="Beginning date for time entry (inclusive). Format YYYY-MM-DD",
                        default=start_date_time_default, widget='DateChooser')
    parser.add_argument("-e", "--end_date", help="End date for time entry (inclusive). Format YYYY-MM-DD",
                        default=end_date_time_default, widget='DateChooser')
    args = parser.parse_args()
    args.start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0,
                                                                             microsecond=0).isoformat()
    args.end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59,
                                                                         microsecond=999999).isoformat()
    print("Starting Date: %s" % args.start_date)
    print("Ending Date: %s" % args.end_date)

    ## Read configuration file
    config = configparser.ConfigParser()
    config.read("config.cfg")

    ## Get time from source application
    client = ClockifyTimeEntryProvider(config["Clockify"]["api_key"], config["Clockify"]["workspace_id"])
    work_records = client.get_work_records(args.start_date, args.end_date)

    ## Show user the work records retrived from source application
    total = 0
    for workRecord in work_records:
        total = total + workRecord.timeSpent
        print(workRecord.date, workRecord.workItemID, workRecord.timeSpent, workRecord.description)
    print("Total hours: ", round(total, 2))

    user_confirmed = get_user_confirmation()
    if user_confirmed:
        library_client = LibraryTimeEntryProvider(library_url=config['Library']['server_url'], user_name=args.user_name,
                                                  password=args.password)
        library_client.save_work_records(work_records)
        # print(library_client.getEnumOptionsFor("slnasolutionsarchitecturehub", "work-record-type"))
    else:
        print("Library Import Cancelled")


if __name__ == '__main__':
    main()
