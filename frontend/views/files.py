
from django.shortcuts import render_to_response, redirect
from django.conf import settings

import os
from frontend.controller.files import getDirectChildren,\
    getParentFolder, getFilesInFolder, getRootFolders, getMoviesToCheck,\
    getPosterList, deleteFileInfos, markFileAsComplete, deleteOtherFileInfos
from urllib.parse import urlparse
from django.template.context_processors import csrf


def filesDisplay(request):
    
    sourceFolder = request.GET['path']
    if sourceFolder.endswith('/'):
        sourceFolder = sourceFolder[:-1]
 
    return render_to_response('fileList.html', {'fileList': getFilesInFolder(sourceFolder),
                                                'parentFolder': getParentFolder(sourceFolder),
                                                'childFolders': getDirectChildren(sourceFolder)})
    
def displayHome(request):
    return render_to_response('home.html', {'rootFolders': getRootFolders(),
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
               'fileId': fileid,
               'parentPath': parentPath}
    params.update(csrf(request))
    
    return render_to_response('posters.html', params)

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
    
    markFileAsComplete(fileId)
    
    return redirect(parentPath)
    