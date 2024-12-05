import threading
import time
import logging
from msghelper import *
import socket

logger = logging.getLogger(__name__)

class role:
    SLAVE = "Passive"
    MASTER = "Active"
    UNDEF = "Undefined"

class sleepinterval:
    SLAVE = 5
    MASTER = 0

class threadbased(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
    
    def stop(self):
        self.running = False

    def awarable_sleep(self, sleep_time, wakeup_interval = 0.2, exit_condition = None, exit_params = None):
        cnt = 0
        if wakeup_interval <= 0.1:
            logger.error("Wake up interval is not correct, fall back to 0.2")
            wakeup_interval = 0.2
        waittime_new = (sleep_time*int(1/wakeup_interval))
        while self.running and cnt < waittime_new:
            time.sleep(wakeup_interval)
            if exit_condition:
                result, data = exit_condition(exit_params)
                if result:
                    logger.info("Exit condition is fullfil")
                    return True, data
            cnt = cnt + 1
        return False, None

class connmgr(threadbased):
    def __init__(self, myid, clusterid):
        self.myid = myid
        self.clusterid = clusterid
        self.myrole = "SLAVE"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(False)

    def send_broadcast(self, msg):
        to_address = ('255.255.255.255', self.clusterid)
        self.socket.sendto(serialize_msg(msg), to_address)
        
    def wait_non_blocking(self, msgtype : Message):
        try:
            message, addr = self.socket.recvfrom(1024)
            data = deserialize_msg(message)
            if data["msg"] == msgtype:
                return True, data
        except BlockingIOError:
            return False, None

    def create_msg_wrapper(self, msg : Message, weight = None):
        return create_msg(self.myid, self.clusterid, msg, weight )

    def wait_pong(self, timeout = 5):
        return self.awarable_sleep(timeout, 0.2, self.wait_non_blocking, Message.PONG)
    
    def wait_ping(self, timeout = 5):
        return self.awarable_sleep(timeout, 0.2, self.wait_non_blocking, Message.PING)
    
    def _init_socket(self):
        self.socket.bind(("0.0.0.0", self.clusterid))

    def run(self):
        try:
            self._init_socket()
        except Exception as e:
            logger.critical("Failed to initlized the connection")
            return False
        while self.running:
            self.awarable_sleep(5)
        return True

class pingmgr(threadbased):
    def __init__(self, conn : connmgr, myrole = role.SLAVE, master_dead_cb = None):
        threadbased.__init__(self)
        self.myrole = myrole
        self.conn = conn
        self.slaveinterval = 60
        self.masterinterval = 1
        self.masterdeadcb = master_dead_cb
        self.msg = create_msg(conn.myid, conn.clusterid)

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
                self.conn.wait_ping()
                msg = create_msg(self.conn.myid, self.conn.clusterid, Message.PONG)
                self.conn.send_broadcast(msg)
                self.sleep_by_role()
            elif self.myrole is role.SLAVE:
                msg = create_msg(self.conn.myid, self.conn.clusterid, Message.PING)
                self.conn.send_broadcast(msg)
                ret, data = self.conn.wait_pong()
                if not ret:
                    # Master is dead, what should we do
                    self.masterdeadcb()
                    self.myrole = role.UNDEF
                    self.sleep_by_role()
                else:
                    self.sleep_by_role()