from rq import Worker, Queue, Connection
from redis import Redis
from utils import logger

redis_conn = Redis()

if __name__ == "__main__":
    with Connection(redis_conn):
        logger.info("Worker started, waiting for tasks...")
        worker = Worker([Queue()])
        worker.work()