import logging
import json
import sys
import appinfo


# ============================================================
# Logging Manager
# ============================================================

class LoggingManager:
    """
    A class to configure logging for the application.
    """
    def __init__(
        self,
        app_name: str,
        log_level: str = "INFO",
        log_in_file: bool = True,
        app_only_log: bool = True,
        separate_log_files: bool = False,
        json_logs: bool = False,
    ):
        """
        :param app_name:  Application name. use to filter logs from this application.
        :param log_level: log level.
        :param log_in_file: If True then log will be written in log file otherwise they will only show on console.
        :param app_only_log: If True then only application logs will be written and other third party packages will be ignored.
        :param separate_log_files: If True then logs from this application and from third party packages will be written in
        separate log files otherwise all logs will be written in same file.
        :param json_logs: If True then json format will be used for logging else standard ext format will be used
        """
        self.app_name = app_name
        self.level = log_level.upper()
        self.log_in_file = log_in_file
        self.app_only_log = app_only_log
        self.separate_log_files = separate_log_files
        self.json_logs = json_logs
        self.log_dir = appinfo.APP_BASE_DIR +"/logs/"

    # ============================================================
    # JSON Formatter
    # ============================================================

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno,
            }

            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_record)

    # ============================================================
    # Filters
    # ============================================================

    class AppOnlyFilter(logging.Filter):
        def __init__(self, app_name: str):
            super().__init__()
            self.app_name = app_name
            self.__module_prefix = self.app_name + "."

        def filter(self, record: logging.LogRecord) -> bool:
            return record.name.startswith(self.__module_prefix)

    class ThirdPartyFilter(logging.Filter):
        def __init__(self, app_name: str):
            super().__init__()
            self.app_name = app_name
            self.__module_prefix = self.app_name + "."

        def filter(self, record: logging.LogRecord) -> bool:
            return not record.name.startswith(self.__module_prefix)

    def __get_standard_format(self):
        return "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    def __rotating_file_handler(self, filename, formatter_name, filter_obj=None):
        # handler = logging.handlers.RotatingFileHandler(
        #     self.log_dir / filename,
        #     maxBytes=10 * 1024 * 1024,  # 10MB
        #     backupCount=5,
        # )

        # handler = logging.FileHandler(self.log_dir + filename, mode='a', encoding='utf-8')
        #
        # handler.setLevel(self.level)
        # handler.setFormatter(self._get_formatter(formatter_name))
        # if filter_obj:
        #     handler.addFilter(filter_obj)
        # return handler

        return {
            "class": "logging.FileHandler",
            "level": self.level,
            "formatter": formatter_name,
            "filename": self.log_dir + filename,
            "mode": "a",
            "encoding": "utf-8",
        }

    def _get_formatter(self, name):
        return self.JsonFormatter() if name == "json" else logging.Formatter(self.__get_standard_format(), datefmt="%Y-%m-%d %H:%M",)

    def configure(self):

        formatter_name = "json" if self.json_logs else "standard"
        app_log_file_path = self.log_dir + "app.log"
        other_log_file_path = self.log_dir + "other.log"

        formatters = {
            "standard": {"format": self.__get_standard_format(), "datefmt": "%Y-%m-%d %H:%M",},
            "json": {"()": LoggingManager.JsonFormatter},
        }

        filters = {
            "app_only": {"()": LoggingManager.AppOnlyFilter, "app_name": self.app_name},
            "third_party": {"()": LoggingManager.ThirdPartyFilter, "app_name": self.app_name},
        }

        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "level": self.level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "app_log_handler": {
                "class": "logging.FileHandler",
                "level": self.level,
                "formatter": formatter_name,
                "filename": app_log_file_path,
                "mode": "a",
                "encoding": "utf-8",
            },
            "other_log_handler": {
                "class": "logging.FileHandler",
                "level": self.level,
                "formatter": formatter_name,
                "filename": other_log_file_path,
                "mode": "a",
                "encoding": "utf-8",
            }
        }


        root_handlers = []

        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(self.level)
        console.setFormatter(self._get_formatter(formatter_name))

        if self.app_only_log:
            console.addFilter(self.AppOnlyFilter(self.app_name))
        root_handlers.append("console")

        if self.log_in_file:

            if self.app_only_log:
                handlers["app_log_handler"]["filters"] = ["app_only"]
                root_handlers.append("app_log_handler")
            elif self.separate_log_files:

                handlers["app_log_handler"]["filters"] = ["app_only"]
                handlers["other_log_handler"]["filters"] = ["third_party"]
                root_handlers.extend(["app_log_handler", "other_log_handler"])
            else:
                root_handlers.append("app_log_handler")
        else:
            if self.app_only_log:
                handlers["console"]["filters"] = ["app_only"]


        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "filters": filters,
            "handlers": handlers,
            "root": {
                "level": self.level,
                "handlers": root_handlers,
            },
        }

        logging.config.dictConfig(logging_config)
