'''
Created on 7 juil. 2012

@author: worm
'''

from django.db import models

class Folders(models.Model):
    
    class Meta:
        db_table = 'folders'
    
    folder_id = models.IntegerField(primary_key=True)
    folder = models.CharField(max_length=200)
    
class Files(models.Model):
    
    class Meta:
        db_table = 'files'
    
    file_id = models.IntegerField(primary_key=True)
    display_folder = models.ForeignKey(Folders, related_name='display_folder_id')
    location_folder = models.ForeignKey(Folders, related_name='location_folder_id')
    path = models.CharField(max_length=200) 
    mimetype = models.CharField(max_length=60) 
    deletable = models.IntegerField() # date at which file has been marked as deletable in epoch format
    newfile = models.BooleanField() 
    searchDone = models.IntegerField() # date at which a scan has been done on this file in epoch format
    virtualPath = models.CharField(max_length=255, null=True) # path to which this file should be presented. Allow to classify files and group them
    

class File_infos(models.Model):
    """    
    Technical information about the file
    """
    
    class Meta:
        db_table = 'file_infos'
        
    file_info_id = models.IntegerField(primary_key=True) 
    file = models.ForeignKey(Files)
    info = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    
class Movie_infos(models.Model):
    
    class Meta:
        db_table = 'movie_infos'
    
    info_id = models.IntegerField(primary_key=True)
    file = models.ForeignKey(Files)
    title = models.CharField(max_length=100)
    casting = models.CharField(max_length=100)
    productionYear = models.CharField(max_length=4)
    description = models.CharField(max_length=1000)
    poster = models.CharField(max_length=100)
    posterUrl = models.CharField(max_length=100)
    descriptionFile = models.CharField(max_length=100)
    thumbnail = models.CharField(max_length=100)
    rating = models.FloatField()
    
    