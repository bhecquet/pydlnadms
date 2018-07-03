'''
Created on 22 nov. 2013

@author: worm
'''
import os
import time

class VDirectory(object):
    """
    virtual directory that may contain several VFile
    """
    FOLDER_TYPE_VIDEO = 'video'
    
    def __init__(self, name, parent=None, path=None, thumbnailFile=None, accessible=True, folderType=None, creationDate=None):
        """
        @param name: folder name
        @param parent: parent VDirectory. May be None for root directory
        @param path: path of this directory. If not specified, it's the virtual path, from root
                    It can be used for special actions where a directory is used to do something and thus point elsewhere
        @param thumbnailFile: path to the thumbnail file
        @param accessible: Say if this virtual folder can be accessed / is available. It's used when a root real directory
                    cannot be read
        @param folderType: type of the folder. May be "video" other types does not exist
        """
        self.fileList = []
        self.name = name
        self.thumbnail = thumbnailFile
        self.parent = parent
        self.dirList = []
        self.folderType = folderType
        if creationDate:
            self.creationDate = creationDate
        else:
            self.creationDate = int(time.time()) 
        self.accessible = accessible
        
        if parent:
            self.path = parent.path + '/' + name.replace('?', '%3F')
            self.level = parent.getLevel() + 1
        else:
            self.path = '/'
            self.level = 0
        self.path = self.path.replace('//', '/')
            
        if path: 
            self.path = path
        
    def addFile(self, vFile):
        self.fileList.append(vFile)
        
    def addDir(self, vDirectory):
        self.dirList.append(vDirectory)
        
    def getLevel(self):
        return self.level
    
    def getParent(self):
        """
        Return parent VDirectory
        """
        return self.parent
    
    def findChildByName(self, childName):
        for folder in self.dirList:
            if folder.name == childName:
                return folder
        for f in self.fileList:
            if f.name == childName:
                return f
        
    def __str__(self):
        fmt = " " * 2 * self.level + self.name + "\n"
        for d in self.dirList:
            fmt += str(d)
        for f in self.fileList:
            fmt += " " * 2 * (self.level + 1) + str(f) + "\n"
        
        return fmt