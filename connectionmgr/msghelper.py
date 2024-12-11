import json
from enum import Enum

class Message(Enum):
    PING = "PING"
    PONG = "PONG"
    GET_NODES = "GET_NODES"
    ELECT_S = "ELECT_S"
    ELECT_E_W = "ELECT_E_W"
    ELECT_E_L = "ELECT_E_L"

def create_msg(myid, clusterid, msg, weight = None):
    # print(Message.__members__.values())
    if msg.value not in Message.__members__.keys():
        raise ValueError(f"Invalid message type: {msg}")

    return {
        "msg" : msg.value,
        "from" : myid,
        "for" : clusterid,
        "weight" : weight # For election
    }

def serialize_msg(msgpack):
    return json.dumps(msgpack).encode()

def deserialize_msg(msgstr):
    try:
        return json.loads(msgstr.decode())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")