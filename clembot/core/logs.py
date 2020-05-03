import logging
import logging.handlers
import sys

global_logger = None


def init_loggers():

    # d.py stuff
    global global_logger

    if global_logger:
        return global_logger

    print("init_loggers()")
    dpy_logger = logging.getLogger("discord")
    dpy_logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    dpy_logger.addHandler(console)
    global_logger = dpy_logger
    # Meowth

    logger = logging.getLogger("clembot")

    clembot_format = logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s() %(lineno)d: '
        '%(message)s',
        datefmt="[%m/%d/%Y %H:%M]")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(clembot_format)
    logger.setLevel(logging.INFO)

    logfile_path = 'logs/clembot.log'
    fhandler = logging.handlers.RotatingFileHandler(
        filename=str(logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=20)
    fhandler.setFormatter(clembot_format)

    global_logger.addHandler(fhandler)
    # global_logger.addHandler(stdout_handler)

    return logger
