#!/usr/bin/env python3
import os
import logging
import sys
from backend.pydlnadms.configuration import Configuration
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pydlnadms_frontend.settings")

import django
django.setup()

from argparse import ArgumentParser
from backend.pydlnadms.configuration.ServerConfiguration import ServerConfiguration
from backend.pydlnadms.configuration.LoggerConfiguration import LoggerConfiguration
from backend.pydlnadms.fileManagement.FileTree import FileTree
from backend.pydlnadms.DigitalMediaServer import DigitalMediaServerPool
from pydlnadms_frontend.settings import HOME_DLNA_DIR
from frontend.models import Folders
import threading
from backend.pydlnadms.fileManagement.Tools import scanDirectories

class DlnaMainServer(threading.Thread):
    
    def __init__(self, *args, **kwds):
        super(DlnaMainServer, self).__init__(*args, **kwds)
    
    def main(self):
     
        parser = ArgumentParser(
            usage='prog [options]',
            description='Serves media from the given PATH over UPnP-AV and DLNA.')
        parser.add_argument(
            '-p', '--port', type=int, 
            default=1337,
            help='media server listen PORT')
        parser.add_argument(
            '-m', '--mode', 
            default=['orderByTitle'], action='append', choices=['orderByTitle', 'orderByDate', 'rescan'],
            help='ordering method, defaults to "orderByTitle", several modes can be used')
        parser.add_argument(
            '--pidfile',
            default = None,
            help='pid file')
        parser.add_argument(
            '--logging_conf', '--logging-conf',
            default = None,
            help='Path of Python logging configuration file')
        parser.add_argument(
            '--path_conf',
            default = None,
            help='Path to folder configuration file')
        parser.add_argument('--notify-interval', '-n', type=int, 
            default=895,
            help='time in seconds between server advertisements on the network')
    
        args = parser.parse_args()
        
        self.startServer(args.pidfile, args.port, args.mode, args.logging_conf, args.notify_interval, args.path_conf)
    
    def run(self):
        self.startServer()
    
    def startServer(self, pidfile="/var/run/pydlnadms.pid", port=1337, mode=['orderByTitle', 'orderByDate'], logging_conf=None, notify_interval=15, path_conf=HOME_DLNA_DIR + "/file_conf.py"):
        """
        Start server
        """
        
        Configuration.readConfig()
        
        # store input configuration
        ServerConfiguration.setConfiguration(pidfile, 
                                             port, 
                                             mode, 
                                             logging_conf, 
                                             notify_interval, 
                                             path_conf)
        
        # configure logging
        LoggerConfiguration.configureLogger()
        
        # build file list and scan for new files
        scanDirectories()
    
        # write pid file
        try:
            pidfile = open(ServerConfiguration.pidFile, 'w')
            pidfile.write(str(os.getpid()))
            pidfile.close()
        except:
            pass
    
        dmsPool = DigitalMediaServerPool()
        for i, mode in enumerate(ServerConfiguration.modes):
            dmsPool.addDMS(ServerConfiguration.port + i * 1000, 
                           notify_interval=ServerConfiguration.notifyInterval, 
                           mode=mode)
        dmsPool.start()

if __name__ == '__main__':
    server = DlnaMainServer()
    server.main()
