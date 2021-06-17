"""Time Entry Tool to import time records from Clockify to the Library"""

import configparser
from datetime import datetime, timedelta
import os.path
from typing import List

from gooey import Gooey, GooeyParser
import PySimpleGUI as sg

from time_entry_tools.clockify_task_sync_service import ClockifyTaskSyncService
from time_entry_tools.library_work_record_sync_service import LibraryWorkRecordSyncService
from time_entry_tools.clockify_time_entry_provider import ClockifyTimeEntryProvider
from time_entry_tools.library_time_entry_provider import LibraryTimeEntryProvider


def get_user_confirmation(prompt: str) -> bool:
    """Show GUI with prompt for user confirmation"""
    layout = [[sg.Text(prompt)],
              [sg.Button('Continue')],
              [sg.Button('Cancel')]]

    window = sg.Window(prompt, layout)
    event = window.read()[0]
    window.close()
    return event == 'Continue'


def get_previously_completed_dates() -> List[str]:
    """Get a list of dates the tool has already imported time entry.  Used to avoid duplication of time entry."""
    if not os.path.exists('completed_dates.txt'):
        return []
    with open('completed_dates.txt', 'r') as file:
        return file.read().splitlines()


def is_selected_date_range_already_complete(start_date: datetime, end_date: datetime) -> bool:
    """Verify the selected dates have not been selected for a past import."""
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range((end_date - start_date).days + 1)]
    completed_dates = get_previously_completed_dates()
    return any(date in completed_dates for date in dates)


def save_dates_as_completed(start_date: datetime, end_date: datetime) -> None:
    """Record the selected dates as completed."""
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range((end_date - start_date).days + 1)]
    with open('completed_dates.txt', 'a') as file:
        file.write('\n'.join(dates))
        file.write('\n')


# TODO Should add some version check/date built as a menu option
@Gooey(program_name="Time Entry Export/Import", auto_start=True, use_cmd_args=True, default_size=(610, 610),
       menu=[{'name': 'Help', 'items': [{
           'type': 'Link',
           'menuTitle': 'Documentation',
           'url': 'https://librarymanagement.swisslog.com/polarion/#/project/slnasolutionsarchitecturehub/wiki/Guides'
                  '/Setup%20Clockify%20Time%20Entry '
       }, {
           'type': 'MessageDialog',
           'menuTitle': 'Author',
           'caption': 'Author Information',
           'message': 'Kyle Frizzell'
       }]}])
def main():
    """Main Program"""
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
    parser.add_argument("-o", "--only_sync", help="Do not run time entry import, only sync tasks/projects",
                        default=False, action="store_true", widget='CheckBox')
    args = parser.parse_args()
    args.start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0,
                                                                             microsecond=0)
    args.end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59,
                                                                         microsecond=999999)
    print("Starting Date: %s" % args.start_date.isoformat(), flush=True)
    print("Ending Date: %s" % args.end_date.isoformat(), flush=True)

    # Read configuration file
    config = configparser.ConfigParser()
    config.read("config.cfg")

    clockify_client = ClockifyTimeEntryProvider(config["Clockify"]["api_key"], config["Clockify"]["workspace_id"])
    library_client = LibraryTimeEntryProvider(library_url=config['Library']['server_url'], user_name=args.user_name,
                                              password=args.password,
                                              library_workitem_query=config['Library']['workitem_query'])

    if args.only_sync:
        task_sync_service = ClockifyTaskSyncService(library_client, clockify_client)
        task_sync_service.sync()
        return

    if is_selected_date_range_already_complete(args.start_date, args.end_date):
        ignore_warning = get_user_confirmation(
            "WARNING: You have already exported today's time entry to the Library.  "
            "Clicking Continue may result in duplicated time entry for today.")
        if not ignore_warning:
            return

    work_record_sync_service = LibraryWorkRecordSyncService(library_client=library_client,
                                                            clockify_client=clockify_client,
                                                            start_date=args.start_date.isoformat(),
                                                            end_date=args.end_date.isoformat())

    # Show user the work records retrieved from source application
    work_record_sync_service.show_work_records_to_sync()

    user_confirmed = get_user_confirmation("Continue with Import to Library?")
    if user_confirmed:
        work_record_sync_service.sync()
        save_dates_as_completed(args.start_date, args.end_date)
    else:
        print("Library Import Cancelled")

    user_confirmed_sync = get_user_confirmation("Optional: Sync Active Tasks from Library to Clockify?")
    if user_confirmed_sync:
        task_sync_service = ClockifyTaskSyncService(library_client, clockify_client)
        task_sync_service.sync()
    else:
        print("Active Task Sync Cancelled")


if __name__ == '__main__':
    main()
