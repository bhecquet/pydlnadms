import logging
import os
import subprocess
import re
import datetime
import time

from backend.movieDb.db import db
from backend._misc.ffprobe import res_data
from backend.movieDb.movieDb import MovieDb
from backend.pydlnadms.configuration.constants import DELETE_AFTER, MOVIE_EXT
from backend._misc.mount import MountUtility
import threading

from backend.pydlnadms.configuration.FolderConfiguration import FolderConfiguration
from backend.pydlnadms.fileManagement.VFile import VFile
from backend.pydlnadms.fileManagement.FileTree import FileTree
from backend.pydlnadms.fileManagement.VDirectory import VDirectory
from backend.pydlnadms.server import getServerActive
from common.Logger import getLogger
from frontend.models import Folders
from backend.pydlnadms.configuration.Configuration import config

class FileInfoError(Exception): pass

class Scanner(threading.Thread):
    """
    Scan a folder list
    """   
    db = db()
    logger = getLogger("Scanner")
    _scannerLock = False # real threading.Lock not used. Unalbe to make it block
    
    def __init__(self, folderList=[]):
        if not folderList:
            folderList = FolderConfiguration.foldersToScan
        super(Scanner, self).__init__()
        self.folderList = folderList
        self.movieDb = MovieDb()
       
    def run(self):
        self.logger.info("scanner started")
        Scanner._scannerLock = True
        for folder in self.folderList:
            MountUtility.mountRootFolders(folder)
        self.scan()
        self.scanForDeletable()
        self.removeDeletedFiles()
        
        # if the server has not been used for playing, we can unmount
        if not getServerActive():
            for folder in self.folderList:
                MountUtility.umountRootFolders(folder)
                
        self.logger.info("scanner finished")
        Scanner._scannerLock = False
         
        
    def getBitrate(self, path):
        if os.path.splitext(path)[1] in ['.ts', '.mkv', '.mp4', '.avi']:
            out, err = subprocess.Popen([config['ffmpeg.directory'] + os.sep + 'ffmpeg', '-i', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            bitrate = int(re.compile('bitrate: (\d+) kb/s').findall(str(err))[0])
            return bitrate * 1000 / 8.
    
        else:
            return 1
        
    def scan(self):
        """
        (re)scan all defined folders
        """
        
        def scanFolder(parent):
            
            for vDir in parent.dirList:
                
                if not vDir.name.startswith(FileTree.DELETE_FILE):
                    scanFolder(vDir)
            for vFile in parent.fileList:
                if os.path.splitext(vFile.name)[1].lower() in MOVIE_EXT and not vFile.name.startswith(FileTree.SYNOPSIS_FILE):
                    
                    # in case of a special folder (eg: for movie), we do not use the full path, but the path in file system
                    if vFile.parent.folderType == VDirectory.FOLDER_TYPE_VIDEO:
                        infos = Scanner._getFileProperties(vFile.parent.parent.path, vFile.name, vFile.realPath)
                    else:
                        infos = Scanner._getFileProperties(vFile.parent.path, vFile.name, vFile.realPath)
                    
                    # stop on this file if something went wrong when analyzing it
                    try:
                        infos['id']
                    except:
                        continue
                    
                    # use fileId to check if information has already been searched
                    alreadySearched = self.db.getFileSearchFlag(infos['id'])
                    if not alreadySearched or alreadySearched == (0,):
                        self.movieDb.createMovieInfo(infos['id'])
                        self.db.updateFileSearchFlag(infos['id'], 1)
        
        scanFolder(FileTree.root)
                      
    def scanForDeletable(self):
        """
        remove all files which should be deleted
        """
        deletableFiles = self.movieDb.db.getAllDeletableFiles()
        for deleteDate, fileId, filePath, folder in deletableFiles:
            if time.time() > deleteDate + DELETE_AFTER:
                
                # remove DB information
                self.db.deleteFile(fileId)
                
                # remove file
                # check first if it has been found in tree parsing
                # else, it may have already been deleted
                if fileId in VFile.allFilesById:
                    try:
                        os.remove(VFile.allFilesById[fileId].realPath)
                    except:
                        pass
                    
    def removeDeletedFiles(self):
        """
        Remove from database all files which are no more present on file system
        First get all files from database
        Then check if they are present in FileTree. If they are not present, it may be caused by:
        - file system absent: the file may still exist once file system will be there
        - file deleted
        """

        for fileId, fileName, folderPath in self.db.getAllFiles():
            
            # does this file still exist on file system
            # if file is a movie in database, we have an intermediate folder (see FileTree)
            if FileTree.createIntermediateFolders(fileName):
                status, vFile = FileTree.getInstance(os.path.normpath(folderPath + "/" + os.path.splitext(fileName)[0] + '/' + fileName))
            else:
                status, vFile = FileTree.getInstance(os.path.normpath(folderPath + "/" + fileName))
            
            if vFile:
                continue
            else:
                # branch is accessible, but not the file, it has been deleted
                # remove from DB
                if status == FileTree.TREE_BRANCH_ACCESSIBLE:
                    self.db.deleteFile(fileId)
                    
                #Dans ce cas, il faut supprimer également les répertoires créés automatiquement
                # Ou alors, il faut faire la même vérification pour les répertoires
            
                
    @classmethod
    def getFilePropertiesById(cls, fileId):
        
        fileInfos = Scanner.db.getFileInfos(fileId)
        fileInfos['duration'] = datetime.timedelta(seconds=float(fileInfos.get('duration', 0)))
        fileInfos['id'] = fileId
        fileInfos['bitrate'] = fileInfos.get('bitrate', 0)
        return fileInfos
        
    @classmethod
    def getFileProperties(cls, filePath):
        
        vFile = VFile.allFilesByRealPath.get(filePath, None)
        if vFile:
            fileInfo = cls._getFileProperties(vFile.parent.path, vFile.name, vFile.realPath)
        
            return fileInfo
        
        raise FileInfoError("No file info could be found for path %s" % filePath)
        
    @classmethod
    def _getFileProperties(cls, vFolderPath, vFileName, realPath):
        """
        Retrieve file properties from database if it's already known, or, get them from ffprobe information
        @param vFolderPath: path of the virtual folder
        @param vFileName: file name
        @param realPath: real path on the file system
        """
        
        from backend.pydlnadms.fileManagement.Tools import guessMimetype
        
        # check if file already exist in database
        dbFileIds = cls.db.getFileId2(os.path.splitext(vFileName)[0])
        if dbFileIds is None:
            
            # add file to database
            mimetype = guessMimetype(realPath)
            folderId = cls.db.getFolderId(vFolderPath) # vFolderPath should here point to a folder existing in file system
            cls.db.addFile(folderId, str(vFileName), mimetype)
            fileId = cls.db.getFileId2(os.path.splitext(vFileName)[0])
            
            # get information about the media file
            fileProperties = res_data(realPath)
   
            print(realPath, fileProperties)
            # new file discovered, increment systemUpdateId
            from backend.pydlnadms.services import incrementSystemUpdateId
            incrementSystemUpdateId()

            # add info about this movie file
            for info, value in fileProperties.items():
                cls.db.addFileInfo(fileId, info, value)
            
            fileProperties.update({'id': fileId})
            fileProperties['duration'] = datetime.timedelta(seconds=float(fileProperties['duration']))
            return fileProperties
        else:
            return cls.getFilePropertiesById(dbFileIds)
            
    
    def startScanning(self):
        """
        start scanner once any other instance of scanner has finished 
        """
        
        while Scanner._scannerLock:
            time.sleep(0.5)
        self.start()
    