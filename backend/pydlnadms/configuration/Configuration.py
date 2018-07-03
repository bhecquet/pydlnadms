'''
Created on 16 janv. 2016

@author: worm
'''
from pydlnadms_frontend.settings import HOME_DLNA_DIR
from backend.pydlnadms.configuration.constants import CONFIG_FILE
import configparser
import os
from backend.pydlnadms.configuration.FolderConfiguration import ConfigurationException
from subprocess import PIPE, Popen

config = {}

def readConfig():
    if not os.path.isfile(HOME_DLNA_DIR + os.sep + CONFIG_FILE):
        return 
    
    parser = configparser.ConfigParser()
    parser.read(HOME_DLNA_DIR + os.sep + CONFIG_FILE)
    
    # ffmpeg
    config['ffmpeg.directory'] = parser.get('General', "ffmpeg.directory", fallback='')
    
    try:
        args = [config['ffmpeg.directory'] + os.sep + 'ffprobe', '--help']
        process = Popen(args, stdout=PIPE, stderr=PIPE, close_fds=True)
        stdout, stderr = process.communicate()
        
    except:
        raise ConfigurationException("ffmpeg or ffprobe are not available in %s" % config['ffmpeg.directory']) 
 