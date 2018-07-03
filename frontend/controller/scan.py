from frontend.models import Files
import time

RECENT_SCAN_DELAY = 3600 * 24 # 1 day


def getMoviesToScan():
    return Files.objects.filter(searchDone=None)

def getRecentlyScannedMovies():
    return Files.objects.filter(searchDone__gt=time.time() - RECENT_SCAN_DELAY)

def getMovieInformation():
    return True

def updateSearchDone(movieId):
    try:
        movie = Files.objects.get(file_id=movieId)
        movie.searchDone = time.time()
        movie.save()
    except:
        pass
    
