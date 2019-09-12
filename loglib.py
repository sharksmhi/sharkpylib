'''
Created on 4 jul 2016

@author: a001985
'''
import os
import logging 


class Logger(object):

    def __init__(self, name='main', **kwargs):
        self.levels = dict(INFO=logging.INFO,
                           DEBUG=logging.DEBUG,
                           WARNING=logging.WARNING,
                           ERROR=logging.ERROR,
                           CRITICAL=logging.CRITICAL)
        self.name = name
        self.kwargs = kwargs
        self.default_format = '%(asctime)s\t%(levelname)s\t%(module)s (row=%(lineno)d)\t%(message)s'

        self.logger = logging.getLogger(name)

        if kwargs.get('level'):
            level = kwargs.get('level')
            self.logger.setLevel(self.levels.get(level, level))

        self.formatter = logging.Formatter(kwargs.get('format', self.default_format))

        for logfile in kwargs.get('logfiles', []):
            if not isinstance(logfile, dict):
                raise AttributeError('log information needs to be of type dict')
            self.add_logfile(**logfile)

    def add_logfile(self, **kwargs):
        logger_file_path = kwargs.get('file_path')
        self.remove_handler(file_path=logger_file_path)
        file_handler = logging.FileHandler(logger_file_path)
        file_handler.setFormatter(self.formatter)
        level = kwargs.get('level', 'WARNING')
        file_handler.setLevel(self.levels.get(level, level))
        self.logger.addHandler(file_handler)

    def remove_handler(self, file_path=None):
        pop_index = []
        for i, handler in enumerate(self.logger.handlers):
            if file_path:
                try:
                    if os.path.samefile(handler.baseFilename, os.path.abspath(file_path)):
                        pop_index.append(i)
                    handler.flush()
                except:
                     pass

        if pop_index:
            pop_index.reverse()
            for i in pop_index:
                self.logger.handlers.pop(i)


    def get_logger(self):
        return self.logger


def get_logger(**kwargs):
    # import Logger
    DEFAULT_LOG_INPUT = {'name': 'test_log',
                         'level': 'DEBUG'}
    DEFAULT_LOG_INPUT.update(kwargs)
    # log_object = log.Logger(**DEFAULT_LOG_INPUT)
    log_object = Logger(**DEFAULT_LOG_INPUT)
    logger = log_object.get_logger()
    return logger


def logtester():
    global logger

    directory = os.path.dirname(__file__)
    logfiles = [dict(file_path=os.path.join(directory, 'test_debug.log'),
                     level='DEBUG'),
                dict(file_path=os.path.join(directory, 'test_warnings.log'),
                     level='WARNING'),
                dict(file_path=os.path.join(directory, 'test_error.log'),
                     level='ERROR')
                ]
    log_info = dict(logfiles=logfiles)

    # Use this setup
    # import Logger
    logger = get_logger(**log_info)

    # log events
    logger.debug('AAA')
    logger.info('BBB')
    logger.warning('CCC')
    logger.error('DDD')
    logger.critical('EEE')



logger = get_logger()

if __name__ == '__main__':
    logtester()





