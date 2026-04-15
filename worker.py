from rq import Worker, Queue
from redis import Redis
from utils import logger

listen = ['default']

redis_conn = Redis()

if __name__ == "__main__":
    logger.info("Starting worker...")
    worker = Worker([Queue(name, connection=redis_conn) for name in listen])
    worker.work()