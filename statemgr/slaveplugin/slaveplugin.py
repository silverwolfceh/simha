import threading
import logging
import time

logger = logging.getLogger(__name__)
class slave_process(threading.Thread):
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
            logger.debug("Slave is running...")
            time.sleep(1)
        logger.debug("Slave is stopped")