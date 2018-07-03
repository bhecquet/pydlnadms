'''
Created on 22 nov. 2013

@author: worm
'''
from backend.movieDb.db import db
from backend.movieDb.movieDb import MovieDb
import os

class VFile(object):
    """
    Class defining a virtual file
    a virtual file is linked to a read file but file tree may be different
    a virtual file is always contained in a VDirectory
    """
    
    movieDb = MovieDb()
    allFilesById = {}
    allFilesByRealPath = {}
    
    def __init__(self, name, realPath, parent, thumbnailFile=None):
        """
        @param name: name of the file with ext
        @param realPath: the real path on file system
        @param parent: the parent VDirectory
        @param thumbnailFile: we can give a thumbnail for this file
        """
        
        self.realPath = realPath
        self.creationDate = os.stat(realPath).st_ctime
        self.name = name
        self.thumbnail = thumbnailFile
        self.path = parent.path + '/' + name.replace('?', '%3F')
        self.parent = parent
        
        self.dbFile = VFile.movieDb.getMovieFileId(os.path.splitext(name)[0])
        
        # keep trace of this file in case of deletion
        if self.dbFile:
            VFile.allFilesById[self.dbFile] = self
        VFile.allFilesByRealPath[realPath] = self
        
    def delete(self):
        if self.dbFile:
            # TODO lier a la BDD
            pass
        
    def getParent(self):
        return self.parent
        
    def __str__(self):
        return self.name