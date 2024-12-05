import json
from enum import Enum

class Message(Enum):
    PING = "ping"
    PONG = "pong"
    GET_NODES = "WhoIsOnline"
    ELECT_S = "StartElection"
    ELECT_E_W = "IAmTheWinner"
    ELECT_E_L = "IAmTheLoser"

def create_msg(myid, clusterid, msg, weight = None):
    if msg not in Message.__members__:
        raise ValueError(f"Invalid message type: {msg}")

    return {
        "msg" : msg,
        "from" : myid,
        "for" : clusterid,
        "weight" : weight # For election
    }

def serialize_msg(msgpack):
    return json.dumps(msgpack)

def deserialize_msg(msgstr):
    try:
        return json.loads(msgstr)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")