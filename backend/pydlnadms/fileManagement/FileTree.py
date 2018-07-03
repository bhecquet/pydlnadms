'''
Created on 22 nov. 2013

@author: worm
'''
from backend.movieDb.movieDb import MovieDb
from backend.pydlnadms.configuration.FolderConfiguration import FolderConfiguration
from backend.pydlnadms.fileManagement.VDirectory import VDirectory
from backend.pydlnadms.fileManagement.VFile import VFile
import os
import time
from backend.pydlnadms.configuration.constants import MOVIE_EXT, DELETE_PATTERN
from backend._misc.mount import MountUtility
from common.Logger import getLogger

class FileTree(object):
    
    TREE_BRANCH_ACCESSIBLE = 1
    TREE_BRANCH_NOT_ACCESSIBLE = 2
    SYNOPSIS_FILE = 'synopsis'
    DELETE_FILE = 'delete file'
 
    root = VDirectory('root')
    movieDb = MovieDb()
    logger = getLogger("FileTree")
    
    def __init__(self, folderList=None, mergedFolders=None):
        if folderList:
            self.folderList = folderList
        else:
            self.folderList = FolderConfiguration.folders
            
        if mergedFolders:
            self.mergedFolders = mergedFolders
        else:
            self.mergedFolders = FolderConfiguration.mergedFolders
            
    @staticmethod
    def createIntermediateFolders(fileName):
        """
        Determine whether intermediate directory will be created (with synopsis and 'delete file') files
        """
        movieName, fileExt = os.path.splitext(fileName)
        if fileExt.lower() in MOVIE_EXT and FileTree.movieDb.movieInDb(movieName):
            return True
        else:
            return False
    
    def buildTree(self):
        """
        Build tree of all folders to explore
        """
        self.logger.info("building file tree")
        
        # mount all directories to scan
        for folder in FolderConfiguration.foldersToScan:
            MountUtility.mountRootFolders(folder)
        
        # add this folder as a child of root            
        # explore folder recursively
        def __exploreDir(directory, parent, currentIsParent=False):
            """
            parse directory adding virtual files and directories to tree
            @param directory: the real directory to walk through
            @param parent: the parent virtual directory
            @param currentIsParent: default is False. If True, the subdirectories are linked directly under
                                    the parent directory
            """
            
            dirName = os.path.basename(directory)
            
            try:
                creationDate = os.stat(directory).st_ctime
            except:
                creationDate = None
            
            # check if the current folder already exist in tree or not
            if currentIsParent:
                thisDir = parent
            else:
                thisDir = parent.findChildByName(dirName)
                if not thisDir:            
                    thisDir = VDirectory(dirName, parent, creationDate=creationDate)
                    parent.addDir(thisDir)
            
            for name in os.listdir(directory):
                if os.path.isdir(directory + os.sep + name):
                    __exploreDir(directory + os.sep + name, thisDir)
                elif os.path.isfile(directory + os.sep + name):
                    
                    movieName, fileExt = os.path.splitext(name)
                    
                    if thisDir.findChildByName(movieName) or thisDir.findChildByName(name):
                        continue
                    
                    # in case this file is known from movie database, add special folders (movie file, delete & synopsis)
                    if FileTree.createIntermediateFolders(name):
                        descrFiles = self.movieDb.getMovieDescriptionFile(movieName)
                        fileId = self.movieDb.getMovieFileId(movieName)
                        
                        # look for information about the movie
                        thumbnailFile = None
                        if self.movieDb.movieHasInformation(movieName):
                            thumbnailFiles = self.movieDb.getThumbnailFile(movieName)
                            
                            if thumbnailFiles:
                                thumbnailFile = thumbnailFiles[0]
                        
                        creationDate = os.stat(directory + os.sep + name).st_ctime
                        fileVDir = VDirectory(movieName, thisDir, thumbnailFile=thumbnailFile, folderType=VDirectory.FOLDER_TYPE_VIDEO, creationDate=creationDate)
                        
                        # 1st child: the movie file
                        fileVDir.addFile(VFile(name, directory + os.sep + name, fileVDir))
                        
                        # 2nd child, the synopsis if one exists
                        for i, descrFile in enumerate(descrFiles): 
                            fileVDir.addFile(VFile('%s %d' % (FileTree.SYNOPSIS_FILE, i), descrFile, fileVDir))

                        # 3rd child, the delete option
                        fileVDir.addDir(VDirectory(FileTree.DELETE_FILE, fileVDir, fileVDir.path + '?%s%d' % (DELETE_PATTERN, fileId)))
                        
                        thisDir.addDir(fileVDir)
                    else:
                        thisDir.addFile(VFile(name, directory + os.sep + name, thisDir))
        
        FileTree.root = VDirectory('root')
        
        # add real folder tree
        for folder in self.folderList:
            if not os.path.isdir(folder):
                FileTree.root.addDir(VDirectory(os.path.basename(folder), FileTree.root, accessible=False))
                continue
                   
            __exploreDir(folder, FileTree.root)
            
        # add merged folders
        for folderName, folderList in self.mergedFolders.items():
            
            mergedRoot = FileTree.root.findChildByName(folderName)
            if not mergedRoot:            
                mergedRoot = VDirectory(folderName, FileTree.root)
                FileTree.root.addDir(mergedRoot)
            
            # walk through all directories in merged folder
            for folder in folderList:
                
                # if one of the folder in merged folder is non accessible, we state that all the folder is non accessible
                # this flag should only be used for file deletion and does not impact file access
                if not os.path.isdir(folder):
                    mergedRoot.accessible = False
                    continue
                
                __exploreDir(folder, mergedRoot, currentIsParent=True)
                
        # mount all directories to scan
        for folder in FolderConfiguration.foldersToScan:
            MountUtility.umountRootFolders(folder)
                      
        self.logger.info("file tree build")    
                        
        return FileTree.root
    
    @staticmethod
    def getInstance(path):
        """
        Returns the VDirectory or VFile corresponding to the path
        If VFile or VDirectory cannot be found, returns None
        @param path: path to look for
        
        @return: status, vFile
        
        The status is 0 if vFile is found
        Status is 1 for deleted vFile
        Status is 2 for not accessible vFile
        """ 
        
        
        def __exploreTree(parent, remainingPath, parentIsAccessible=True):
            
            pathParts = remainingPath.split('/')
            currentName = pathParts[0]
            remainingPath = '/'.join(pathParts[1:])
            parentIsAccessible = parentIsAccessible and parent.accessible
            
            for d in parent.dirList + parent.fileList:
                if d.name == currentName:
                    
                    # still more dir to find
                    if remainingPath:
                        return __exploreTree(d, remainingPath, parentIsAccessible)
                    else:
                        return 0, d
                 
            # no vFile or vFolder found, there may be an error accessing it 
            # check the reason  
            else:
                # the sub-root folder has been accessed, mount is OK
                if parentIsAccessible:
                    return FileTree.TREE_BRANCH_ACCESSIBLE, None
                # the sub-root folder cannot be accessed, a disk or folder may not have been
                # mounted
                else:
                    return FileTree.TREE_BRANCH_NOT_ACCESSIBLE, None
                    
                
                    
        if path == '/':
            return 0, FileTree.root
                    
        if path.startswith('/'):
            path = path[1:]
        path = path.replace('%3F', '?')
        return __exploreTree(FileTree.root, path)
     
 
                
    
                
