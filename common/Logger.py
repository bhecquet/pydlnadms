'''
Created on 11 oct. 2016

@author: worm
'''
import logging


def getLogger(className):
    
    logger = logging.getLogger(className)
    logger.setLevel(logging.INFO)
    return logger
