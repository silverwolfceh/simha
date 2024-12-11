from .electionplugin.electionplugin import *
from .masterplugin.masterplugin import *
from .slaveplugin.slaveplugin import *
import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.__file__)))
from connectionmgr.conn import connmgr, pingmgr
from connectionmgr.msghelper import Message

logger = logging.getLogger(__name__)

class role:
    MASTER = 0
    SLAVE = 1
    UNDEF = 2
class rolemanager:
    def __init__(self, mrole = role.SLAVE):
        self.slaveprocess = slave_process()
        self.masterprocess = master_process()
        self.currole = role.SLAVE
        self.runningprocess = self.slaveprocess if mrole is role.SLAVE else self.masterprocess
    
    def start(self):
        self.runningprocess.start()

    def stop(self):
        self.runningprocess.stop()

    def switch(self):
        self.stop()
        self.currole = role.SLAVE if self.currole is role.MASTER else role.MASTER
        self.runningprocess = self.slaveprocess if self.currole is role.SLAVE else self.masterprocess
        self.start()

# The GOD class
class statemgrprog(threading.Thread):
    def __init__(self, clusterid, myid, myweight, maxnodes):
        threading.Thread.__init__(self)
        self.myid = myid
        self.conmgr = connmgr(myid, clusterid)
        self.pingmgr = pingmgr(self.conmgr, self.master_is_dead)
        self.mweight = int(myweight)
        self.rolemgr = rolemanager()
        self.role = role.SLAVE
        self.running = True
        self.isroleupdate = False
        self.maxnodes = int(maxnodes)
        logger.info("Start manager initialize done")

    def master_is_dead(self):
        logger.info("Sending my weight for other nodes")
        msg = self.conmgr.create_msg_wrapper(Message.ELECT_S, self.mweight)
        self.conmgr.send_broadcast(msg)
        logger.info("Received weight from other nodes")
        electsdata = self.conmgr.wait_and_collect_elects_message()
        print(f"All election data: {electsdata}")
        ret = amithewinner(self.myid, electsdata, random_election)
        if not ret:
            msg = self.conmgr.create_msg_wrapper(Message.ELECT_E_L, self.mweight)
            self.conmgr.send_broadcast(msg)
            self.role = role.SLAVE
            self.pingmgr.change_to_slave()
        else:
            msg = self.conmgr.create_msg_wrapper(Message.ELECT_E_W, self.mweight)
            self.conmgr.send_broadcast(msg)
            self.role = role.MASTER
            self.isroleupdate = True
            self.pingmgr.change_to_master()

    def stop(self):
        self.running = False
    
    def run(self):
        # Initialization
        logger.info("Start connection manager")
        self.conmgr.start()
        time.sleep(1)
        logger.info("Start ping manager")
        self.pingmgr.start()
        time.sleep(1)
        # Start salve process
        logger.info("Start the current role process")
        self.rolemgr.start()
        # Wait for event update
        logger.info("Wait for event on role-change")
        while self.running:
            if self.isroleupdate:
                logger.info("Role changed, switching...")
                self.rolemgr.switch()
                self.isroleupdate = False
        logger.info("Stopping the node on demand")
        # HA is end
        self.conmgr.stop()
        self.pingmgr.stop()
        self.rolemgr.stop()

