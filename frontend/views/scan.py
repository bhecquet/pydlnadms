from django.shortcuts import render
from frontend.controller.scan import getMoviesToScan,\
    getRecentlyScannedMovies, updateSearchDone
from django.http import HttpResponse

def scanMovies(request):
    return render(request, 'scan.html', {'moviesToScan': getMoviesToScan(),
                                            'moviesAlreadyScanned': getRecentlyScannedMovies()})

def updateScannedMovie(request):
    movieId = request.GET['movieId']
    
    # get the information on the movie and return OK when done
    
    # update searchDone field of the movie
    updateSearchDone(movieId)
    
    return HttpResponse('OK', mimetype='text/plain')