import sqlite3
import threading
import os
from backend.pydlnadms.configuration.constants import DATA_DIR
from frontend.models import Files, Movie_infos

try:
    os.makedirs(DATA_DIR)
except:
    pass

DB_FILE = DATA_DIR + 'pydlnadms.db'
LOCK = threading.Lock()

def connectDb(func):
    
    CONNECTION = sqlite3.connect(DB_FILE, check_same_thread=False)
    
    def connect(self, *args):
        with LOCK:
            
            cursor = CONNECTION.cursor()
            reply = func(self, *args, cursor=cursor, connection=CONNECTION)
            cursor.close()
        
        return reply 
    
    return connect
        

class db(object):
    """
    access to movie database
    """

    def __init__(self):
        self.createDb()
      
    def createDb(self):
        
        if not os.path.isfile(DB_FILE) or os.path.getsize(DB_FILE) == 0:
            open(DB_FILE, 'wb').close()
        
            self.createTables()
        
    @connectDb
    def createTables(self, cursor=None, connection=None):
        cursor.execute("""CREATE TABLE folders (folder_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                    folder STRING)""")
        
        # display_folder_id is the folder where we will display the file in frontend tree
        # location_folder_id is the folder where the file resides (found be FileTree building)
        cursor.execute("""CREATE TABLE files (file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                  display_folder_id INTEGER, 
                                                  location_folder_id, 
                                                  path STRING, 
                                                  mimetype STRING,
                                                  deletable INTEGER,
                                                  newfile INTEGER,
                                                  searchDone INTEGER
                                                  )""")
        cursor.execute("""CREATE TABLE file_infos (file_info_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                  file_id INTEGER,
                                                  info STRING,
                                                  value STRING
                                                  )""")
        cursor.execute("""CREATE TABLE movie_infos (info_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                  file_id INTEGER, 
                                                  title STRING, 
                                                  casting STRING, 
                                                  productionYear STRING, 
                                                  description STRING, 
                                                  poster STRING, 
                                                  posterUrl STRING,
                                                  descriptionFile STRING,
                                                  thumbnail STRING,
                                                  rating FLOAT)""")
        connection.commit()
        
    @connectDb
    def getFolderId(self, folderName, cursor=None, connection=None):
        """
        Returns the folder Id and add it if it's not present in DB
        """
        
        if not folderName.endswith('/'):
            folderName += '/'
        
        # check if this folder already exist
        cursor.execute("""SELECT folder_id FROM folders WHERE folder = ?""", [folderName])
        folderId = cursor.fetchone()
        if folderId is None:
            cursor.execute("""INSERT INTO folders(folder_id, folder) VALUES (NULL, ?)""", (folderName,))
            connection.commit()
            
            # get the ID
            cursor.execute("""SELECT folder_id FROM folders WHERE folder = ?""", [folderName])
            folderId = cursor.fetchone()[0]
        else:
            folderId = folderId[0]
        
        return folderId
    
    @connectDb
    def getFolders(self, cursor=None, connection=None):
        """
        Returns the list of files in one folder
        """
        cursor.execute("""SELECT f.folder_id FROM folders f""")
        folders = cursor.fetchall()
        return [f[0] for f in folders]
    
    @connectDb
    def getFilesInFolder(self, folderId, cursor=None, connection=None):
        """
        Returns the list of files in one folder
        """
        cursor.execute("""SELECT f.file_id FROM files f WHERE f.location_folder_id=?""", (folderId,))
        files = cursor.fetchall()
        return [f[0] for f in files]
    
    @connectDb
    def getAllFiles(self, cursor=None, connection=None):
        """
        returns all files known by the database
        """
        cursor.execute("""SELECT f.file_id, f.path, d.folder FROM files f LEFT OUTER JOIN folders d ON d.folder_id = f.location_folder_id""")
        return cursor.fetchall()
    
#     @connectDb
    def getFileId2(self, fileName, cursor=None, connection=None):

        files = Files.objects.filter(path__startswith=fileName)
        for f in files:
            if os.path.splitext(f.path)[0] == fileName:
                return f.file_id

        return None


#         cursor.execute("""SELECT f.file_id FROM files f WHERE f.path LIKE ? || '.___' OR f.path LIKE ? || '.__'""", (fileName, fileName))
#         dbFiles = cursor.fetchone()
#         return dbFiles
    
    @connectDb
    def getFileInfo(self, fileId, cursor=None, connection=None):

        # get path
        cursor.execute("""SELECT f.path FROM files f WHERE f.file_id=?""", (fileId,))
        path = cursor.fetchone()[0]
        
        # get bitrate
        cursor.execute("""SELECT i.value FROM file_infos i WHERE i.file_id=? AND i.info='bitrate'""", (fileId,))
        try:
            bitrate = int(cursor.fetchone()[0])
        except:
            bitrate = 1
            
        # get duration
        cursor.execute("""SELECT i.value FROM file_infos i WHERE i.file_id=? AND i.info='duration'""", (fileId,))
        try:
            duration = int(cursor.fetchone()[0])
        except:
            duration = 1
            
        return bitrate, duration, path
    
    @connectDb
    def getFileSearchFlag(self, fileId, cursor=None, connection=None):

        cursor.execute("""SELECT f.searchDone FROM files f WHERE f.file_id=?""", (fileId,))
        dbFiles = cursor.fetchone()
        return dbFiles
    
    @connectDb
    def updateFileSearchFlag(self, fileId, flag, cursor=None, connection=None):

        cursor.execute("""UPDATE files SET searchDone=? WHERE file_id=?""", (flag, fileId))
        connection.commit()
        
    @connectDb
    def updateNewFileFlag(self, fileId, flag, cursor=None, connection=None):

        cursor.execute("""UPDATE files SET newfile=? WHERE file_id=?""", (flag, fileId))
        connection.commit()
        
    @connectDb
    def updateDeletableFlag(self, fileId, flag, cursor=None, connection=None):

        cursor.execute("""UPDATE files SET deletable=? WHERE file_id=?""", (flag, fileId))
        connection.commit()
        
    @connectDb
    def getFileDeletableFlag(self, fileId, cursor=None, connection=None):

        cursor.execute("""SELECT f.deletable FROM files f WHERE f.file_id=?""", (fileId,))
        flag = cursor.fetchone()
        return flag
    
    @connectDb
    def getAllDeletableFiles(self, cursor=None, connection=None):
        cursor.execute("""SELECT f.deletable, f.file_id, f.path, g.folder FROM files f LEFT OUTER JOIN folders g ON f.location_folder_id=g.folder_id WHERE f.deletable > 0""")
        return cursor.fetchall()

#     @connectDb
    def getMovieInfo(self, fileId, cursor=None, connection=None):
        
        return Movie_infos.objects.filter(file__file_id=fileId)
        
#         cursor.execute("""SELECT f.title, f.casting, f.productionYear, f.description, f.poster, f.rating, f.posterUrl, f.descriptionFile, f.thumbnail FROM movie_infos f WHERE f.file_id=?""", (fileId,))
#         fileInfos = cursor.fetchall()
#         return fileInfos
        
    @connectDb
    def addFile(self, folderId, fileName, mimetype, cursor=None, connection=None):
        """
        By default, location_folder_id and display_folder_id are the same
        """
        cursor.execute("""INSERT INTO files(file_id, display_folder_id, location_folder_id, path, mimetype, deletable, newfile, searchDone)
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)""", (folderId, folderId, str(fileName), mimetype, 0, 1, 0))
        connection.commit()
        
    @connectDb
    def deleteFile(self, fileId, cursor=None, connection=None):
        cursor.execute("""DELETE from files WHERE file_id=?""", (fileId,))
        
        # if movie_infos exists for this file
        try:
            cursor.execute("""DELETE from movie_infos WHERE file_id=?""", (fileId,))
        except:
            pass
        
        # if file_info exists for this file
        try:
            cursor.execute("""DELETE from file_infos WHERE file_id=?""", (fileId,))
        except:
            pass
        connection.commit()
        
    @connectDb
    def addMovieInfo(self, fileId, title, casting, productionYear, description, poster, posterUrl, descriptionFile, rating, thumbnail, cursor=None, connection=None):
        
        cursor.execute("""INSERT INTO movie_infos(info_id, file_id, title, casting, productionYear, description, poster, posterUrl, descriptionFile, rating, thumbnail)
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (fileId, title, casting, str(productionYear), description, poster, posterUrl, descriptionFile, float(rating), thumbnail))
        connection.commit()
        
    @connectDb
    def addFileInfo(self, fileId, infoName, infoValue, cursor=None, connection=None):
        cursor.execute("""INSERT INTO file_infos(file_info_id, file_id, info, value) VALUES (NULL, ?, ?, ?)""", (fileId, infoName, str(infoValue)))
        connection.commit()
        
    @connectDb
    def getFileInfos(self, fileId, cursor=None, connection=None):
        cursor.execute("""SELECT i.info, i.value FROM file_infos i WHERE file_id=?""", (fileId,))
        fileInfos = cursor.fetchall()
        return dict(fileInfos)
        
        
            
if __name__ == '__main__':
    s = db()
    s.getFileId('/home/worm/Videos/tests', 'Jean-Philippe.avi')
      
    
