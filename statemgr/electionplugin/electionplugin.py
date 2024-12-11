import random

def weight_based_election(myid, data):
    max_weight = 0
    win_id = myid
    for d in data:
        if "from" in d and "weight" in d:
            if int(d["weight"]) > max_weight:
                max_weight = int(d["weight"])
                win_id = int(d["from"])
    if win_id == myid:
        return True
    return False

def random_election(myid, data):
    windidx = random.randint(0, len(data)-1)
    if data[windidx]["from"] == myid:
        return True
    return False

def amithewinner(myid, data, selectionmethod):
    return selectionmethod(myid, data)