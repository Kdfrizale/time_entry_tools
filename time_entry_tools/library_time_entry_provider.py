from time_entry_tools.time_entry_provider import TimeEntryProvider
from zeep import Client
from zeep.plugins import HistoryPlugin

from time_entry_tools.workrecord import round_hours_for_library


class Polarion(object):
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

        self.history = HistoryPlugin()
        self.session = Client(wsdl=self.url + '/ws/services/SessionWebService?wsdl', plugins=[self.history])
        self.session.service.logIn(self.username, self.password)
        tree = self.history.last_received['envelope'].getroottree()
        self.sessionHeaderElement = tree.find('.//{http://ws.polarion.com/session}sessionID')

        self.__tracker = Client(wsdl=self.url + '/ws/services/TrackerWebService?wsdl', plugins=[self.history])
        self.__tracker.set_default_soapheaders([self.sessionHeaderElement])
        self.__tracker.wsdl.messages['{http://ws.polarion.com/TrackerWebService}getModuleWorkItemsRequest'].parts[
            'parameters'].element.type._element[1].nillable = True
        self.__tracker.service.getModuleWorkItemUris._proxy._binding.get(
            'getModuleWorkItemUris').input.body.type._element[1].nillable = True
        self.__tracker.service.getModuleWorkItemUris._proxy._binding.get('getModuleWorkItems').input.body.type._element[
            1].nillable = True

        self.__projectService = Client(wsdl=self.url + '/ws/services/ProjectWebService?wsdl', plugins=[self.history])
        self.__projectService.set_default_soapheaders([self.sessionHeaderElement])

    @property
    def tracker(self):
        return self.__tracker

    @property
    def projectService(self):
        return self.__projectService

    def get_user(self, user_id):
        return self.projectService.service.getUser(user_id)

    def get_workitem_by_id(self, work_item_id):
        return self.tracker.service.queryWorkItems('id:%s' % work_item_id, 'id',
                                                   ['id', 'title', 'description', 'linkedWorkItems'])[0]

    def get_workitems_for_user(self, user_id):
        return self.tracker.service.queryWorkItems('NOT HAS_VALUE:resolution AND type:(task improvement) AND assignee.id:%s' % user_id, 'id', ['id', 'title', 'project'])

    def add_work_record(self, workItemURI, user, date, timeSpent):
        return self.tracker.service.createWorkRecord(workItemURI, user, date, timeSpent)

    def add_work_record_with_comment(self, workItemURI, user, date, timeSpent, enumType, comment):
        return self.tracker.service.createWorkRecordWithTypeAndComment(workItemURI, user, date, enumType, timeSpent,
                                                                       comment)

    def get_all_enum_option_ids_for_id(self, projectID, enumId):
        return self.tracker.service.getAllEnumOptionIdsForId(projectID, enumId)


class LibraryTimeEntryProvider(TimeEntryProvider):
    def __init__(self, library_url: str, user_name: str, password: str):
        self.library_url = library_url
        self.user_name = user_name
        self.password = password
        self.polarion = Polarion(library_url, user_name, password)

    def get_enum_options_for_enum(self, projectId, enumId):
        return self.polarion.get_all_enum_option_ids_for_id(projectId, enumId)

    def get_workItems_for_User(self):
        return self.polarion.get_workitems_for_user(self.user_name)

    def save_work_records(self, work_records: list):
        ## Get User object from library
        user = self.polarion.get_user(self.user_name)
        for work_record in work_records:  ##TODO could paralleize this as each request has to wait for connection/response to the library, meaning it takes awhile (15sec) to do a week's worth of time entry
            print("Saving work record in Library.  WorkItem: %s, Date:%s, TimeSpent: %s, Comment: %s" % (
                work_record.workItemID, work_record.date, round_hours_for_library(work_record.timeSpent),
                work_record.description))
            ## Get WorkItemURI
            workItemURI = None
            workItemURI = self.polarion.get_workitem_by_id(work_record.workItemID).uri
            ## Add work record to workItem
            temp_enum = {
                'id': 'admin'}  ##TODO find a good way to set this enum in clockify or lookup a default in the library project space
            self.polarion.add_work_record_with_comment(workItemURI, user, work_record.date,
                                                       round_hours_for_library(work_record.timeSpent), temp_enum,
                                                       work_record.description)

    def get_work_records(self, stateDate: str, endDate: str):
        raise NotImplementedError
