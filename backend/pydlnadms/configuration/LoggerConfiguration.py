from backend.pydlnadms.configuration.ServerConfiguration import ServerConfiguration
import logging

class LoggerConfiguration(object):
    
    logger = None
    logFormat = '%(asctime)s.%(msecs)03d;%(levelname)s;%(name)s;%(message)s'
    dateFormat = '%H:%M:%S'
    
    @classmethod
    def configureLogger(cls):
        if ServerConfiguration.loggingFileConf is None:
            formatter = logging.Formatter(cls.logFormat, datefmt=cls.dateFormat)
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
        else:
            logging.config.fileConfig(ServerConfiguration.loggingFileConf, disable_existing_loggers=False)
        logger = logging.getLogger('pydlnadms.main')