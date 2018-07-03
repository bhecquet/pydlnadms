import urllib.request
import urllib.parse
import json
import os

from collections import namedtuple
from backend.pydlnadms.configuration.constants import DATA_DIR
import time
import base64
import hashlib

ALLOCINE_URL_API = "http://api.allocine.fr/rest/v3/"
ALLOCINE_URL_MOVIE = ALLOCINE_URL_API + "movie?"
ALLOCINE_URL_SEARCH = ALLOCINE_URL_API + "search?"
ALLOCINE_URL = "www.allocine.fr"
PARTNER = "partner=QUNXZWItQWxsb0Npbuk"
POSTER_DIR = DATA_DIR + 'data'

Movie = namedtuple('Movie', ('title', 'description', 'casting', 'rating', 'posterUrl', 'posterFile', 'productionYear', 'id'))

class Allocine(object):
    
    def __init__(self, downloadPath=POSTER_DIR):
        
        self.downloadPath = downloadPath
        
        if os.path.isdir(self.downloadPath):
            self.downloadFiles = True
        else:
            try:
                os.makedirs(self.downloadPath)
                self.downloadFiles = True
            except:
                self.downloadFiles = False
                
    def searchAndSelectMovie(self, movieName):
        """
        Search for a movie and ask the user to select the correct poster
        """
        movies = self.searchMovies(movieName, False)
            
        selectedMovie = self.__displayChoice(movies, movieName)
        
        if selectedMovie is None:
            print("could not find any movie corresponding to %s" % (movieName))
        
        else:
            # really download poster now
            self.downloadPoster(selectedMovie.posterUrl, True)
        
        return selectedMovie
    
    def allocineUrl(self, route ='search', arTokens = {}):
        secret              = 'e2b7fd293906435aa5dac4be670e7982'.encode()
        secret              = '29d185d98c984a359e6e6f26a0474269'.encode()
        arTokens['partner'] = 'V2luZG93czg'.encode()
        arTokens['partner'] = '100043982026'.encode()
        arTokens['sed']     = time.strftime('%Y%m%d', time.localtime())
        arTokens['sig']     = base64.b64encode(hashlib.sha1(secret + urllib.parse.urlencode(arTokens).encode()).digest())
        return urllib.request.urlopen('http://api.allocine.fr/rest/v3/' + route + '?' + urllib.parse.urlencode(arTokens))
     
        
    
    def searchMovies(self, movieName, downloadPosters=True):
        """
        Search for movie information and return all information found
        """
        movies = []
        
        try:
            reply = urllib.request.urlopen(ALLOCINE_URL_SEARCH + PARTNER + "&filter=movie&count=20&format=json&q=" + urllib.parse.quote(movieName))
        except Exception as err:
            return None
        moviesData = json.loads(reply.read().decode())
        
        if moviesData['feed']['totalResults'] == 0:
            return None
        
        for movieData in moviesData['feed']['movie']:
            posterUrls = [movieData.get('poster', {}).get('href', '')]
            if posterUrls[0] != '':
                posterUrls += ['http://images.allocine.fr/r_640_600/b_1_d6d6d6/' + movieData.get('poster', {}).get('path', ''), 
                               'http://fr.web.img1.acsta.net/r_160_240/b_1_d6d6d6' + movieData.get('poster', {}).get('path', '')
                               ]
            newMovie = Movie(movieData.get('title', movieData.get('originalTitle', movieName)), 
                             self.getMovieDescription(movieData['code']), 
                             movieData.get('castingShort', {}).get('actors', ''), 
                             movieData.get('statistics', {}).get('userRating', 0.0), 
                             posterUrls, 
                             self.downloadPoster(posterUrls),
                             movieData.get('productionYear', ''), 
                             movieData['code']
                        )
            
            movies.append(newMovie)

        # really download poster now
        if downloadPosters:
            for movie in movies:
                self.downloadPoster(movie.posterUrl, True)
               
        newMovies = [] 
        for movie in movies:
            newMovie = Movie(movie.title, 
                             movie.description, 
                             movie.casting, 
                             movie.rating, 
                             movie.posterUrl[0], 
                             movie.posterFile,
                             movie.productionYear, 
                             movie.id
                        )
            newMovies.append(newMovie)
        
        return newMovies
    
    def __displayChoice(self, movies, movieName):
        """
        If several movies are found, ask the user to choose which is the right one
        """
        if len(movies) == 0:
            return None
        elif len(movies) == 1:
            print("found match: " + movies[0].title)
            return movies[0]
        else:
            print("found %d movies for %s" % (len(movies), movieName))
            print(" - 0 . None of them")
            for i, movie in enumerate(movies):
                print(" - %d . %s - %s" % (i + 1, movie.title, movie.productionYear))
            
            while 1:
                
                choice = input("select movie [1-%d]:\n" % len(movies))
                try:
                    if int(choice) == 0:
                        return None
                    if 0 < int(choice) <= len(movies):
                        return movies[int(choice) - 1]
                except:
                    pass
        
    
    def getMovieDescription(self, movieId):
        """
        Retrieve complete movie information 
        """
        try:
            reply = urllib.request.urlopen(ALLOCINE_URL_MOVIE + PARTNER + "&filter=movie&striptags=synopsis,synopsisshort&format=json&profile=large&code=%d" % (movieId ))
            jsonData = str(reply.read(), encoding='utf8')
            movieData = json.loads(jsonData)
            return movieData['movie'].get('synopsis', 'pas de description')
        except:
            return ''
        
    def downloadPoster(self, urls, downloadFile=False):
        if self.downloadFiles:
            for url in urls:
                if url == '':
                    continue
                
                fileName = os.path.basename(url)
                if downloadFile:
                    with open(self.downloadPath + os.sep + fileName, 'wb') as posterFile:
                        
                        # do not stop if error occurs on URL
                        try:
                            posterFile.write(urllib.request.urlopen(url).read())
                        except:
                            print("error %s" % (url))
                            continue
                return fileName
            
            else:
                return ''
        else:
            return ''
            
        
        
if __name__ == '__main__':
    allo = Allocine()
    print(allo.allocineUrl('search', {'q':'avatar','filter':'movie','format':'json'}))
#    movies = allo.searchMovies("The Mask")
    
    