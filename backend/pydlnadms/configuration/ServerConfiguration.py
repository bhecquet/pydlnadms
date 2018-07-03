'''
Created on 21 nov. 2013

@author: worm
'''
import os
import sys

from xml.etree import ElementTree as etree
from backend.pydlnadms.configuration.FolderConfiguration import FolderConfiguration

def fix_etree_to_string():
    '''Fix xml.etree.ElementTree.tostring for python < 3.2'''
    if sys.version_info.major >= 3 and sys.version_info.minor >= 2:
        return
    
    _etree_tostring_original = etree.tostring
    def _etree_tostring_wrapper(*args, **kwargs):
        if kwargs.get('encoding') == 'unicode':
            del kwargs['encoding']
        return _etree_tostring_original(*args, **kwargs)
    etree.tostring = _etree_tostring_wrapper

class ServerConfiguration(object):
    
    pidFile = None
    port = 1337
    modes = ['orderByTitle']
    loggingFileConf = None
    notifyInterval = 895
    mergedFolders = {}
    
    @classmethod
    def setConfiguration(cls, pidFile, port, modes, loggingFileConf, notifyInterval, pathConf):
        cls.pidFile = pidFile
        cls.port = port
        cls.modes = list(set(modes))
        cls.loggingFileConf = loggingFileConf
        cls.notifyInterval = notifyInterval 
        FolderConfiguration.readFolderConfiguration(pathConf)
