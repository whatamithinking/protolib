from typing import *
import logging
import sys
from enum import Enum
from abc import ABC

__all__ = [
    "LogLevelType",
    "Logable",
]


class LogLevelType(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Logable(ABC):
    def __init__(self, log_name, **kwargs) -> None:
        self._logger = logging.getLogger(log_name)
        self._logger.addHandler(logging.NullHandler())
        super().__init__(**kwargs)

    def _log_extra(self) -> Dict[Any, Any]:
        """Return a dict of any additional metadata which would be useful
        in a log record or exception."""
        return dict()

    def _log(
        self, level: Union[int, str, LogLevelType], msg: Optional[str] = None, **kwargs
    ) -> None:
        extra = self._log_extra() | kwargs.pop("extra", {}) | kwargs
        exc_info = kwargs.get("exc_info", None)  # may sometimes pass this in
        # debug level where problem is somewhat expected but having the stacktrace
        # will aide with determining if there is a real issue or not
        if isinstance(level, LogLevelType):
            level = level.value
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        if level >= logging.ERROR:
            exc_info = sys.exc_info()
        self._logger.log(level=level, msg=msg, extra=extra, exc_info=exc_info)
