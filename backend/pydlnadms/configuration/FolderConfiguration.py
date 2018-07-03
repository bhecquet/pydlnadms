import os
import sys
import importlib

class ConfigurationException(Exception): pass

class FolderConfiguration(object):
    
    folders = []
    foldersToScan = []
    mergedFolders = {}
    
    @classmethod
    def readFolderConfiguration(cls, folderConf):
        """
        Read configuration file for folders
        It is in python format
        e.g:
        
        folders = [folder1, folder2]
        mergedFolders = {'mergedName': [folder1, folder2], }
        """
        
        if folderConf is None or not os.path.isfile(folderConf):
            raise ConfigurationException("file for folder %s configuration does not exist" % folderConf)
        
        sys.path.append(os.path.dirname(folderConf))
        
        try:
            folderConf = importlib.import_module(os.path.splitext(os.path.basename(folderConf))[0])
        except ImportError as e:
            raise ConfigurationException("file %s cannot be imported %s" % (folderConf, e))
        
        if not hasattr(folderConf, "folders"):
            raise ConfigurationException("configuration file must contain 'folder' variable as a list")
        
        cls.folders = folderConf.folders
        cls.foldersToScan = cls.folders[:]
        
        if hasattr(folderConf, 'mergedFolders'):
            cls.mergedFolders = folderConf.mergedFolders
            
            # if some folders are not defined in folder list (as folder or subfolder), add them
            for mergedFolderName, folderList in folderConf.mergedFolders.items():
                
                for folder in folderList:
                    for f in cls.folders:
                        if folder.find(f) == -1:
                            cls.foldersToScan.append(folder)
                            break
                        
            
            