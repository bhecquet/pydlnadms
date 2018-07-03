
import random
import threading
from backend.pydlnadms.configuration.FolderConfiguration import FolderConfiguration
from backend.pydlnadms.server import HTTPServer, UPNP_ROOT_DEVICE
from backend.pydlnadms.services import SERVICE_LIST
from backend.pydlnadms.ssdp import SSDPAdvertiser, SSDPResponder
from backend.pydlnadms.device import make_device_desc, ROOT_DEVICE_DEVICE_TYPE,\
    ROOT_DEVICE_NAME
import logging
import hashlib

MODE_NAMES = {
              'orderByTitle': 'Par nom',
              'orderByDate': 'Par date',
              'delete': 'SUPPRESSION',
              'rescan': 'Rescan'
              }


# TODO this could probably have named param to set the logger
def exception_logging_decorator(func):
    '''Log exceptions and reraise them.'''
    def callable():
        try:
            return func()
        except:
            logging.exception('Exception in thread %r:', threading.current_thread())
            raise
    return callable

class DigitalMediaServerPool(object):
    
    def __init__(self):
        self.stopped = threading.Event()
        self.dmsList = []
        
    def stop(self):
        self.stopped.set()
        
    def addDMS(self, port, notify_interval, mode):
        self.dmsList.append(DigitalMediaServer(port, notify_interval, mode))
        
    def start(self):
        for dms in self.dmsList:
            dms.run()
        self.stopped.wait()
        

class DigitalMediaServer(object):

    def __init__(self, port, notify_interval, mode):

        ROOT_DEVICE_FRIENDLY_NAME = ROOT_DEVICE_NAME + MODE_NAMES.get(mode, 'UNKNOWN')
        
        # use a hash of the friendly name (should be unique enough)
        self.device_uuid = 'uuid:4d696e69-444c-164e-9d41-{}{}'.format(
            hashlib.sha224(ROOT_DEVICE_FRIENDLY_NAME.encode('utf-8')).hexdigest()[-8:], port)
        logging.info('DMS UUID is %r', self.device_uuid)
        self.notify_interval = notify_interval
        self.mode = mode
        self.device_desc = make_device_desc(self.device_uuid, MODE_NAMES.get(mode, 'UNKNOWN'))
        self.http_server = HTTPServer(port, self)
        self.ssdp_advertiser = SSDPAdvertiser(self)
        self.ssdp_responder = SSDPResponder(self)
        self.stopped = threading.Event()

    def run_daemon(self, target):
        try:
            target()
        finally:
            self.stop()

    def stop(self):
        self.stopped.set()

    def run(self):
        for runnable in [self.http_server, self.ssdp_advertiser, self.ssdp_responder]:
            thread = threading.Thread(
                target=self.run_daemon,
                args=[exception_logging_decorator(runnable.run)],
                name=runnable.__class__.__name__)
            thread.daemon = True
            thread.start()

    @property
    def all_targets(self):
        yield self.device_uuid
        yield UPNP_ROOT_DEVICE
        yield ROOT_DEVICE_DEVICE_TYPE
        for service in SERVICE_LIST:
            yield service.serviceType

    def usn_from_target(self, target):
        if target == self.device_uuid:
            return target
        else:
            return self.device_uuid + '::' + target
