import appinfo
import logging
#import logging.config
from . import log_manager


#log settings
LOG_LEVEL = 'DEBUG'  # log level
log_in_file = True   # If True then log will be written in log file otherwise they will only show on console.
app_only_log = False # If True then only application logs will be written and other third party packages will be ignored.
separate_log_files = True # If True then logs from this application and from third party packages will be written in
                          # separate log files otherwise all logs will be written in same file.


# def _setup_logging():

    # Some testing code.
    # LOGGING_CONFIG = {
    #         "version": 1,
    #         "disable_existing_loggers": False,
    #
    #         "formatters": {
    #             "standard": {
    #                 "format": "%(asctime)s\t%(name)s\t%(levelname)s\t%(module)s\t%(message)s"
    #             },
    #             "detailed": {
    #                 "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    #             },
    #         },
    #
    #         "handlers": {
    #             "console": {
    #                 "class": "logging.StreamHandler",
    #                 "level": LOG_LEVEL,
    #                 "formatter": "standard",
    #                 "stream": "ext://sys.stdout",
    #             },
    #             "app_log_handler": {
    #                 "class": "logging.FileHandler",
    #                 "level": LOG_LEVEL,
    #                 "formatter": "detailed",
    #                 "filename": appinfo.APP_BASE_DIR +"/logs/dishtalk.log",
    #                 "mode": "a",
    #                 "encoding": "utf-8",
    #             },
    #             "other_log_handler": {
    #                 "class": "logging.FileHandler",
    #                 "level": LOG_LEVEL,
    #                 "formatter": "detailed",
    #                 "filename": appinfo.APP_BASE_DIR +"/logs/other.log",
    #                 "mode": "a",
    #                 "encoding": "utf-8",
    #             },
    #             "nullhandler": {
    #                 "class": "logging.NullHandler"
    #             }
    #         },
    #
    #         "loggers": {
    #             "root": {  # root logger
    #                 "level": LOG_LEVEL,
    #                 "handlers": ["console"],
    #             },
    #             "applogger": {  # custom logger
    #                 "level": LOG_LEVEL,
    #                 "handlers": ["console"],
    #                 "propagate": False,
    #             }
    #         },
    #     }

    # loggers = LOGGING_CONFIG["loggers"]
    # if log_in_file:
    #     loggers["applogger"]["handlers"] = ["console", "app_log_handler"]
    #     if app_only_log:
    #         loggers["root"]["handlers"] = ["nullhandler"] # add null handler
    #     else:
    #         if separate_log_files:
    #             loggers["root"]["handlers"] = ["console", "other_log_handler"]
    #         else:
    #             loggers["root"]["handlers"] = ["console", "app_log_handler"]
    #             del loggers["applogger"]
    # else:
    #     if app_only_log:
    #         loggers["root"]["handlers"] = ["nullhandler"] # add null handler
    #         loggers["applogger"]["handlers"] = ["console"]
    #     else:
    #         loggers["root"]["handlers"] = ["console"]  # add null handler
    #         loggers["applogger"]["handlers"] = ["console"]

    # logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(module_name):
    app_name = appinfo.APP_NAME
    logger = logging.getLogger(app_name + "." + module_name)
    return logger

def setup_logging():
    app_name = appinfo.APP_NAME
    log_mngr = log_manager.LoggingManager(app_name, LOG_LEVEL, log_in_file, app_only_log, separate_log_files)
    log_mngr.configure()



