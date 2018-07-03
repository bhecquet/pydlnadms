'''
Created on 23 nov. 2013

@author: worm
'''

import logging
import mimetypes

from backend.pydlnadms.fileManagement.Scanner import Scanner
from backend.pydlnadms.fileManagement.FileTree import FileTree


def guessMimetype(path):
    fileType = None
    if path.endswith('.avi'):
        return 'video/divx'
    if fileType is None:
        if path.endswith('.ts'):
            return 'video/mpeg'
        elif path.endswith('.mkv'):
            return 'video/x-matroska'
        elif path.endswith('.avi'):
            return 'video/divx'

    fileType = mimetypes.guess_type(path)[0]
    if not fileType:
        fileType = 'application/octet-stream'
    return fileType

def scanDirectories():
    """
    build the file tree and scan it
    """
    # build file tree
    FileTree().buildTree()

    # scan folder
    try:
        scanner = Scanner()
        scanner.startScanning()
    except Exception as err:
        logging.warn("scanner failed: %s" % str(err))
