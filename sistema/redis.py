import json, redis

def redis_connect():
    dir = '127.0.0.1'
    port = 6379
    db = 0
    pool = redis.Redis(host=dir, port=port, db=db)
    return pool


def persistVar(variable_name):
    try:
        my_server = redis_connect()
        my_server.persist(variable_name)
        resp = True
    except:
        resp = False
    return resp


def getVar(variable_name):
    my_server = redis_connect()
    response = my_server.get(variable_name)
    if response == None:
        resp = False
    else:
        resp = json.loads(response)
    return resp


def setVar(variable_name, variable_value,ex):
    try:
        my_server = redis_connect()
        if ex == 0:
            my_server.set(variable_name, json.dumps(variable_value))
        else:
            my_server.set(variable_name, json.dumps(variable_value), ex=ex)
        resp = True
    except:
        resp = False
    return resp