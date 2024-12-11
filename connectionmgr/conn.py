import threading
import time
import logging
from .msghelper import *
import socket

logger = logging.getLogger(__name__)

class role:
    MASTER = 0
    SLAVE = 1
    UNDEF = 2

class sleepinterval:
    SLAVE = 5
    MASTER = 0
    ELECTION = 10

class threadbased(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.maxnodes = 5
    
    def stop(self):
        self.running = False

    def set_max_nodes(self, maxnodes):
        self.maxnodes = maxnodes

    def awarable_sleep(self, sleep_time, wakeup_interval = 0.2, exit_condition = None, exit_params = None):
        cnt = 0
        if wakeup_interval <= 0.1:
            logger.error("Wake up interval is not correct, fall back to 0.2")
            wakeup_interval = 0.2
        waittime_new = (sleep_time*int(1/wakeup_interval))
        while self.running and cnt < waittime_new:
            time.sleep(wakeup_interval)
            if exit_condition is not None:
                result, data = exit_condition(exit_params)
                if result:
                    logger.info("Exit condition is fullfil")
                    return True, data
            cnt = cnt + 1
        return False, None

class connmgr(threadbased):
    def __init__(self, myid, clusterid):
        super().__init__()
        self.myid = myid
        self.clusterid = clusterid
        self.myrole = "SLAVE"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setblocking(False)
        self._init_socket()
        self.rxthr = activereceiver(self.socket)

    def send_broadcast(self, msg):
        to_address = ('255.255.255.255', self.clusterid)
        self.socket.sendto(serialize_msg(msg), to_address)
        
    def wait_non_blocking(self, msgtype : Message):
        try:
            message, addr = self.socket.recvfrom(1024)
            data = deserialize_msg(message)
            if data["msg"] == msgtype:
                return True, data
            return False, None
        except BlockingIOError:
            return False, None

    def create_msg_wrapper(self, msg : Message, weight = None):
        return create_msg(self.myid, self.clusterid, msg, weight )

    def wait_pong(self, timeout = 5):
        return self.awarable_sleep(timeout, 0.2, self.wait_non_blocking, Message.PONG)
    
    def wait_ping(self, timeout = 5):
        return self.awarable_sleep(timeout, 0.2, self.wait_non_blocking, Message.PING)

    def wait_elects_message(self):
        return self.awarable_sleep(2, 0.2, self.wait_non_blocking, Message.ELECT_S)

    def _init_socket(self):
        self.socket.bind(("0.0.0.0", self.clusterid))

    def run(self):
        self.rxthr.start()
        while self.running:
            self.awarable_sleep(5)
        self.rxthr.stop()
        self.rxthr.join()

class activereceiver(threadbased):
    def __init__(self, rxsocket, cbhandles = {}):
        super().__init__()
        self.socket = rxsocket
        self.cbhandles = cbhandles
        self.synclock = threading.Lock()

    def register_handler(self, msg : Message, hdl):
        self.synclock.acquire()
        self.cbhandles[msg.value] = hdl
        self.synclock.release()

    def deregister_handler(self, msg: Message):
        self.synclock.acquire()
        if msg.value in self.cbhandles:
            del self.cbhandles[msg.value]
        self.synclock.release()

    def run(self):
        while self.running:
            try:
                message, addr = self.socket.recvfrom(1024)
            except BlockingIOError:
                continue
            try:
                data = deserialize_msg(message)
                self.synclock.acquire()
                if "msg" in data and data["msg"] in self.cbhandles:
                    self.cbhandles[data["msg"]](data)
                self.synclock.release()
            except BlockingIOError:
                pass
            except Exception as e:
                logger.error(str(e))
            time.sleep(0.2)
    


class pingmgr(threadbased):
    def __init__(self, conn : connmgr, master_dead_cb = None, myrole = role.SLAVE):
        super().__init__()
        self.myrole = myrole
        self.conn = conn
        self.slaveinterval = 60
        self.masterinterval = 1
        self.masterdeadcb = master_dead_cb
        self.msg = create_msg(conn.myid, conn.clusterid, Message.PING)

    def update_role(self, newrole):
        self.myrole = newrole

    def sleep_by_role(self):
        cnt = 0
        while self.running:
            if self.myrole is role.SLAVE:
                time.sleep(1)
                cnt = cnt + 1
            elif self.myrole is role.MASTER:
                cnt = 0
                time.sleep(1)
            elif self.myrole is role.UNDEF:
                # System is still finding the master, ping manager should sleep and wait
                time.sleep(1)
            else:
                logger.critical("The role is not existed")
                return

            if cnt > self.slaveinterval:
                cnt = 0
                break

    def run(self):
        while self.running:
            if self.myrole is role.MASTER:
                ret, data = self.conn.wait_ping()
                if ret:
                    logger.info("Receive ping request from slaves")
                    msg = create_msg(self.conn.myid, self.conn.clusterid, Message.PONG)
                    logger.info("Send pong")
                    self.conn.send_broadcast(msg)
                # self.sleep_by_role()
            elif self.myrole is role.SLAVE:
                msg = create_msg(self.conn.myid, self.conn.clusterid, Message.PING)
                self.conn.send_broadcast(msg)
                ret, data = self.conn.wait_pong()
                if not ret:
                    logger.error("Failed to received from master")
                    logger.info("Callback to notify the master is dead")
                    # Master is dead, what should we do
                    self.masterdeadcb()
                    self.myrole = role.UNDEF
                    logger.info("Waiting for role update from manager")
                    self.sleep_by_role()
                else:
                    self.sleep_by_role()