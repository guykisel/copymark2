"""Wrapper for python's logging class to make logging easier
and more standardized.

"""

import sys
import platform
import logging

file_format_string = '%(created).3f\t %(asctime)s\t %(threadName)s\t %(module)s\t %(name)s\t %(funcName)s\t %(lineno)d\t %(levelname)s\t %(message)s\t'
console_format_string = '%(message)s\t %(threadName)s\t %(module)s\t %(funcName)s\t %(lineno)d\t %(created).3f\t %(asctime)s\t %(name)s\t %(levelname)s\t'
datefmt_string = '%a %d %b %Y %H:%M:%S'

def main():
    """Parse input strings and run the appropriate function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'sys_info':
            return sys_info()
        elif sys.argv[1] == 'log_format':
            return file_format_string
        elif sys.argv[1] == 'console_format':
            return console_format_string
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

def set_logfile(logger, filename, format_string=None, max_bytes=(5*1024*1024), append=True):
    """Create a new file handler for a logger.

    Keyword arguments:
    logger -- the logger to be given a file handler.
    filename -- the file to be logged to.

    """
    import logging
    import logging.handlers

    if append:
        file_handler = logging.FileHandler(filename=filename)
    else:
        file_handler = logging.FileHandler(filename=filename, mode='w')
    file_handler.setLevel(logging.DEBUG)
    if format_string == None:
        format_string = file_format_string
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

def set_console(logger, format_string=None):
    """Create a new console stream for a logger.

    Keyword arguments:
    logger - the logger to be given a stream handler.

    """
    import logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    if format_string == None:
        format_string = console_format_string
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    for handler in logger.handlers:
        if handler.formatter == console_handler.formatter or handler.formatter._fmt == console_handler.formatter._fmt:
            logger.debug('(not an error) logger already has a console handler')
            return
    logger.addHandler(console_handler)


if __name__ == "__main__":
    print main()