from xml.etree import cElementTree as etree
from xml.sax.saxutils import escape as xml_escape
from operator import attrgetter
from backend.pydlnadms.soap import didl_lite
import collections
import itertools
import logging
import os
import pprint
import urllib.parse
import time

from backend._misc.mount import MountUtility

from backend.movieDb.movieDb import MovieDb
from backend.pydlnadms.fileManagement.Scanner import Scanner
from backend.pydlnadms.fileManagement.Tools import guessMimetype,\
    scanDirectories
from backend.pydlnadms.fileManagement.FileTree import FileTree
from backend.pydlnadms.fileManagement.VFile import VFile
from backend.pydlnadms.configuration.constants import DELETE_PATTERN
from backend.pydlnadms.fileManagement.VDirectory import VDirectory
from backend.pydlnadms.device import DEVICE_DESC_SERVICE_FIELDS
from backend.pydlnadms.dlna import DLNAContentFeatures
import datetime
from pydlnadms_frontend.settings import HOME_DLNA_DIR




Service = collections.namedtuple(
    'Service',
    DEVICE_DESC_SERVICE_FIELDS + ('xmlDescription',))
File = collections.namedtuple('File', ['name', 'virtualName', 'path', 'creationDate'])
Entry = collections.namedtuple('Entry', ['path', 'transcode', 'title', 'vFile'])

SYSTEM_UPDATE_ID_FILE = 'systemUpdateId'

def make_xml_service_description(actions, statevars):
    from xml.etree.cElementTree import Element, tostring, SubElement
    scpd = Element('scpd', xmlns='urn:schemas-upnp-org:service-1-0')
    specVersion = SubElement(scpd, 'specVersion')
    SubElement(specVersion, 'major').text = '1'
    SubElement(specVersion, 'minor').text = '0'
    actionList = SubElement(scpd, 'actionList')
    for action in actions:
        action_elt = SubElement(actionList, 'action')
        SubElement(action_elt, 'name').text = action[0]
        argumentList = SubElement(action_elt, 'argumentList')
        for name, dir, var in action[1]:
            argument = SubElement(argumentList, 'argument')
            SubElement(argument, 'name').text = name
            SubElement(argument, 'direction').text = dir
            SubElement(argument, 'relatedStateVariable').text = var
    serviceStateTable = SubElement(scpd, 'serviceStateTable')
    for name, datatype, *rest in statevars:
        if name in ['TransferIDs', 'SystemUpdateID', 'SourceProtocolInfo', 'SinkProtocolInfo', 'CurrentConnectionIDs']:
            stateVariable = SubElement(serviceStateTable, 'stateVariable', sendEvents='yes')
        else:
            stateVariable = SubElement(serviceStateTable, 'stateVariable', sendEvents='no')
        SubElement(stateVariable, 'name').text = name
        SubElement(stateVariable, 'dataType').text = datatype
        if rest:
            assert len(rest) == 1
            allowedValueList = SubElement(stateVariable, 'allowedValueList')
            for av in rest[0]:
                SubElement(allowedValueList, 'allowedValue').text = av
    return b'<?xml version="1.0"?>\n' + tostring(scpd)#.encode('utf-8')

SERVICE_LIST = []
for service, domain, version, actions, statevars in [
            ('ContentDirectory', None, 1, [
                ('Browse', [
                    ('ObjectID', 'in', 'A_ARG_TYPE_ObjectID'),
                    ('BrowseFlag', 'in', 'A_ARG_TYPE_BrowseFlag'),
                    ('Filter', 'in', 'A_ARG_TYPE_Filter'),
                    ('StartingIndex', 'in', 'A_ARG_TYPE_Index'),
                    ('RequestedCount', 'in', 'A_ARG_TYPE_Count'),
                    ('SortCriteria', 'in', 'A_ARG_TYPE_SortCriteria'),
                    ('Result', 'out', 'A_ARG_TYPE_Result'),
                    ('NumberReturned', 'out', 'A_ARG_TYPE_Count'),
                    ('TotalMatches', 'out', 'A_ARG_TYPE_Count'),
                    ('UpdateID', 'out', 'A_ARG_TYPE_UpdateID'),
                    ]),
                ('GetSystemUpdateID', [('Id', 'out', 'SystemUpdateID')]),
                ('GetSearchCapabilities', [('SearchCaps', 'out', 'SearchCapabilities')]),
                ('GetSortCapabilities', [('SortCaps', 'out', 'SortCapabilities')]),
                ], [
                ('A_ARG_TYPE_ObjectID', 'string'),
                ('A_ARG_TYPE_Result', 'string'),
                ('A_ARG_TYPE_BrowseFlag', 'string', [
                    'BrowseMetadata', 
                    'BrowseDirectChildren']),
                ('A_ARG_TYPE_Index', 'ui4'),
                ('A_ARG_TYPE_Count', 'ui4'),
                ('TransferIDs', 'string'),
                ('A_ARG_TYPE_Filter', 'string'),
                ('A_ARG_TYPE_SearchCriteria', 'string'),
                ('A_ARG_TYPE_SortCriteria', 'string'),
                ('SearchCapabilities', 'string'),
                ('SortCapabilities', 'string'),
                ('SystemUpdateID', 'ui4'),
                ('A_ARG_TYPE_UpdateID', 'ui4'),
                
                ]),
            ('ConnectionManager', None, 1,
                [('GetProtocolInfo', [
                    ('Source', 'out', 'SourceProtocolInfo'),
                    ('Sink', 'out', 'SinkProtocolInfo'),
                   ]),
                 ('GetCurrentConnectionIDs', [
                    ('ConnectionIDs', 'out', 'CurrentConnectionIDs')
                   ]),
                 ('GetCurrentConnectionInfo', [
                    ('ConnectionID', 'in', 'A_ARG_TYPE_ConnectionID'),
                    ('RcsID', 'out', 'A_ARG_TYPE_RcsID'),
                    ('AVTransportID', 'out', 'A_ARG_TYPE_AVTransportID'),
                    ('ProtocolInfo', 'out', 'A_ARG_TYPE_ProtocolInfo'),
                    ('PeerConnectionManager', 'out', 'A_ARG_TYPE_ConnectionManager'),
                    ('PeerConnectionID', 'out', 'A_ARG_TYPE_ConnectionID'),
                    ('Direction', 'out', 'A_ARG_TYPE_Direction'),
                    ('Status', 'out', 'A_ARG_TYPE_ConnectionStatus'),
                   ]) 
                 ],  # actions
                [('SourceProtocolInfo', 'string'),
                 ('SinkProtocolInfo', 'string'),
                 ('CurrentConnectionIDs', 'string'),
                 ('A_ARG_TYPE_ConnectionStatus', 'string', ['OK', 'ContentFormatMismatch', 'InsufficientBandwidth', 'UnreliableChannel', 'Unknown']),
                 ('A_ARG_TYPE_ConnectionManager', 'string'),
                 ('A_ARG_TYPE_Direction', 'string', ['Input', 'Output']),
                 ('A_ARG_TYPE_ProtocolInfo', 'string'),
                 ('A_ARG_TYPE_ConnectionID', 'i4'),
                 ('A_ARG_TYPE_AVTransportID', 'i4'),
                 ('A_ARG_TYPE_RcsID', 'i4'),
                 ]),                        # statevars
#            ('X_MS_MediaReceiverRegistrar', 'microsoft.com', 1, (), ()),
        ]:
    SERVICE_LIST.append(Service(
        serviceType='urn:{}:service:{}:{}'.format(
            'schemas-upnp-org' if domain is None else domain,
            service, version),
        serviceId='urn:{}:serviceId:{}'.format(
            'upnp-org' if domain is None else domain, service),
        SCPDURL='/'+service+'.xml',
        controlURL='/ctl/'+service,
        eventSubURL='/evt/'+service,
        xmlDescription=make_xml_service_description(actions, statevars)))

import concurrent.futures
thread_pool = concurrent.futures.ThreadPoolExecutor(20)

from backend._misc.ffprobe import res_data


def readSystemUpdateId():
    if not os.path.isfile(HOME_DLNA_DIR + SYSTEM_UPDATE_ID_FILE):
        with open(HOME_DLNA_DIR + SYSTEM_UPDATE_ID_FILE, 'w') as sysFile:
            sysFile.write('0')
            return 0
    
    else:
        with open(HOME_DLNA_DIR + SYSTEM_UPDATE_ID_FILE, 'r') as sysFile:
            return int(sysFile.read())
        
def incrementSystemUpdateId():
    ContentDirectoryService.updateId = (ContentDirectoryService.updateId + 1) % 255
    with open(HOME_DLNA_DIR + SYSTEM_UPDATE_ID_FILE, 'w') as sysFile:
        sysFile.write(str(ContentDirectoryService.updateId))


class ContentDirectoryService(object):
    
    

    # lit le UpdateId original
    updateId = readSystemUpdateId()
    res_data = staticmethod(res_data)

    def __init__(self, res_scheme, res_netloc, res_path, res_mode):
        self.res_scheme = res_scheme
        self.res_netloc = res_netloc
        self.res_path = res_path
        self.res_mode = res_mode
        self.movieDb = MovieDb(False)
        
    def list_dlna_dir(self, vPath):
        '''
        Yields entries to be shown for the given path with the metadata obtained while processing them.
        @param vPath: virtual path (VDirectory or VFile
        '''
        files = []
        entries = []
        
        # in case of a file
        if isinstance(vPath, VFile):
            return entries
            
        # in case of a directory
        else:
            for vFile in vPath.fileList:
                
                movieName = os.path.splitext(vFile.name)[0]
                isDeletable = self.movieDb.movieIsDeletable(movieName)
      
                # the movie does not exist in DB
                if not isDeletable:
                    files.append(vFile)

            # sort folders
            if self.res_mode in ['orderByTitle', 'delete', 'rescan']:
                sorter = 'name'
            elif self.res_mode == 'orderByDate':
                sorter = 'creationDate'
            for d in sorted(vPath.dirList, key=attrgetter(sorter)):
                entries.append(Entry(d.path, False, d.name, d))
            
            # this wants yield from itertools.chain.from_iterable... PEP 380
            if self.res_mode == 'orderByTitle':
                for file in sorted(files, key=attrgetter('name')):
                    if file.name.startswith('.'):
                        continue
                    entries.append(Entry(file.path, False, file.name, file))
            elif self.res_mode == 'delete':
                for file in sorted(files, key=attrgetter('name')):
                    if file.name.startswith('.'):
                        continue
                    entries.append(Entry(file.path, False, file.name + ' delete', file))
            elif self.res_mode == 'orderByDate':
                for file in sorted(files, key=attrgetter('creationDate')):
                    if file.name.startswith('.'):
                        continue
                    entries.append(Entry(file.path, False, file.name, file))
                        
        return entries
    
    def _update_element_xml(self, element, isdir, cdentry):
        """
        Update the element XML
        """
        
        if isdir:
            mimetype        = guessMimetype(cdentry.vFile.path)
        else:
            mimetype        = guessMimetype(cdentry.vFile.realPath)
        
        # video res element
        content_features = DLNAContentFeatures()
        content_features.support_time_seek = True
        content_features.support_range = True
            
        res_elt = etree.SubElement(element, 'res',
            protocolInfo='http-get:*:{}:{}'.format(
                '*' if isdir else 'video/mpeg' if cdentry.transcode else mimetype,
                content_features))
        
        if isdir:
            resourcePath = cdentry.path
        else:
            resourcePath = cdentry.vFile.realPath 
        res_elt.text = urllib.parse.urlunsplit((
            self.res_scheme,
            self.res_netloc,
            self.res_path,
            urllib.parse.urlencode([('path', resourcePath)] + ([('transcode', '1')] if cdentry.transcode else [])),
            None))
        
        # set file properties        
        if not isdir:
            
            if cdentry.vFile.dbFile:
                fileProperties = Scanner.getFilePropertiesById(cdentry.vFile.dbFile)
            else:
                fileProperties = {'bitrate': 0, 'duration': datetime.timedelta(seconds=float(0))}
            for attr, value in fileProperties.items():
                res_elt.set(attr, str(value))
                
            res_elt.set('size', str(os.path.getsize(cdentry.vFile.realPath)))

        return etree.tostring(element, encoding='unicode')
        
                        
    def object_xml(self, parent_id, cdentry):
        '''Returns XML describing a UPNP object'''

        path            = cdentry.path
        title           = cdentry.title        
        isdir           = isinstance(cdentry.vFile, VDirectory)
        
        if isdir:
            mimetype        = guessMimetype(cdentry.vFile.path)
        else:
            mimetype        = guessMimetype(cdentry.vFile.realPath)
            
        type, subtype = mimetype.split('/')

        # a directory in file system
        if isdir and path.find(DELETE_PATTERN) == -1:
            element = etree.Element('container', id=path, parentID=parent_id, restricted='1')
            element.set('childCount', str(sum(1 for _ in self.list_dlna_dir(cdentry.vFile))))
            thumbnailFile = cdentry.vFile.thumbnail
      
        # the DELETE option is seen as a directory so that a link to parent can be made
        elif path.find(DELETE_PATTERN) > -1:
            element = etree.Element('container', id=path, parentID=parent_id, restricted='1')
            element.set('childCount', '1')
            isdir = True
            thumbnailFile = None
            
        else:
            element = etree.Element('item', id=path, parentID=parent_id, restricted='1')
            thumbnailFile = cdentry.vFile.thumbnail
            
        etree.SubElement(element, 'dc:title').text = title
        if not isdir:
            etree.SubElement(element, 'dc:date').text = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(os.stat(cdentry.vFile.realPath).st_ctime))
        
        class_elt = etree.SubElement(element, 'upnp:class')
        if isdir:
            class_elt.text = 'object.container'
        else:
            class_elt.text = 'object.item.{type}Item'.format(**vars())
            
        if thumbnailFile is not None:
            # upnp:icon doesn't seem to work anyway, see the image/* res tag
            etree.SubElement(element, 'upnp:icon').text = urllib.parse.urlunsplit((
                self.res_scheme,
                self.res_netloc,
                self.res_path,
                urllib.parse.urlencode({'path': thumbnailFile}),
                None))
            etree.SubElement(element, 'upnp:albumArtURI').text = urllib.parse.urlunsplit((
                self.res_scheme,
                self.res_netloc,
                self.res_path,
                urllib.parse.urlencode({'path': thumbnailFile}),
                None))
            
            # element for icon
            icon_res_element = etree.SubElement(
                element,
                'res',
                protocolInfo='http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_TN;DLNA.ORG_OP=00;DLNA.ORG_CI=1;DLNA.ORG_FLAGS=00D00000000000000000000000000000" resolution="128x128"')
            icon_res_element.text = urllib.parse.urlunsplit((
                self.res_scheme,
                self.res_netloc,
                self.res_path,
                urllib.parse.urlencode({'path': thumbnailFile}),
                None))
        
        return self._update_element_xml(element, isdir, cdentry)
  
    def object_metadata_xml(self, parent, cdentry):
        '''Returns XML describing a UPNP object'''
        isdir           = isinstance(cdentry.vFile, VDirectory)
        if isdir:
            mimetype        = guessMimetype(cdentry.vFile.path)
        else:
            mimetype        = guessMimetype(cdentry.vFile.realPath)
            
        type, subtype = mimetype.split('/')

        # a real directory in file system
        element = etree.Element('item', id=self.path_to_object_id(cdentry.vFile), parentID=self.getParentId(parent), restricted='1')
        etree.SubElement(element, 'dc:title').text = cdentry.title
        if not isdir:
            etree.SubElement(element, 'dc:date').text = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(os.stat(cdentry.vFile.realPath).st_ctime))
        
        class_elt = etree.SubElement(element, 'upnp:class')
        if isdir:
            class_elt.text = 'object.container.storageFolder'
        else:
            class_elt.text = 'object.item.{type}Item'.format(**vars())
            
        return self._update_element_xml(element, isdir, cdentry)
    
    def getParentId(self, parent):
        if parent is None:
            return '-1'
        else:
            return parent.path

    def path_to_object_id(self, vFile):
        if vFile.parent:
            return vFile.path
        else:
            return '0'

    def object_id_to_path(self, object_id):
        if object_id == '0':
            oid = '/'
        else:
            oid = object_id
        MountUtility.checkMount(oid)
        
        # add rescan action in rescan mode
        if self.res_mode == 'rescan':
            oid += '?rescan=1'
        
        return oid
    
    def doAction(self, path):
        """
        Extract actions from the path
        path looks like /home/worm/Videos/?delete=2 (action is delete id 2)
        """
        parseResult = urllib.parse.urlparse(path)
        actionsRequest = parseResult.query.split('&')
        
        for actionRequest in actionsRequest:
            
            try:
                action, value = actionRequest.split('=')
            except:
                break
            
            # delete the file pointed by value (the id in DB)
            if action == 'delete':
                self.movieDb.db.updateDeletableFlag(int(value), int(time.time()))
            elif action == 'rescan':
                scanDirectories()
               
        # return the path without actions
        return parseResult.path
            

    def Browse(self, BrowseFlag, StartingIndex, RequestedCount, ObjectID,
            Filter=None, SortCriteria=None):
        RequestedCount = int(RequestedCount)
        path = self.object_id_to_path(ObjectID)
        
        if BrowseFlag == 'BrowseDirectChildren':
            
            # do some actions in case URL contains any action
            path = self.doAction(path)
            
            # get the current virtual file or directory
            vDirectory = FileTree.getInstance(path)[1]
            
            # in case the instance cannot be found, state there are non children
            # do not search for files if we try to rescan
            if vDirectory and self.res_mode != 'rescan':
                children = self.list_dlna_dir(vDirectory)
            else:
                children = []
            start = int(StartingIndex)
            stop = (start + RequestedCount) if RequestedCount else None
            
            result_elements = list(thread_pool.map(
                self.object_xml,
                itertools.repeat(ObjectID),
                children[start:stop]))
            
            total_matches = len(children)
            number_returned = len(result_elements)
            addDict = {'UpdateID': str(self.updateId)}
        
        elif BrowseFlag == 'BrowseMetadata':
            
            # get virtual file/directory associated to this path
            vFile = FileTree.getInstance(path)[1]
            cdentry = Entry(path=path, transcode=False, title=vFile.name, vFile=vFile)
    
            result_elements = self.object_metadata_xml(vFile.getParent(), cdentry)
            total_matches = 1
            number_returned = 1
            
            addDict = {'UpdateID': str(self.updateId)}
            
        else: # TODO check other flags
            parent_id = self.path_to_object_id(os.path.normpath(os.path.split(path)[0]))
            result_elements = [self.object_xml(parent_id, path, '??ROOT??', None)]
            total_matches = 1
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug(
                'ContentDirectory::Browse result:\n%s',
                pprint.pformat(result_elements))
        
        reply = {'Result': xml_escape(didl_lite(''.join(result_elements))),
                 'NumberReturned': number_returned,
                 'TotalMatches': total_matches
                 }
        reply.update(addDict)
        
        return reply
