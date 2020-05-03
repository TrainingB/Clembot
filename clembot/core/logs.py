import logging
import logging.handlers
import sys

global_logger = None


def init_loggers():


    global global_logger

    if global_logger:
        return global_logger

    print("init_loggers()")


    dpy_logfile_path = 'logs/discord.log'
    dpy_fhandler = logging.handlers.RotatingFileHandler(
        filename=str(dpy_logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=5)

    dpy_logger = logging.getLogger('discord')
    dpy_logger.setLevel(logging.INFO)
    dpy_logger.addHandler(dpy_fhandler)


    global_logger = dpy_logger



    console = logging.StreamHandler()
    console.setLevel(logging.INFO)


    logger = logging.getLogger("clembot")
    logger.setLevel(logging.INFO)

    clembot_format = logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s() %(lineno)d: '
        '%(message)s',
        datefmt="[%m/%d/%Y %H:%M]")


    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(clembot_format)


    logfile_path = 'logs/clembot.log'
    fhandler = logging.handlers.RotatingFileHandler(
        filename=str(logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=20)
    fhandler.setFormatter(clembot_format)

    global_logger.addHandler(fhandler)
    # global_logger.addHandler(stdout_handler)

    return logger
