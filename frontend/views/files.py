
import os
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import render, redirect
from django.template.context_processors import csrf

from frontend.controller.files import getDirectChildren, \
    getParentFolder, getFilesInFolder, getRootFolders, getMoviesToCheck, \
    getPosterList, deleteFileInfos, markFileAsComplete, deleteOtherFileInfos
from frontend.models import Files


def filesDisplay(request):
    
    sourceFolder = request.GET['path']
    if sourceFolder.endswith('/'):
        sourceFolder = sourceFolder[:-1]
 
    return render(request, 'fileList.html', {'fileList': getFilesInFolder(sourceFolder),
                                                'parentFolder': getParentFolder(sourceFolder),
                                                'childFolders': getDirectChildren(sourceFolder)})
    
def displayHome(request):
    return render(request, 'home.html', {'rootFolders': getRootFolders(),
                                            'moviesToCheck': getMoviesToCheck()})
    
def posters(request, fileid=0):
    
    # get the parent path to be sure to return to parent when done
    parentPath = request.POST.get('parentPath', request.META['HTTP_REFERER'])
    parse = urlparse(parentPath)
    parentPath = parse.path
    if parse.query:
        parentPath += '?' + parse.query
    
    posterList = getPosterList(fileid)
    
    params = {'posterList': posterList,
               'file': Files.objects.get(file_id=fileid),
               'parentPath': parentPath}
    params.update(csrf(request))
    
    return render(request, 'posters.html', params)

def deleteFileInfo(request):
    infoId = int(request.POST['infoId'])
    deleteFileInfos(infoId)
    
    return posters(request, int(request.POST['fileId']))

def selectFileInfo(request):
    deleteOtherFileInfos(int(request.POST['fileId']), int(request.POST['infoId']))
    return markFileComplete(request)

def markFileComplete(request):
    fileId = int(request.POST['fileId'])
    parentPath = request.POST['parentPath']
    virtualPath = request.POST.get('virtualPath')
    
    markFileAsComplete(fileId)
    
    fileM = Files.objects.get(file_id=fileId)
    fileM.virtualPath = virtualPath
    fileM.save()
    
    return redirect(parentPath)
    