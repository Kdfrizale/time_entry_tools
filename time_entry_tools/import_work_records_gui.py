import configparser

import PySimpleGUI as sg
from gooey import Gooey, GooeyParser
from datetime import datetime, timedelta
import os.path

from time_entry_tools.ClockifyTaskSyncService import ClockifyTaskSyncService
from time_entry_tools.LibraryWorkRecordSyncService import LibraryWorkRecordSyncService
from time_entry_tools.clockify_time_entry_provider import ClockifyTimeEntryProvider
from time_entry_tools.library_time_entry_provider import LibraryTimeEntryProvider


def get_user_confirmation(prompt) -> bool:
    layout = [[sg.Text(prompt)],
              [sg.Button('Continue')],
              [sg.Button('Cancel')]]

    window = sg.Window(prompt, layout)
    event, values = window.read()
    window.close()
    return event == 'Continue'


def getPreviouslyCompletedDates():
    if not os.path.exists('completed_dates.txt'):
        return []
    with open('completed_dates.txt', 'r') as file:
        return file.read().splitlines()


def checkIfDatesHaveAlreadyBeenCompleted(start_date, end_date):
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range((end_date - start_date).days + 1)]
    completed_dates = getPreviouslyCompletedDates()
    return any(date in completed_dates for date in dates)


def saveDatesAsCompleted(start_date, end_date):
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range((end_date - start_date).days + 1)]
    with open('completed_dates.txt', 'a') as file:
        file.write('\n'.join(dates))
        file.write('\n')


@Gooey(program_name="Time Entry Export/Import", auto_start=True, use_cmd_args=True)
def main():
    # Parse Command-Line arguments
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
                                                                             microsecond=0)
    args.end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59,
                                                                         microsecond=999999)
    print("Starting Date: %s" % args.start_date.isoformat())
    print("Ending Date: %s" % args.end_date.isoformat())

    # Read configuration file
    config = configparser.ConfigParser()
    config.read("config.cfg")

    if checkIfDatesHaveAlreadyBeenCompleted(args.start_date, args.end_date):
        print("WARNING!.. A date in the selected Date Range has already been processed.  Continuing with this process might result in duplicated time entry.")
        ignore_warning = get_user_confirmation("WARNING: Selected date has already been processed.  Continuing with this process might result in duplicated time entry")
        if not ignore_warning:
            return

    clockify_client = ClockifyTimeEntryProvider(config["Clockify"]["api_key"], config["Clockify"]["workspace_id"])
    library_client = LibraryTimeEntryProvider(library_url=config['Library']['server_url'], user_name=args.user_name,
                                              password=args.password,
                                              library_workitem_query=config['Library']['workitem_query'])

    workRecordSyncService = LibraryWorkRecordSyncService(library_client=library_client, clockify_client=clockify_client,
                                                         start_date=args.start_date.isoformat(), end_date=args.end_date.isoformat())

    # Show user the work records retrieved from source application
    workRecordSyncService.showWorkRecordsToSync()

    user_confirmed = get_user_confirmation("Continue with Import to Library?")
    if user_confirmed:
        workRecordSyncService.sync()
        saveDatesAsCompleted(args.start_date, args.end_date)
    else:
        print("Library Import Cancelled")

    user_confirmed_sync = get_user_confirmation("Sync Active Tasks from Library to Clockify?")
    if user_confirmed_sync:
        taskSyncService = ClockifyTaskSyncService(library_client, clockify_client)
        taskSyncService.sync()
    else:
        print("Active Task Sync Cancelled")


if __name__ == '__main__':
    main()
