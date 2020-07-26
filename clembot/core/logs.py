import logging
import logging.handlers
import sys

_instance = None


def init_loggers():
    global _instance

    if _instance:
        return _instance

    dpy_logfile_path = 'logs/discord.log'
    dpy_fhandler = logging.handlers.RotatingFileHandler(
        filename=str(dpy_logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=5)

    dpy_logger = logging.getLogger('discord')
    dpy_logger.setLevel(logging.INFO)
    dpy_logger.addHandler(dpy_fhandler)


    _instance = dpy_logger



    console = logging.StreamHandler()
    console.setLevel(logging.INFO)


    logger = logging.getLogger("clembot")
    logger.setLevel(logging.INFO)
    _instance = logger
    clembot_format = logging.Formatter(
        '%(asctime)s %(levelname)s [%(module)s %(funcName)s():%(lineno)d] : '
        '%(message)s',
        datefmt="[%m/%d/%Y %H:%M:%S]")


    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(clembot_format)


    logfile_path = 'logs/clembot.log'
    fhandler = logging.handlers.RotatingFileHandler(
        filename=str(logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=10)
    fhandler.setFormatter(clembot_format)


    #_instance.addHandler(fhandler)
    _instance.addHandler(stdout_handler)
    logger.info("logger initialized.")
    return logger


Logger = init_loggers()