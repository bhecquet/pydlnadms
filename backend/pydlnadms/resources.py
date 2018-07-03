import os

from backend.pydlnadms.fileManagement.Scanner import Scanner
from backend._misc.mount import MountUtility
from pydlnadms_frontend.settings import BASE_DIR

class FileResource(object):

    knownRessources = {}
    
    @staticmethod
    def getBitrate(path):
        if os.path.splitext(path)[1] in ['.ts', '.mkv', '.mp4', '.avi']:
            
            if path not in FileResource.knownRessources:
                FileResource.knownRessources[path] = Scanner.getFileProperties(path)['bitrate']
            return FileResource.knownRessources[path] / 8.
    
        else:
            return 1

    def __init__(self, path, start=0, end=None):
        
        # before starting playing, check if the folder is mounted
        MountUtility.checkMount(path)
        
        if path.startswith('static/'):
            path = BASE_DIR + os.sep + 'backend' + os.sep + path
        
        self.file = open(path, 'rb')
        self.start = start
        self.end = end
        self.file.seek(start)

    def read(self, count):
        if self.end is not None:
            count = min(self.end - self.file.tell(), count)
        data = self.file.read(count)
        if data:
            return data

    @property
    def size(self):
        return os.fstat(self.file.fileno()).st_size

    @property
    def length(self):
        if self.end is None:
            return None
        else:
            return self.end - self.start

    def __repr__(self):
        return '<FileResource path=%r, start=%r, end=%r>' % (self.file.name, self.start, self.end)

    def close(self):
        self.file.close()

    def fileno(self):
        return self.file.fileno()
