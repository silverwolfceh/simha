import threading
import logging
import time
logger = logging.getLogger(__name__)

class master_process(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.processid = None

    def get_id(self):
        return self.processid
    
    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            logger.debug("Master is running...")
            time.sleep(5)
        logger.debug("Master is stopped")