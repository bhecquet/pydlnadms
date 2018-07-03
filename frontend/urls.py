from django.conf.urls import url

from frontend.views import files, scan
from pydlnadms_frontend import settings
from django.views.static import serve
import os

urlpatterns = [
#     url(r'^$', views.index, name='index'),
    
    
    url(r'^fileList/$', files.filesDisplay, name='filesDisplay'),
    url(r'^$', files.displayHome, name='home'),
    url(r'^home', files.displayHome, name='home2'),
    url(r'^(?P<fileid>\d+)/posters', files.posters, name='posters'),
    url(r'^deleteInfo/$', files.deleteFileInfo, name='deleteInfo'),
    url(r'^selectFileInfo/$', files.selectFileInfo, name='selectInfo'),
    url(r'^markFileComplete/$', files.markFileComplete, name='markFileComplete'),
    
    url(r'^scan/$', scan.scanMovies, name='scan'),
    url(r'^scan/movie/$', scan.updateScannedMovie, name='updateScan'),

]

urlpatterns += [
    url(r'^data(?P<path>.*)$', serve, {'document_root': settings.DLNA_DATA_DIR}, name='dataFile'),
    url(r'^static/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.BASE_DIR, 'static') }, name='static'),
    ]