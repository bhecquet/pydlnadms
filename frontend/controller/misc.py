import os
from django.conf import settings


pydlnaFile = settings.HOME_DIR + os.sep + '.pydlna'

def markActive(callback):
    return callback
    #open(pydlnaFile, 'w').close()