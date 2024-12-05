import threading
from electionplugin import *
from masterplugin import *
from slaveplugin import *
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.__file__)))
from connectionmgr import connmgr, pingmgr, Message

# The GOD class
class statemanagerprog:
    def __init__(self, clusterid, myid, myweight):
        self.conmgr = connmgr(myid, clusterid)
        self.pingmgr = pingmgr(self.conmgr, self.master_is_dead)
        self.mweight - myweight
        self.slaveprocess = slave_process
        
    def master_is_dead(self):
        msg = self.conmgr.create_msg_wrapper(Message.ELECT_S)
        self.conmgr.send_broadcast(msg)

        pass

    def start(self):
        if self.conmgr.start():
            self.pingmgr.start()
