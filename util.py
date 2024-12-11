import socket
import random

def gen_my_id():
    myid = random.randint(8000, 8888)
    isvalid = test_connection(myid)
    while not isvalid:
        myid = random.randint(8000, 8888)
        isvalid = test_connection(myid)
    return myid

def test_connection(myid):
    msocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    msocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msocket.setblocking(False)
    try:
        msocket.bind(("0.0.0.0", myid))
        msocket.close()
        return True
    except Exception as e:
        return False