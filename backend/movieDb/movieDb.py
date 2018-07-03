import os
import sys

from backend.pydlnadms.configuration.constants import PATTERNS_TO_REMOVE, DATA_DIR
from .allocine import Allocine
from .db import db
from .DescriptionFile import DescriptionFile
from backend.movieDb.allocine import POSTER_DIR
from backend.movieDb.tmdb import Tmdb


class MovieDb(object):
    """
    Class for updating movie data in database
    This uses Allocine access to retrieve information
    """
    cache = {}
    
    def __init__(self, initAllocine=True):
        self.tmdb = Tmdb()
        self.db = db()
    
    def completeMovieInfo(self, folderName=None):
        """
        Add movie info to database
        """
        # get all movies associated to a folder
        if folderName is None:
            folderIds = self.db.getFolders()
        else:
            folderId = self.db.getFolderId(folderName)
            if not folderId:
                return
            else:
                folderIds = list(folderId)
          
        # get all files to search for  
        fileIds = []
        for folderId in folderIds:
            fileIds += self.db.getFilesInFolder(folderId)
        
        for fileId in fileIds:
            
            infos = self.db.getMovieInfo(fileId)
            
            if infos:
                # check if description file still exists
                if not os.path.isfile(infos[0].descriptionFile):
                    infos = None
                createInfos = False
            else:
                createInfos = True
                
            if not infos:
                self.createMovieInfo(fileId, createInfos)
                
                
    def createMovieInfo(self, fileId, createInfos=True):
        """
        Add allocine information to the database
        """
        
        # get movie name
        bitrate, duration, path = self.db.getFileInfo(fileId)
        movieName = os.path.splitext(path)[0]
        print("scanning movie: %s" % movieName)
        
        # remove patterns which could prevent from getting info from allocine
        for pattern in PATTERNS_TO_REMOVE:
            movieName = movieName.replace(pattern, '')
        
        # here, we may get several different information for the same movie
        movieInfos = self.tmdb.searchMovies(movieName)
        
        if movieInfos is None:
            self.db.updateNewFileFlag(fileId, 0)
            return
        
        # create description file for each description
        for infoId, movieInfo in enumerate(movieInfos):
            
            descriptionFile = DescriptionFile(movieInfo.title, 
                                              movieInfo.casting[:300], 
                                              movieInfo.productionYear, 
                                              movieInfo.description, 
                                              POSTER_DIR + os.sep + movieInfo.posterFile,
                                              movieInfo.rating,
                                              POSTER_DIR + os.sep + 'info-%d-%d.jpeg' % (fileId, infoId)
                                              )
            descriptionFile.buildMovieDescriptionFile()
        
            # add info to database
            if createInfos:
                thumbnailFilePath = DescriptionFile.createThumbnail(POSTER_DIR + os.sep + movieInfo.posterFile, POSTER_DIR + os.sep + 'thumbnail-%d-%d.jpeg' % (fileId, infoId))
                self.db.addMovieInfo(fileId, 
                                    movieInfo.title, 
                                    movieInfo.casting[:300], 
                                    movieInfo.productionYear, 
                                    movieInfo.description, 
                                    movieInfo.posterFile, 
                                    movieInfo.posterUrl, 
                                    'info-%d-%d.jpeg' % (fileId, infoId), 
                                    movieInfo.rating,
                                    thumbnailFilePath.replace(POSTER_DIR + os.sep, '')  # may be empty if no thumbnail exist
                                   )
        
                
    def movieHasInformation(self, movieName):
        """
        Check in database if the movie has descriptive information or not
        """
        fileId = self.getMovieFileId(movieName)
        
        if fileId and list(self.db.getMovieInfo(fileId)):
            return True
        else:
            return False
        
    def movieInDb(self, movieName):
        """
        Check in database if the movie has descriptive information or not
        """
        fileId = self.getMovieFileId(movieName)
        
        if fileId:
            return True
        else:
            return False
        
    def movieIsDeletable(self, movieName):
        fileId = self.getMovieFileId(movieName)
        
        if fileId and self.db.getFileDeletableFlag(fileId) == (1,):
            return True
        else:
            return False
        
    def getMovieFileId(self, movieName):
        
        if movieName in MovieDb.cache:
            return MovieDb.cache[movieName]
        
        fileId = self.db.getFileId2(movieName)
        
        if fileId is None:
            MovieDb.cache[movieName] = None
            return None
        else:
            MovieDb.cache[movieName] = fileId
            return fileId
        
        
    def getMovieDescriptionFile(self, movieName):
        fileId = self.getMovieFileId(movieName)
        infos = self.db.getMovieInfo(fileId) 
        
        if infos:
            return [POSTER_DIR + os.sep + info.descriptionFile for info in infos]
        else:
            return []
        
    def getThumbnailFile(self, movieName):
        fileId = self.getMovieFileId(movieName)
        infos = self.db.getMovieInfo(fileId) 
        
        if infos:
            return [POSTER_DIR + os.sep + info.thumbnail if info.thumbnail else None for info in infos]
        else:
            return []
