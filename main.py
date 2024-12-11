from logcfg import setup_logger
from statemgr import statemanager
from dotenv import load_dotenv
from util import gen_my_id
import logging
import sys
import signal
import os

DEFAULT_CLUSTER_ID = 9999
DEFAULT_WEIGHT = 0
DEFAULT_ID = 0
DEFAULT_MAX_NODE = 5

if __name__ == "__main__":
	if len(sys.argv) > 1:
		print(sys.argv[1])
		load_dotenv(sys.argv[1], override=True)
	else:
		load_dotenv(".env", override=True)
	setup_logger()
	logger = logging.getLogger(__name__)
	clusterid = int(os.getenv("CLUSTER_ID", DEFAULT_CLUSTER_ID))
	myid = gen_my_id()
	myweight = os.getenv("MY_WEIGHT", DEFAULT_WEIGHT)
	maxnodes = os.getenv("MAX_NODE", DEFAULT_MAX_NODE)
	logger.info(f"Start running a node {myid} inside the {clusterid} with weight {myweight}")
	prog = statemanager.statemgrprog(clusterid, myid, myweight, maxnodes)
	prog.start()
	try:
		logger.info("Running forever...")
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		#signal.pause()
	except KeyboardInterrupt:
		logger.info("Request to stop from user")
		prog.stop()
		prog.join()