from logcfg import setup_logger
from statemgr import statemanager
from dotenv import load_dotenv
import time
import os

DEFAULT_CLUSTER_ID = 9999
DEFAULT_WEIGHT = 0
DEFAULT_ID = f"{DEFAULT_CLUSTER_ID}_{int(time.time)}"

if __name__ == "__main__":
    load_dotenv(override=True)
    setup_logger()
    clusterid = os.getenv("CLUSTER_ID", DEFAULT_CLUSTER_ID)
    myid = os.getenv("MY_ID", DEFAULT_ID)
    myweight = os.getenv("MY_WEIGHT", DEFAULT_WEIGHT)
    prog = statemanager.statemanagerprog(clusterid, myid, myweight)
    prog.start()