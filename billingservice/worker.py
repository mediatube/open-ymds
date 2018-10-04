import sys

from redis import Redis
from rq import Connection, Worker

import imp

with open('.secret/rq_access.py', 'rb') as fp:
    rq_access = imp.load_module('rq_access', fp, '.secret/rq_access.py', ('.py', 'rb', imp.PY_SOURCE))
redis_conn = Redis(host=rq_access.host, port=rq_access.port, password=rq_access.password)

with Connection(redis_conn):
    qs = sys.argv[1:] or ['default']
    w = Worker(qs)
    w.work()
