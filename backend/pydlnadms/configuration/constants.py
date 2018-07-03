import os
from pydlnadms_frontend.settings import HOME_DLNA_DIR

DATA_DIR = HOME_DLNA_DIR

PATTERNS_TO_REMOVE = ['__mpeg4', ' HD', '_nuv', ' DVD']

MOVIE_EXT = ['.avi', '.ts', '.mpeg', '.mpg', '.mkv', '.nuv', '.mp4', '.mp3']

DELETE_AFTER = 7 * 24 * 3600

DELETE_PATTERN = 'delete='

CONFIG_FILE = "pydlnadms.cfg"