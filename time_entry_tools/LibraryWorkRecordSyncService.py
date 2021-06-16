class LibraryWorkRecordSyncService():
    def __init__(self, library_client, clockify_client, start_date, end_date):
        self._library_client = library_client
        self._clockify_client = clockify_client
        self.start_date = start_date
        self.end_date = end_date
        self.work_records = self._clockify_client.get_work_records(self.start_date, self.end_date)

    def sync(self):
        """Sync workRecords from Clockify to the Libray"""
        self._library_client.save_work_records(self.work_records)

    def showWorkRecordsToSync(self):
        """Show the user what WorkRecords were selected for import to the Library"""
        for workRecord in self.work_records:
            print(f"WorkRecord Date: {workRecord.date} | WorkItem: {workRecord.workItemID} | Timespent: {workRecord.timeSpent} | Description: {workRecord.description}")
        total = sum([workRecord.timeSpent for workRecord in self.work_records])
        print("Total hours: ", round(total, 2), flush=True)
