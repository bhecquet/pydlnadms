'''
Created on 4 sept. 2012

@author: worm
'''

from frontend.models import Folders, Files, Movie_infos
from django.conf import settings

import os
from frontend.controller.misc import markActive

@markActive
def getDirectChildren(sourceFolder):
    
    # filter child folders
    childFolders = Folders.objects.filter(folder__startswith=sourceFolder)
    
    childFolderPaths = []
    for childFolder in childFolders:
        if childFolder.folder[-1] == '/':
            folderPath = childFolder.folder[:-1]
        else:
            folderPath = childFolder.folder
            
        if folderPath == sourceFolder:
            continue
            
        # this folder is a direct child, referenced in database
        if os.path.dirname(folderPath) == sourceFolder:
            childFolderPaths.append(folderPath)
            
        # this folder is a subfolders
        else:
            childFolderPaths.append(sourceFolder + '/' + folderPath.replace(sourceFolder, '').split('/')[1])
            
    return list(set(childFolderPaths))

@markActive
def getParentFolder(sourceFolder):
    
    parentFolderName = os.path.dirname(sourceFolder)
    try:
        parentFolder = Folders.objects.get(folder__in=[parentFolderName, parentFolderName + '/']).folder
    except:
        # if none of the folder in database is the parent of this folder (direct or not), we
        # are above root
        # check we are on the same branch
        for folder in Folders.objects.all():
            if len(folder.folder) > len(parentFolderName) or not parentFolderName.startswith(folder.folder):
                continue
            else:
                parentFolder = parentFolderName
                break
        else:
            parentFolder = ''
        
    return parentFolder

@markActive
def getFilesInFolder(sourceFolder):
    
    return Files.objects.filter(location_folder__folder__in=[sourceFolder, sourceFolder + '/']).order_by('path')

@markActive
def getRootFolders():
    
    allFolders = [f.folder for f in Folders.objects.all()]

    roots = []
    
    while len(allFolders) > 0:
        
        sortedFolders = sorted(allFolders)
        allFolders = []
        roots.append(sortedFolders[0])
        for folder in sortedFolders[1:]:
            if not folder.startswith(sortedFolders[0]):
                allFolders.append(folder)
    
    return roots

@markActive
def getMoviesToCheck():
    return Files.objects.filter(newfile=True)

@markActive
def getPosterList(fileId):
    return Movie_infos.objects.filter(file__file_id=fileId)

def deleteFileInfo(fileInfo):
    try:
        # remove all downloaded files
        if os.path.isfile(settings.DLNA_DATA_DIR + fileInfo.poster):
            os.remove(settings.DLNA_DATA_DIR + fileInfo.poster)
        if os.path.isfile(settings.DLNA_DATA_DIR + fileInfo.descriptionFile):
            os.remove(settings.DLNA_DATA_DIR + fileInfo.descriptionFile)
        if os.path.isfile(settings.DLNA_DATA_DIR + fileInfo.thumbnail):
            os.remove(settings.DLNA_DATA_DIR + fileInfo.thumbnail)
        
        fileInfo.delete()
    except:
        pass
    

def deleteFileInfos(infoId):
    fileInfo = Movie_infos.objects.get(info_id=infoId)
    deleteFileInfo(fileInfo)

def deleteOtherFileInfos(fileId, infoIdToKeep):
    
    infos = getPosterList(fileId)
    for fileInfo in infos:
        if fileInfo.info_id != infoIdToKeep:
            deleteFileInfo(fileInfo)
    
def markFileAsComplete(fileId):
    fileM = Files.objects.get(file_id=fileId)
    fileM.newfile = False
    fileM.save()