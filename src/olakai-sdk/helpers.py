from typing import Any, Dict, Optional, Union
from .types import MonitorOptions
from .utils import MonitorUtils
from .monitor import monitor
import logging


def olakai_monitor(options: Optional[Union[Dict[str, Any], MonitorOptions]] = None, logger: Optional[logging.Logger] = None):
    if options is None:
        options = MonitorUtils.capture_all
    elif isinstance(options, MonitorOptions):
        pass
    else:
        # If it's a dictionary, create MonitorOptions from it
        if "capture" not in options:
            options["capture"] = MonitorUtils.capture_all_f
        options = MonitorOptions(**options)

    return monitor(options, logger)
