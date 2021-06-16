"""Library specific Time Entry Provider"""
import ssl
from requests import Session
from requests.adapters import HTTPAdapter
from zeep.plugins import HistoryPlugin
from zeep import Client, Transport

from time_entry_tools.workrecord import round_hours_for_library
from time_entry_tools.time_entry_provider import TimeEntryProvider


class SslContextHttpAdapter(HTTPAdapter):
    """Transport adapter that allows us to use system-provided SSL
    certificates."""

    def init_poolmanager(self, *args, **kwargs):
        ssl_context = ssl.create_default_context()
        ssl_context.load_default_certs()
        kwargs['ssl_context'] = ssl_context
        return super(SslContextHttpAdapter, self).init_poolmanager(*args, **kwargs)


class Polarion:
    """SOAP Accessor class to Polarion"""
    def __init__(self, url, username, password, library_workitem_query):
        self.url = url
        self.username = username
        self.password = password
        self.library_workitem_query = library_workitem_query
        self.history = HistoryPlugin()

        tmp_session = Session()
        tmp_adapter = SslContextHttpAdapter()
        tmp_session.mount("https://librarymanagement.swisslog.com/", tmp_adapter)
        tmp_transport = Transport(session=tmp_session)

        self.session = Client(wsdl=self.url + '/ws/services/SessionWebService?wsdl', plugins=[self.history],
                              transport=tmp_transport)
        self.session.service.logIn(self.username, self.password)
        tree = self.history.last_received['envelope'].getroottree()
        self.session_header_element = tree.find('.//{http://ws.polarion.com/session}sessionID')

        self.__tracker = Client(wsdl=self.url + '/ws/services/TrackerWebService?wsdl', plugins=[self.history],
                                transport=tmp_transport)
        self.__tracker.set_default_soapheaders([self.session_header_element])
        self.__tracker.wsdl.messages['{http://ws.polarion.com/TrackerWebService}getModuleWorkItemsRequest'].parts[
            'parameters'].element.type._element[1].nillable = True
        self.__tracker.service.getModuleWorkItemUris._proxy._binding.get(
            'getModuleWorkItemUris').input.body.type._element[1].nillable = True
        self.__tracker.service.getModuleWorkItemUris._proxy._binding.get('getModuleWorkItems').input.body.type._element[
            1].nillable = True

        self.__project_service = Client(wsdl=self.url + '/ws/services/ProjectWebService?wsdl', plugins=[self.history],
                                        transport=tmp_transport)
        self.__project_service.set_default_soapheaders([self.session_header_element])

    @property
    def tracker(self):
        """SOAP Client to the Library Tracker Service"""
        return self.__tracker

    @property
    def project_service(self):
        """SOAP Client to the Library Project Service"""
        return self.__project_service

    def get_user(self, user_id):
        """Query the Library to get the User's Information"""
        return self.project_service.service.getUser(user_id)

    def get_workitem_by_id(self, work_item_id):
        """Query the Library to get a single Work Item with the selected ID"""
        return self.tracker.service.queryWorkItems('id:%s' % work_item_id, 'id',
                                                   ['id', 'title', 'description', 'linkedWorkItems'])[0]

    def get_workitems_for_user(self, user_id):
        """Query the Library to get all work items assigned to the user and matching the configurable query"""
        query = self.library_workitem_query + f" AND assignee.id:{user_id}"
        return self.tracker.service.queryWorkItems(query, 'id', ['id', 'title', 'project'])

    def get_workitems_with_ids(self, work_item_ids):
        """Query the Library to get all work items with the selected IDs"""
        return self.tracker.service.queryWorkItems('id:(%s)' % " ".join(work_item_ids), 'id',
                                                   ['id', 'title', 'project'])

    def add_work_record(self, work_item_uri, user, date, time_spent):
        """Send request to libray to add a work record to a work item"""
        return self.tracker.service.createWorkRecord(work_item_uri, user, date, time_spent)

    def add_work_record_with_comment(self, work_item_uri, user, date, time_spent, enum_type, comment):
        """Send request to libray to add a work record to a work item"""
        return self.tracker.service.createWorkRecordWithTypeAndComment(work_item_uri, user, date, enum_type, time_spent,
                                                                       comment)

    def get_all_enum_option_ids_for_id(self, project_id, enum_id):
        """Query the Library to get the possible IDs for a selected enum"""
        return self.tracker.service.getAllEnumOptionIdsForId(project_id, enum_id)


class LibraryTimeEntryProvider(TimeEntryProvider):
    """Library specific Time Entry Provider"""

    def __init__(self, library_url: str, user_name: str, password: str, library_workitem_query: str):
        self.library_url = library_url
        self.user_name = user_name
        self.password = password
        self.library_workitem_query = library_workitem_query
        self.polarion = Polarion(library_url, user_name, password, library_workitem_query)

    def get_enum_options_for_enum(self, project_id, enum_id):
        """Get the possible IDs for a selected library enum"""
        return self.polarion.get_all_enum_option_ids_for_id(project_id, enum_id)

    def get_workitems_for_user(self):
        """Get workItems for the library user using the configured query"""
        return self.polarion.get_workitems_for_user(self.user_name)

    def get_workitems_with_ids(self, workitem_ids):
        """Get WorkItems with the specified IDs"""
        return self.polarion.get_workitems_with_ids(workitem_ids)

    def save_work_records(self, work_records: list):
        """Save a list of WorkRecords to the Library"""
        ## Get User object from library
        user = self.polarion.get_user(self.user_name)
        for work_record in work_records:  ##TODO could paralleize this as each request has to wait for connection/response to the library, meaning it takes awhile (15sec) to do a week's worth of time entry
            print("Saving work record in Library.  WorkItem: %s, Date:%s, TimeSpent: %s, Comment: %s" % (
                work_record.work_item_id, work_record.date, round_hours_for_library(work_record.time_spent),
                work_record.description), flush=True)
            ## Get WorkItemURI
            work_item_uri = None
            work_item_uri = self.polarion.get_workitem_by_id(work_record.work_item_id).uri
            ## Add work record to workItem
            temp_enum = {
                'id': 'admin'}  ##TODO find a good way to set this enum in clockify or lookup a default in the library project space
            self.polarion.add_work_record_with_comment(work_item_uri, user, work_record.date,
                                                       round_hours_for_library(work_record.time_spent), temp_enum,
                                                       work_record.description)

    def get_work_records(self, start_date: str, end_date: str):
        raise NotImplementedError
