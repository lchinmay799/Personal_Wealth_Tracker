import logging
import os
from logging.handlers import TimedRotatingFileHandler

class logger:
    def __init__(self):
        logFile=os.path.join(os.getenv("PYTHONPATH"),"logs","personal_wealth_tracker","personalWealthTracker.log")
        logHandler=TimedRotatingFileHandler(filename=logFile,
                                            backupCount=30,
                                            when='midnight',
                                            interval=1)
        formatter=logging.Formatter(fmt="%(asctime)s - %(levelname)s : [%(pathname)s:%(lineno)s] : %(message)s")
        logHandler.setFormatter(formatter)
        logHandler.setLevel(logging.INFO)

        self.logger=logging.getLogger(name="PersonalWealthTracker")
        self.logger.handlers.clear()
        self.logger.addHandler(logHandler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate=False

    def getLogger(self):
        return self.logger