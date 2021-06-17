"""Service to sync work records from Clockify to the Library"""


class LibraryWorkRecordSyncService:
    """Service to sync work records from Clockify to the Library"""
    def __init__(self, library_client, clockify_client, start_date, end_date):
        self._library_client = library_client
        self._clockify_client = clockify_client
        self.start_date = start_date
        self.end_date = end_date
        self.work_records = self._clockify_client.get_work_records(self.start_date, self.end_date)

    def sync(self) -> None:
        """Sync workRecords from Clockify to the Libray"""
        self._library_client.save_work_records(self.work_records)

    def show_work_records_to_sync(self) -> None:
        """Show the user what WorkRecords were selected for import to the Library"""
        for work_record in self.work_records:
            print(
                f"WorkRecord Date: {work_record.date} | WorkItem: {work_record.work_item_id} | Timespent: {work_record.time_spent} | Description: {work_record.description}")
        total = sum([work_record.time_spent for work_record in self.work_records])
        print("Total hours: ", round(total, 2), flush=True)
