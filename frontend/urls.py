from django.urls import path

from frontend.views import files, scan
from pydlnadms_frontend import settings
from django.views.static import serve
import os

urlpatterns = [
#     url(r'^$', views.index, name='index'),
    
    
    path(r'fileList/', files.filesDisplay, name='filesDisplay'),
    path(r'', files.displayHome, name='home'),
    path(r'home', files.displayHome, name='home2'),
    path(r'<int:fileid>/posters', files.posters, name='posters'),
    path(r'deleteInfo/', files.deleteFileInfo, name='deleteInfo'),
    path(r'selectFileInfo/', files.selectFileInfo, name='selectInfo'),
    path(r'markFileComplete/', files.markFileComplete, name='markFileComplete'),
    
    path(r'scan/', scan.scanMovies, name='scan'),
    path(r'scan/movie/', scan.updateScannedMovie, name='updateScan'),

]

urlpatterns += [
    path(r'data<str:path>', serve, {'document_root': settings.DLNA_DATA_DIR}, name='dataFile'),
    path(r'static/<str:path>', serve, {'document_root': os.path.join(settings.BASE_DIR, 'static') }, name='static'),
    ]