import logging
import os
from logging.handlers import TimedRotatingFileHandler

class logger:
    def __init__(self):
        logFile=os.path.join(os.getenv("PYTHONPATH"),"logs","personalWealthTracker.log")
        logHandler=TimedRotatingFileHandler(filename=logFile,
                                            backupCount=30,
                                            when='midnight',
                                            interval=1)
        formatter=logging.Formatter(fmt="%(asctime)s - %(levelname)s : [%(pathname)s:%(lineno)s] : %(message)s")
        logHandler.setFormatter(formatter)
        logHandler.setLevel(logging.INFO)

        logger=logging.getLogger(name="PersonalWealthTracker")
        logger.handlers.clear()
        logger.addHandler(logHandler)
        logger.setLevel(logging.INFO)
        logger.propagate=False