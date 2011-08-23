"""Wrapper for python's logging class to make logging easier
                             and more standardized.

                             """

                             import sys
                             import platform
                             import logging

                             FILE_FORMAT_STRING = '%(created).3f\t %(asctime)s\t %(threadName)s\t %(module)s\t %(name)s\t %(funcName)s\t %(lineno)d\t %(levelname)s\t %(message)s\t'
                             CONSOLE_FORMAT_STRING = '%(message)s\t %(threadName)s\t %(module)s\t %(funcName)s\t %(lineno)d\t %(created).3f\t %(asctime)s\t %(name)s\t %(levelname)s\t'
                             QUIET_FORMAT_STRING = '%(message)s'
                             datefmt_string = '%a %d %b %Y %H:%M:%S'

                             DEBUG = logging.DEBUG
                             ERROR = logging.ERROR
                             INFO = logging.INFO
                             WARNING = logging.WARNING
                             CRITICAL = logging.CRITICAL

                             def main():
                                 """Parse input strings and run the appropriate function."""
                                 if len(sys.argv) > 1:
                                     if sys.argv[1] == 'sys_info':
                                         return sys_info()
                                     elif sys.argv[1] == 'log_format':
                                         return FILE_FORMAT_STRING
                                     elif sys.argv[1] == 'console_format':
                                         return CONSOLE_FORMAT_STRING
                                     elif sys.argv[1] == 'quiet_format':
                                         return QUIET_FORMAT_STRING
                                     elif sys.argv[1] == 'date_format':
                                         return datefmt_string

                             def sys_info():
                                 """Gather as much OS and computer info as possible."""

                                 header = '\n'
                                 header += 'Python version=' + sys.version + '\n'
                                 header += 'OS=' + sys.platform + '\n'
                                 header += 'System=' + platform.system() + '\n'
                                 header += 'Release=' + platform.release() + '\n'
                                 header += 'Version=' + platform.version() + '\n'
                                 header += 'Linkage=' + platform.architecture()[1] + '\n'
                                 if sys.platform == 'win32':
                                     header += 'Windows Version=' + get_windows_version() + '\n'
                                     header += 'Win32 Version=' + platform.win32_ver()[2] + '\n'
                                     header += 'Processor type=' + platform.win32_ver()[3] + '\n'
                                 header += 'Bits=' + platform.architecture()[0] + '\n'
                                 header += 'Network name=' + platform.node() + '\n'
                                 header += 'Machine type=' + platform.machine() + '\n'
                                 header += 'Processor=' + platform.processor() + '\n'

                                 return header

                             def get_windows_version():
                                 """Pull the Windows OS version out of the registry."""

                                 import _winreg
                                 key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                 'SOFTWARE\\Microsoft\Windows NT\\CurrentVersion')
                                 return _winreg.QueryValueEx(key, 'ProductName')[0]


                             def get_logger(loggerName=''):
                                 """Return a configured logger. A logger heirarchy can be created using the
                                 format 'parent_name.child_name'. Child loggers will pass log messages
                                 up to parent loggers.

                                 Keyword arguments:
                                 loggerName -- the name the logger will use inside the log file.

                                 """
                                 import logging
                                 logger = logging.getLogger(loggerName)
                                 logger.setLevel(logging.DEBUG)
                                 logger.debug('created logger: ' + str(loggerName))
                                 return logger

                             def set_logfile(logger, filename, format_string=None, append=True, level=DEBUG):
                                 """Create a new file handler for a logger.

                                 Keyword arguments:
                                 logger -- the logger to be given a file handler.
                                 filename -- the file to be logged to.
                                 format_string -- see http://docs.python.org/library/logging.html for more information
                                 append -- whether or not to append to existing log files
                                 level -- the minimum level of messages to write to the log

                                 """
                                 import logging
                                 import logging.handlers

                                 if append:
                                     file_handler = logging.FileHandler(filename=filename)
                                 else:
                                     file_handler = logging.FileHandler(filename=filename, mode='w')
                                 file_handler.setLevel(level)
                                 if format_string is None:
                                     format_string = FILE_FORMAT_STRING
                                 file_formatter = logging.Formatter(format_string)
                                 file_handler.setFormatter(file_formatter)
                                 for handler in logger.handlers:
                                     try:
                                         if handler.baseFilename == file_handler.baseFilename:
                                             logger.debug('(not an error) logger already has a handler for this filename: ' + str(filename))
                                             return
                                     except AttributeError:
                                         pass
                                 logger.addHandler(file_handler)
                                 logger.debug('added logfile: ' + str(filename))

                             def get_logfiles(logger):
                                 logfiles = []
                                 for handler in logger.handlers:
                                     logfiles.append(handler.baseFilename)
                                 return logfiles

                             def set_rotating_logfile(logger, filename, format_string=None, max_bytes=(5*1024*1024), backup_count=5, append=True, level=DEBUG):
                                 """Create a new file handler for a logger.

                                 Keyword arguments:
                                 logger -- the logger to be given a file handler.
                                 filename -- the file to be logged to.
                                 format_string -- see http://docs.python.org/library/logging.html for more information
                                 max_bytes -- the maximum file size of a log file
                                 backup_count -- the number of log files to keep
                                 append -- whether or not to append to existing log files
                                 level -- the minimum level of messages to write to the log

                                 """
                                 import logging
                                 import logging.handlers

                                 if append:
                                     file_handler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count)
                                 else:
                                     file_handler = logging.handlers.RotatingFileHandler(filename=filename, mode='w', maxBytes=max_bytes, backupCount=backup_count)
                                 file_handler.setLevel(level)
                                 if format_string is None:
                                     format_string = FILE_FORMAT_STRING
                                 file_formatter = logging.Formatter(format_string)
                                 file_handler.setFormatter(file_formatter)
                                 for handler in logger.handlers:
                                     try:
                                         if handler.baseFilename == file_handler.baseFilename:
                                             logger.debug('(not an error) logger already has a handler for this filename: ' + str(filename))
                                             return
                                     except AttributeError:
                                         pass
                                 logger.addHandler(file_handler)
                                 logger.debug('added rotating logfile: ' + str(filename))

                             def close_logfile(logger, handler):
                                 logger.removeHandler(handler)

                             def set_console(logger, format_string=None, level=DEBUG):
                                 """Create a new console stream for a logger.

                                 Keyword arguments:
                                 logger - the logger to be given a stream handler.
                                 format_string -- see http://docs.python.org/library/logging.html for more information
                                 level -- the minimum level of messages to write to the log

                                 """
                                 import logging
                                 console_handler = logging.StreamHandler()
                                 console_handler.setLevel(level)
                                 if format_string is None:
                                     format_string = CONSOLE_FORMAT_STRING
                                 console_formatter = logging.Formatter(format_string)
                                 console_handler.setFormatter(console_formatter)
                                 for handler in logger.handlers:
                                     if handler.formatter == console_handler.formatter or handler.formatter._fmt == console_handler.formatter._fmt:
                                         logger.debug('(not an error) logger already has a console handler')
                                         return
                                 logger.addHandler(console_handler)


                             if __name__ == "__main__":
                                 print main()